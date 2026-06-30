/**
 * inspection_commander_node.cpp
 *
 * ROS2 C++ node — Visual Inspection state machine.
 *
 * Exposes a /run_inspection action server. When triggered, the node drives the
 * robot arm through 5 fixed inspection poses (P1–P5), collects AI inference
 * votes from /inspection_result at each pose, performs majority-vote
 * classification, then sorts the object to PASS or FAIL tray.
 *
 * Topics subscribed:
 *   /inspection_result  (visual_inspection/msg/InspectionResult)
 *
 * Actions provided:
 *   /run_inspection     (visual_inspection/action/RunInspection)
 *
 * Motion:
 *   MoveGroupInterface on "denso_arm" planning group (joint-space waypoints).
 *   Gripper via GripperCommand action on /denso_hand_controller/gripper_cmd.
 *
 * Waypoints (joint values [X,Y,Z,A,B,C] rad) are loaded from ROS2 parameters
 * and intentionally left as zeros — calibrate on hardware and update
 * inspection_config.yaml.
 *
 * State machine:
 *   IDLE → MOVING_TO_P1 → COLLECTING_P1
 *        → MOVING_TO_P2 → COLLECTING_P2
 *        → MOVING_TO_P3 → COLLECTING_P3
 *        → MOVING_TO_P4 → COLLECTING_P4
 *        → MOVING_TO_P5 → COLLECTING_P5
 *        → CLASSIFYING
 *        → MOVING_TO_SORT (PASS or FAIL tray)
 *        → MOVING_HOME → IDLE
 */

#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <std_msgs/msg/string.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <control_msgs/action/gripper_command.hpp>

#include <atomic>
#include <chrono>
#include <deque>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

#include "visual_inspection/msg/inspection_result.hpp"
#include "visual_inspection/action/run_inspection.hpp"

using InspectionResult   = visual_inspection::msg::InspectionResult;
using RunInspection      = visual_inspection::action::RunInspection;
using GoalHandle         = rclcpp_action::ServerGoalHandle<RunInspection>;
using GripperCommand     = control_msgs::action::GripperCommand;
using MoveGroupInterface = moveit::planning_interface::MoveGroupInterface;

// ─────────────────────────────────────────────────────────────────────────────

class InspectionCommanderNode : public rclcpp::Node
{
public:
  InspectionCommanderNode()
  : Node("inspection_commander_node"),
    busy_(false)
  {
    // ── Parameters ────────────────────────────────────────────────────────────
    this->declare_parameter("confidence_threshold", 0.70);
    this->declare_parameter("frames_per_pose",      5);
    this->declare_parameter("settle_time_sec",      0.5);
    this->declare_parameter("enable_pick",          false);
    this->declare_parameter("gripper_open_pos",     1.47);
    this->declare_parameter("gripper_closed_pos",   0.10);

    // Waypoints: 6 joint values each [X,Y,Z,A,B,C] in radians
    // Default all-zero — update inspection_config.yaml after hardware calibration
    auto declare_wp = [this](const std::string & name) {
      this->declare_parameter(name, std::vector<double>{0.0, 0.0, 0.0, 0.0, 0.0, 0.0});
    };
    declare_wp("waypoints.home");
    declare_wp("waypoints.pick");
    declare_wp("waypoints.inspect_p1");
    declare_wp("waypoints.inspect_p2");
    declare_wp("waypoints.inspect_p3");
    declare_wp("waypoints.inspect_p4");
    declare_wp("waypoints.inspect_p5");
    declare_wp("waypoints.pre_place");
    declare_wp("waypoints.sort_pass");
    declare_wp("waypoints.sort_fail");

    confidence_threshold_ = this->get_parameter("confidence_threshold").as_double();
    frames_per_pose_      = this->get_parameter("frames_per_pose").as_int();
    settle_time_sec_      = this->get_parameter("settle_time_sec").as_double();
    enable_pick_          = this->get_parameter("enable_pick").as_bool();
    gripper_open_pos_     = this->get_parameter("gripper_open_pos").as_double();
    gripper_closed_pos_   = this->get_parameter("gripper_closed_pos").as_double();

    // ── Subscriber: AI results ────────────────────────────────────────────────
    result_sub_ = this->create_subscription<InspectionResult>(
      "/inspection_result", 10,
      std::bind(&InspectionCommanderNode::resultCallback, this, std::placeholders::_1));

    // ── Action server ─────────────────────────────────────────────────────────
    action_server_ = rclcpp_action::create_server<RunInspection>(
      this, "/run_inspection",
      std::bind(&InspectionCommanderNode::handleGoal,     this,
                std::placeholders::_1, std::placeholders::_2),
      std::bind(&InspectionCommanderNode::handleCancel,   this, std::placeholders::_1),
      std::bind(&InspectionCommanderNode::handleAccepted, this, std::placeholders::_1));

    // ── Gripper action client ─────────────────────────────────────────────────
    gripper_client_ = rclcpp_action::create_client<GripperCommand>(
      this, "/denso_hand_controller/gripper_cmd");

    RCLCPP_INFO(this->get_logger(),
                "InspectionCommanderNode created (MoveGroup not yet ready)");
  }

  /**
   * Call from main() after the executor has started spinning.
   */
  void setupMoveGroup(const std::shared_ptr<rclcpp::Node> & node)
  {
    move_group_ = std::make_shared<MoveGroupInterface>(node, "denso_arm");
    move_group_->setMaxVelocityScalingFactor(0.5);
    move_group_->setMaxAccelerationScalingFactor(0.5);
    RCLCPP_INFO(this->get_logger(),
                "MoveGroupInterface ready [planning_frame=%s]",
                move_group_->getPlanningFrame().c_str());
  }

private:
  // ── Parameters ──────────────────────────────────────────────────────────────
  double confidence_threshold_;
  int    frames_per_pose_;
  double settle_time_sec_;
  bool   enable_pick_;
  double gripper_open_pos_;
  double gripper_closed_pos_;

  // ── State ───────────────────────────────────────────────────────────────────
  std::atomic<bool>           busy_;
  std::mutex                  vote_mutex_;
  std::vector<InspectionResult> vote_buffer_;   // frames collected at current pose
  bool                        collecting_{false};

  // ── ROS interfaces ──────────────────────────────────────────────────────────
  rclcpp::Subscription<InspectionResult>::SharedPtr     result_sub_;
  rclcpp_action::Server<RunInspection>::SharedPtr       action_server_;
  rclcpp_action::Client<GripperCommand>::SharedPtr      gripper_client_;
  std::shared_ptr<MoveGroupInterface>                   move_group_;

  // ── Incoming AI result ───────────────────────────────────────────────────────
  void resultCallback(const InspectionResult & msg)
  {
    if (!collecting_) return;
    if (msg.confidence < static_cast<float>(confidence_threshold_)) return;

    std::lock_guard<std::mutex> lock(vote_mutex_);
    vote_buffer_.push_back(msg);
  }

  // ── Action server callbacks ──────────────────────────────────────────────────
  rclcpp_action::GoalResponse handleGoal(
    const rclcpp_action::GoalUUID &,
    std::shared_ptr<const RunInspection::Goal> goal)
  {
    if (busy_.load()) {
      RCLCPP_WARN(this->get_logger(),
                  "Inspection already running — rejecting goal for '%s'",
                  goal->object_id.c_str());
      return rclcpp_action::GoalResponse::REJECT;
    }
    RCLCPP_INFO(this->get_logger(),
                "Inspection goal accepted: object_id='%s'", goal->object_id.c_str());
    return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
  }

  rclcpp_action::CancelResponse handleCancel(
    const std::shared_ptr<GoalHandle>)
  {
    RCLCPP_INFO(this->get_logger(), "Cancel requested.");
    return rclcpp_action::CancelResponse::ACCEPT;
  }

  void handleAccepted(const std::shared_ptr<GoalHandle> goal_handle)
  {
    // Spawn execution thread to avoid blocking the executor
    std::thread([this, goal_handle]() { runSequence(goal_handle); }).detach();
  }

  // ── Main inspection sequence ─────────────────────────────────────────────────
  void runSequence(const std::shared_ptr<GoalHandle> goal_handle)
  {
    busy_ = true;

    auto feedback = std::make_shared<RunInspection::Feedback>();
    auto result   = std::make_shared<RunInspection::Result>();
    int total_pass = 0;
    int total_fail = 0;

    auto publish_feedback = [&](const std::string & state, float progress) {
      feedback->state      = state;
      feedback->progress   = progress;
      feedback->pass_votes = total_pass;
      feedback->fail_votes = total_fail;
      goal_handle->publish_feedback(feedback);
      RCLCPP_INFO(this->get_logger(), "[%s] progress=%.0f%%  pass=%d  fail=%d",
                  state.c_str(), progress * 100.0f, total_pass, total_fail);
    };

    // ── PICK (optional) ───────────────────────────────────────────────────────
    if (enable_pick_) {
      // Ensure gripper is open before approaching the object
      publish_feedback("OPENING_GRIPPER", 0.03f);
      sendGripper(gripper_open_pos_);

      publish_feedback("MOVING_TO_PICK", 0.05f);
      if (!moveToWaypoint("waypoints.pick")) {
        abortGoal(goal_handle, result, "Failed to reach PICK pose");
        busy_ = false; return;
      }
      // Let arm fully settle at pick pose before closing gripper
      std::this_thread::sleep_for(
        std::chrono::milliseconds(static_cast<int>(settle_time_sec_ * 1000)));
      publish_feedback("PICKING", 0.08f);
      sendGripper(gripper_closed_pos_);  // close gripper to grasp
    }

    // ── Inspection poses ──────────────────────────────────────────────────────
    const std::vector<std::pair<std::string, float>> poses = {
      {"inspect_p1", 0.15f},
      {"inspect_p2", 0.30f},
      {"inspect_p3", 0.45f},
      {"inspect_p4", 0.60f},
      {"inspect_p5", 0.75f},
    };

    for (const auto & [pose_name, progress] : poses) {
      if (goal_handle->is_canceling()) {
        cancelGoal(goal_handle, result);
        busy_ = false; return;
      }

      // Move to pose
      publish_feedback("MOVING_TO_" + upperCase(pose_name), progress - 0.05f);
      if (!moveToWaypoint("waypoints." + pose_name)) {
        abortGoal(goal_handle, result, "Failed to reach " + pose_name);
        busy_ = false; return;
      }

      // Settle: wait for arm vibration to damp out
      std::this_thread::sleep_for(
        std::chrono::milliseconds(static_cast<int>(settle_time_sec_ * 1000)));

      // Collect votes
      publish_feedback("COLLECTING_" + upperCase(pose_name), progress);
      auto [p, f] = collectVotes(frames_per_pose_);
      total_pass += p;
      total_fail += f;
    }

    // ── Classify ──────────────────────────────────────────────────────────────
    publish_feedback("CLASSIFYING", 0.85f);

    if (total_pass == 0 && total_fail == 0) {
      // No frame passed the confidence threshold — cannot classify.
      // Return the object to the pick position so the operator can retry.
      RCLCPP_WARN(this->get_logger(),
                  "No confident votes collected (threshold=%.2f). "
                  "Returning object to PICK pose for operator retry.",
                  confidence_threshold_);
      publish_feedback("RETURNING_TO_PICK", 0.88f);
      moveToWaypoint("waypoints.pick");
      std::this_thread::sleep_for(
        std::chrono::milliseconds(static_cast<int>(settle_time_sec_ * 1000)));
      sendGripper(gripper_open_pos_);   // release object at pick position
      publish_feedback("MOVING_HOME", 0.95f);
      moveToWaypoint("waypoints.home");
      result->verdict    = "UNCERTAIN";
      result->pass_votes = 0;
      result->fail_votes = 0;
      publish_feedback("DONE", 1.0f);
      goal_handle->succeed(result);
      busy_ = false;
      return;
    }

    std::string verdict = (total_pass > total_fail) ? "PASS" : "FAIL";
    RCLCPP_INFO(this->get_logger(),
                "Verdict: %s  (pass_votes=%d  fail_votes=%d)",
                verdict.c_str(), total_pass, total_fail);

    // ── Pre-place: retract arm to clear inspection camera before sorting ──────
    publish_feedback("MOVING_TO_PRE_PLACE", 0.88f);
    if (!moveToWaypoint("waypoints.pre_place")) {
      abortGoal(goal_handle, result, "Failed to reach pre_place pose");
      busy_ = false; return;
    }

    // ── Sort ──────────────────────────────────────────────────────────────────
    const std::string sort_wp = (verdict == "PASS") ? "waypoints.sort_pass" : "waypoints.sort_fail";
    publish_feedback("MOVING_TO_SORT_" + verdict, 0.90f);
    if (!moveToWaypoint(sort_wp)) {
      abortGoal(goal_handle, result, "Failed to reach sort pose");
      busy_ = false; return;
    }
    // Let arm fully settle at sort pose before releasing / moving home
    std::this_thread::sleep_for(
      std::chrono::milliseconds(static_cast<int>(settle_time_sec_ * 1000) + 500));
    // Open gripper to release object
    sendGripper(gripper_open_pos_);
    std::this_thread::sleep_for(std::chrono::milliseconds(800));

    // ── Return home ───────────────────────────────────────────────────────────
    publish_feedback("MOVING_HOME", 0.95f);
    moveToWaypoint("waypoints.home");  // best-effort, don't abort on failure
    std::this_thread::sleep_for(
      std::chrono::milliseconds(static_cast<int>(settle_time_sec_ * 1000) + 500));

    // ── Succeed ───────────────────────────────────────────────────────────────
    result->verdict    = verdict;
    result->pass_votes = total_pass;
    result->fail_votes = total_fail;
    publish_feedback("DONE", 1.0f);
    goal_handle->succeed(result);
    RCLCPP_INFO(this->get_logger(), "Inspection complete — verdict: %s", verdict.c_str());

    busy_ = false;
  }

  // ── Motion helpers ───────────────────────────────────────────────────────────

  bool moveToWaypoint(const std::string & param_name)
  {
    if (!move_group_) {
      RCLCPP_ERROR(this->get_logger(), "MoveGroup not initialised.");
      return false;
    }
    auto joint_values = this->get_parameter(param_name).as_double_array();
    if (joint_values.size() != 6) {
      RCLCPP_ERROR(this->get_logger(),
                   "Waypoint '%s' must have 6 values, got %zu",
                   param_name.c_str(), joint_values.size());
      return false;
    }

    move_group_->setJointValueTarget(joint_values);
    MoveGroupInterface::Plan plan;
    if (move_group_->plan(plan) != moveit::core::MoveItErrorCode::SUCCESS) {
      RCLCPP_WARN(this->get_logger(), "Planning failed for waypoint '%s'", param_name.c_str());
      return false;
    }
    move_group_->execute(plan);
    return true;
  }

  void sendGripper(double position)
  {
    if (!gripper_client_->wait_for_action_server(std::chrono::seconds(2))) {
      RCLCPP_WARN(this->get_logger(), "Gripper action server not available.");
      return;
    }
    auto goal = GripperCommand::Goal();
    goal.command.position   = position;
    goal.command.max_effort = 0.0;
    gripper_client_->async_send_goal(goal);
    std::this_thread::sleep_for(std::chrono::milliseconds(1200));
  }

  // ── Vote collection ──────────────────────────────────────────────────────────

  /**
   * Enables result collection for the given duration (based on target frame
   * count), then disables it and returns (pass_count, fail_count).
   */
  std::pair<int, int> collectVotes(int target_frames)
  {
    {
      std::lock_guard<std::mutex> lock(vote_mutex_);
      vote_buffer_.clear();
    }
    collecting_ = true;

    // Wait until we have enough frames or timeout (3× expected time)
    const auto deadline = std::chrono::steady_clock::now()
                          + std::chrono::milliseconds(target_frames * 300);
    while (std::chrono::steady_clock::now() < deadline) {
      {
        std::lock_guard<std::mutex> lock(vote_mutex_);
        if (static_cast<int>(vote_buffer_.size()) >= target_frames) break;
      }
      std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
    collecting_ = false;

    std::lock_guard<std::mutex> lock(vote_mutex_);
    int pass = 0, fail = 0;
    for (const auto & r : vote_buffer_) {
      if (r.label == "PASS") ++pass;
      else                   ++fail;
    }
    RCLCPP_INFO(this->get_logger(),
                "  Votes collected: %zu frames  PASS=%d  FAIL=%d",
                vote_buffer_.size(), pass, fail);
    return {pass, fail};
  }

  // ── Goal helpers ─────────────────────────────────────────────────────────────

  void abortGoal(const std::shared_ptr<GoalHandle> & gh,
                 std::shared_ptr<RunInspection::Result> & res,
                 const std::string & reason)
  {
    RCLCPP_ERROR(this->get_logger(), "Aborting inspection: %s", reason.c_str());
    res->verdict    = "ERROR";
    res->pass_votes = 0;
    res->fail_votes = 0;
    gh->abort(res);
  }

  void cancelGoal(const std::shared_ptr<GoalHandle> & gh,
                  std::shared_ptr<RunInspection::Result> & res)
  {
    RCLCPP_INFO(this->get_logger(), "Inspection cancelled.");
    res->verdict = "CANCELLED";
    gh->canceled(res);
  }

  static std::string upperCase(std::string s)
  {
    for (auto & c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
  }
};

// ─────────────────────────────────────────────────────────────────────────────

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<InspectionCommanderNode>();

  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  std::thread spin_thread([&executor]() { executor.spin(); });

  node->setupMoveGroup(std::static_pointer_cast<rclcpp::Node>(node));

  RCLCPP_INFO(rclcpp::get_logger("inspection_commander"),
              "Ready — waiting for /run_inspection goals.");

  spin_thread.join();
  rclcpp::shutdown();
  return 0;
}
