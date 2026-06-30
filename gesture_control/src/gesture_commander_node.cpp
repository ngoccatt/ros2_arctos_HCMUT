/**
 * gesture_commander_node.cpp
 *
 * ROS2 node that subscribes to /gesture_detection, applies debounce + confidence
 * filtering, and executes robot commands via MoveGroupInterface (arm) and a
 * GripperCommand action client (gripper).
 *
 * Two control modes (set use_servo in gesture_config.yaml):
 *   use_servo: false  — MoveGroupInterface for all arm moves (default)
 *   use_servo: true   — MoveIt Servo JointJog for 'point'; MoveGroupInterface only for 'home'
 *
 * Topics subscribed:
 *   /gesture_detection  (gesture_control/msg/GestureDetection)
 *
 * Topics published:
 *   /gesture_command    (std_msgs/String)   — executed gesture label, for monitoring
 *
 * Gesture mapping:
 *   thumbs-up → MoveIt2 named pose "home"
 *   point     → Z_joint + point_delta_rad (elbow forward)
 *   open      → gripper_gear_right_joint → gripper_open_pos  (1.40 rad, wide open)
 *   fist      → gripper_gear_right_joint → gripper_closed_pos (0.05 rad, gentle grip)
 *   none      → move_group.stop() / servo auto-halt
 *
 * Performance metrics logged every 10 s via logPerformanceStats():
 *   - Detection counts: received / conf_rejected / stability_pending /
 *     stability_rejected / cooldown_rejected / exec_blocked / executed / plan_failed
 *   - Command acceptance rate  (executed / received * 100 %)
 *   - Mean pipe latency  (camera frame capture → gestureCallback, via capture_time_unix)
 *   - Mean execution latency  (command dispatch → motion complete)
 */

#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <std_msgs/msg/string.hpp>
#include <std_srvs/srv/trigger.hpp>

#include <moveit/move_group_interface/move_group_interface.h>

#include <control_msgs/action/gripper_command.hpp>
#include <control_msgs/msg/joint_jog.hpp>

#include <deque>
#include <atomic>
#include <thread>
#include <mutex>
#include <algorithm>
#include <cmath>
#include <chrono>

#include "gesture_control/msg/gesture_detection.hpp"

using GestureDetection     = gesture_control::msg::GestureDetection;
using GripperCommandAction = control_msgs::action::GripperCommand;
using MoveGroupInterface   = moveit::planning_interface::MoveGroupInterface;
using Trigger              = std_srvs::srv::Trigger;

// Z_joint limits (degrees → radians, from ros2_controllers.yaml)
static constexpr double Z_LOWER_RAD = -119.0 * M_PI / 180.0;   // -2.0769 rad
static constexpr double Z_UPPER_RAD =  169.0 * M_PI / 180.0;   //  2.9496 rad

// Servo JointJog publish rate (must be > 1/incoming_command_timeout = 10 Hz)
static constexpr int SERVO_PUBLISH_HZ = 20;

// ─────────────────────────────────────────────────────────────────────────────

class GestureCommanderNode : public rclcpp::Node
{
public:
  GestureCommanderNode()
  : Node("gesture_commander_node"),
    executing_(false)
  {
    // ── Parameters ────────────────────────────────────────────────────────────
    this->declare_parameter("confidence_threshold", 0.70);
    this->declare_parameter("stability_frames",     3);
    this->declare_parameter("command_cooldown_sec", 2.0);
    this->declare_parameter("point_delta_rad",      0.3);
    this->declare_parameter("gripper_open_pos",     1.47);
    this->declare_parameter("gripper_closed_pos",   0.10);
    this->declare_parameter("use_servo",            false);
    this->declare_parameter("point_velocity_rad_s", 0.5);

    confidence_threshold_  = this->get_parameter("confidence_threshold").as_double();
    stability_frames_      = this->get_parameter("stability_frames").as_int();
    command_cooldown_sec_  = this->get_parameter("command_cooldown_sec").as_double();
    point_delta_rad_       = this->get_parameter("point_delta_rad").as_double();
    gripper_open_pos_      = this->get_parameter("gripper_open_pos").as_double();
    gripper_closed_pos_    = this->get_parameter("gripper_closed_pos").as_double();
    use_servo_             = this->get_parameter("use_servo").as_bool();
    point_velocity_rad_s_  = this->get_parameter("point_velocity_rad_s").as_double();

    // ── Subscriber ───────────────────────────────────────────────────────────
    gesture_sub_ = this->create_subscription<GestureDetection>(
      "/gesture_detection", 10,
      std::bind(&GestureCommanderNode::gestureCallback, this, std::placeholders::_1));

    // ── Publishers ───────────────────────────────────────────────────────────
    cmd_pub_         = this->create_publisher<std_msgs::msg::String>("/gesture_command", 10);
    exec_result_pub_ = this->create_publisher<std_msgs::msg::String>("/gesture_exec_result", 10);

    // ── Gripper action client ─────────────────────────────────────────────────
    gripper_client_ = rclcpp_action::create_client<GripperCommandAction>(
      this, "/denso_hand_controller/gripper_cmd");

    // ── Servo interfaces (only created when use_servo is true) ────────────────
    if (use_servo_) {
      joint_jog_pub_ = this->create_publisher<control_msgs::msg::JointJog>(
        "/denso_moveit_servo_node/delta_joint_cmds", 10);
      servo_start_client_ = this->create_client<Trigger>(
        "/denso_moveit_servo_node/start_servo");
      servo_stop_client_  = this->create_client<Trigger>(
        "/denso_moveit_servo_node/stop_servo");
      RCLCPP_INFO(this->get_logger(),
        "Servo mode enabled — JointJog on /denso_moveit_servo_node/delta_joint_cmds");
    }

    last_command_time_ = this->now();

    // ── Performance stats timer — fires every 10 s ───────────────────────────
    stats_timer_ = this->create_wall_timer(
      std::chrono::seconds(10),
      std::bind(&GestureCommanderNode::logPerformanceStats, this));

    RCLCPP_INFO(this->get_logger(),
      "GestureCommanderNode created [use_servo=%s] (move_group not yet ready)",
      use_servo_ ? "true" : "false");
  }

  /**
   * Call from main() after the node is managed by a shared_ptr and the
   * executor has started spinning. MoveGroupInterface requires the node
   * to be alive and processing callbacks while it connects to move_group.
   */
  void setupMoveGroup(const std::shared_ptr<rclcpp::Node> & node)
  {
    move_group_ = std::make_shared<MoveGroupInterface>(node, "denso_arm");
    move_group_->setMaxVelocityScalingFactor(0.3);
    move_group_->setMaxAccelerationScalingFactor(0.3);
    RCLCPP_INFO(this->get_logger(),
      "MoveGroupInterface ready  [group=denso_arm  planning_frame=%s]",
      move_group_->getPlanningFrame().c_str());

    if (use_servo_) {
      callServoService(servo_start_client_, "start_servo");
    }
  }

private:
  // ── Parameters ─────────────────────────────────────────────────────────────
  double confidence_threshold_;
  int    stability_frames_;
  double command_cooldown_sec_;
  double point_delta_rad_;
  double gripper_open_pos_;
  double gripper_closed_pos_;
  bool   use_servo_;
  double point_velocity_rad_s_;

  // ── State ───────────────────────────────────────────────────────────────────
  std::deque<std::string> gesture_buffer_;
  std::mutex              buffer_mutex_;
  rclcpp::Time            last_command_time_;
  std::atomic<bool>       executing_;

  // ── ROS interfaces ──────────────────────────────────────────────────────────
  rclcpp::Subscription<GestureDetection>::SharedPtr gesture_sub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr  cmd_pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr  exec_result_pub_;
  rclcpp_action::Client<GripperCommandAction>::SharedPtr gripper_client_;

  // ── Servo interfaces ────────────────────────────────────────────────────────
  rclcpp::Publisher<control_msgs::msg::JointJog>::SharedPtr joint_jog_pub_;
  rclcpp::Client<Trigger>::SharedPtr servo_start_client_;
  rclcpp::Client<Trigger>::SharedPtr servo_stop_client_;

  // ── MoveIt2 ─────────────────────────────────────────────────────────────────
  std::shared_ptr<MoveGroupInterface> move_group_;

  // ── Performance counters (lock-free — all atomic) ───────────────────────────
  // received         : every detection that passes the move_group guard
  // conf_rejected    : dropped due to confidence < threshold
  // stability_pending: buffer not yet full (warming up after gesture change)
  // stability_rejected: buffer full but not all frames match (unstable gesture)
  // cooldown_rejected: within command_cooldown_sec of the last command
  // exec_blocked     : previous command still executing
  // executed         : commands actually dispatched
  // plan_failed      : MoveIt planning returned non-SUCCESS
  std::atomic<uint64_t> stat_received_{0};
  std::atomic<uint64_t> stat_conf_rejected_{0};
  std::atomic<uint64_t> stat_stability_pending_{0};
  std::atomic<uint64_t> stat_stability_rejected_{0};
  std::atomic<uint64_t> stat_cooldown_rejected_{0};
  std::atomic<uint64_t> stat_exec_blocked_{0};
  std::atomic<uint64_t> stat_executed_{0};
  std::atomic<uint64_t> stat_plan_failed_{0};

  // ── Latency accumulators (guarded by stats_mutex_) ──────────────────────────
  std::mutex   stats_mutex_;
  double       pipe_latency_sum_ms_ = 0.0;   // camera capture → this callback
  uint64_t     pipe_latency_count_  = 0;
  double       exec_latency_sum_ms_ = 0.0;   // command dispatch → motion complete
  uint64_t     exec_latency_count_  = 0;

  // ── Stats timer ──────────────────────────────────────────────────────────────
  rclcpp::TimerBase::SharedPtr stats_timer_;

  // ── Servo helper ────────────────────────────────────────────────────────────

  void callServoService(rclcpp::Client<Trigger>::SharedPtr client, const std::string & name)
  {
    if (!client->wait_for_service(std::chrono::seconds(2))) {
      RCLCPP_WARN(this->get_logger(), "Servo service not available: %s", name.c_str());
      return;
    }
    client->async_send_request(std::make_shared<Trigger::Request>());
    RCLCPP_INFO(this->get_logger(), "Called servo service: %s", name.c_str());
  }

  // ── Gesture callback ────────────────────────────────────────────────────────

  void gestureCallback(const GestureDetection & msg)
  {
    if (!move_group_) {
      return;  // Not yet initialised
    }

    stat_received_++;

    // 1. Confidence filter
    if (msg.confidence < static_cast<float>(confidence_threshold_)) {
      stat_conf_rejected_++;
      return;
    }

    // 2. Rolling stability buffer
    std::string gesture;
    {
      std::lock_guard<std::mutex> lock(buffer_mutex_);
      gesture_buffer_.push_back(msg.label);
      if (static_cast<int>(gesture_buffer_.size()) > stability_frames_) {
        gesture_buffer_.pop_front();
      }
      if (static_cast<int>(gesture_buffer_.size()) < stability_frames_) {
        stat_stability_pending_++;
        return;
      }

      // All N entries must agree on the same label
      const std::string & front = gesture_buffer_.front();
      bool all_same = std::all_of(
        gesture_buffer_.begin(), gesture_buffer_.end(),
        [&front](const std::string & s) { return s == front; });
      if (!all_same) {
        stat_stability_rejected_++;
        return;
      }
      gesture = front;
    }

    // 3. Cooldown
    double elapsed = (this->now() - last_command_time_).seconds();
    if (elapsed < command_cooldown_sec_) {
      stat_cooldown_rejected_++;
      return;
    }

    // 4. Execution gate
    if (executing_.load()) {
      stat_exec_blocked_++;
      return;
    }

    // 5. Commit: lock in state before spawning thread
    last_command_time_ = this->now();
    {
      std::lock_guard<std::mutex> lock(buffer_mutex_);
      gesture_buffer_.clear();
    }
    executing_ = true;
    stat_executed_++;

    // Pipe latency: camera frame grab → this callback arrival.
    // capture_time_unix is Unix epoch (s) from the inference backend.
    // Only valid when use_sim_time is false (real hardware clock).
    if (msg.capture_time_unix > 0.0) {
      double now_unix = std::chrono::duration<double>(
        std::chrono::system_clock::now().time_since_epoch()).count();
      double pipe_ms = (now_unix - msg.capture_time_unix) * 1000.0;
      RCLCPP_INFO(this->get_logger(),
        "Gesture '%s' triggered  conf=%.2f  pipe_latency=%.0f ms",
        gesture.c_str(), msg.confidence, pipe_ms);
      {
        std::lock_guard<std::mutex> lk(stats_mutex_);
        pipe_latency_sum_ms_ += pipe_ms;
        pipe_latency_count_++;
      }
    } else {
      RCLCPP_INFO(this->get_logger(),
        "Gesture '%s' triggered  conf=%.2f", gesture.c_str(), msg.confidence);
    }

    std::thread([this, gesture]() {
      auto t0 = std::chrono::steady_clock::now();
      executeCommand(gesture);
      double exec_ms = std::chrono::duration<double, std::milli>(
        std::chrono::steady_clock::now() - t0).count();
      RCLCPP_INFO(this->get_logger(),
        "Command '%s' done in %.0f ms", gesture.c_str(), exec_ms);
      {
        std::lock_guard<std::mutex> lk(stats_mutex_);
        exec_latency_sum_ms_ += exec_ms;
        exec_latency_count_++;
      }
      // Publish "label:latency_ms" so metrics node can log per-gesture exec latency
      auto result_msg = std_msgs::msg::String();
      result_msg.data = gesture + ":" + std::to_string(static_cast<int>(exec_ms));
      exec_result_pub_->publish(result_msg);
      executing_ = false;
    }).detach();
  }

  // ── Performance stats ────────────────────────────────────────────────────────

  void logPerformanceStats()
  {
    uint64_t rx   = stat_received_.load();
    uint64_t conf = stat_conf_rejected_.load();
    uint64_t pend = stat_stability_pending_.load();
    uint64_t stab = stat_stability_rejected_.load();
    uint64_t cool = stat_cooldown_rejected_.load();
    uint64_t blk  = stat_exec_blocked_.load();
    uint64_t exec = stat_executed_.load();
    uint64_t fail = stat_plan_failed_.load();
    double   accept = (rx > 0) ? static_cast<double>(exec) / rx * 100.0 : 0.0;

    RCLCPP_INFO(this->get_logger(),
      "[PERF] rx=%lu  conf_rej=%lu  pend=%lu  stab_rej=%lu  "
      "cool_rej=%lu  blk=%lu  exec=%lu  plan_fail=%lu  accept=%.1f%%",
      rx, conf, pend, stab, cool, blk, exec, fail, accept);

    std::lock_guard<std::mutex> lk(stats_mutex_);
    if (pipe_latency_count_ > 0) {
      RCLCPP_INFO(this->get_logger(),
        "[PERF] pipe_latency  avg=%.0f ms  n=%lu",
        pipe_latency_sum_ms_ / pipe_latency_count_, pipe_latency_count_);
    }
    if (exec_latency_count_ > 0) {
      RCLCPP_INFO(this->get_logger(),
        "[PERF] exec_latency  avg=%.0f ms  n=%lu",
        exec_latency_sum_ms_ / exec_latency_count_, exec_latency_count_);
    }
  }

  // ── Command dispatch ────────────────────────────────────────────────────────

  void executeCommand(const std::string & gesture)
  {
    if      (gesture == "thumbs-up") { executeHome();                       }
    else if (gesture == "point")     { executePoint();                      }
    else if (gesture == "open")      { executeGripper(gripper_open_pos_);   }
    else if (gesture == "fist")      { executeGripper(gripper_closed_pos_); }
    else if (gesture == "none")      { executeStop();                       }
    else {
      RCLCPP_WARN(this->get_logger(), "Unknown gesture label: '%s'", gesture.c_str());
      return;
    }

    // Publish for monitoring / logging
    auto cmd_msg = std_msgs::msg::String();
    cmd_msg.data = gesture;
    cmd_pub_->publish(cmd_msg);
  }

  // ── Motion primitives ───────────────────────────────────────────────────────

  void executeHome()
  {
    RCLCPP_INFO(this->get_logger(), "Moving to 'home' pose...");

    // Stop servo to avoid trajectory command conflicts during MoveGroupInterface execution
    if (use_servo_) {
      callServoService(servo_stop_client_, "stop_servo");
      std::this_thread::sleep_for(std::chrono::milliseconds(300));
    }

    move_group_->setNamedTarget("home");
    MoveGroupInterface::Plan plan;
    if (move_group_->plan(plan) == moveit::core::MoveItErrorCode::SUCCESS) {
      move_group_->execute(plan);
      RCLCPP_INFO(this->get_logger(), "Home pose reached.");
    } else {
      stat_plan_failed_++;
      RCLCPP_WARN(this->get_logger(), "Failed to plan home pose.");
    }

    // Resume servo after MoveGroupInterface is done
    if (use_servo_) {
      callServoService(servo_start_client_, "start_servo");
    }
  }

  void executePoint()
  {
    if (use_servo_) {
      executePointServo();
    } else {
      executePointMoveIt();
    }
  }

  // MoveIt path: getCurrentState → setJointValueTarget → plan → execute
  void executePointMoveIt()
  {
    RCLCPP_INFO(this->get_logger(),
      "Moving arm via MoveIt (Z_joint += %.3f rad)...", point_delta_rad_);

    auto current_state = move_group_->getCurrentState(5.0);
    if (!current_state) {
      RCLCPP_WARN(this->get_logger(), "Could not get current robot state.");
      return;
    }

    const auto * jmg = current_state->getJointModelGroup("denso_arm");
    std::vector<double> joint_values;
    current_state->copyJointGroupPositions(jmg, joint_values);

    const auto & joint_names = jmg->getVariableNames();
    auto it = std::find(joint_names.begin(), joint_names.end(), "Z_joint");
    if (it == joint_names.end()) {
      RCLCPP_ERROR(this->get_logger(), "Z_joint not found in 'denso_arm' group.");
      return;
    }
    const size_t z_idx = static_cast<size_t>(std::distance(joint_names.begin(), it));

    const double current_z = joint_values[z_idx];
    joint_values[z_idx] = std::clamp(current_z + point_delta_rad_, Z_LOWER_RAD, Z_UPPER_RAD);

    RCLCPP_INFO(this->get_logger(),
      "Z_joint: %.4f → %.4f rad", current_z, joint_values[z_idx]);

    move_group_->setJointValueTarget(joint_values);
    MoveGroupInterface::Plan plan;
    if (move_group_->plan(plan) == moveit::core::MoveItErrorCode::SUCCESS) {
      move_group_->execute(plan);
      RCLCPP_INFO(this->get_logger(), "Arm raised.");
    } else {
      stat_plan_failed_++;
      RCLCPP_WARN(this->get_logger(), "Failed to plan arm raise.");
    }
  }

  // Servo path: publish JointJog velocity to servo for a computed duration
  // No planning — arm starts moving within one servo publish_period (~150ms)
  void executePointServo()
  {
    const double velocity   = (point_delta_rad_ >= 0) ? point_velocity_rad_s_ : -point_velocity_rad_s_;
    const double duration_s = std::abs(point_delta_rad_) / std::abs(point_velocity_rad_s_);
    const int    steps      = static_cast<int>(duration_s * SERVO_PUBLISH_HZ) + 1;

    RCLCPP_INFO(this->get_logger(),
      "Raising arm via Servo (Z_joint %.3f rad/s for %.2fs, %d steps)...",
      velocity, duration_s, steps);

    control_msgs::msg::JointJog jog;
    jog.header.frame_id = "base_link";
    jog.joint_names     = {"Z_joint"};
    jog.velocities      = {velocity};
    jog.duration        = 1.0 / SERVO_PUBLISH_HZ;

    rclcpp::Rate rate(SERVO_PUBLISH_HZ);
    for (int i = 0; i < steps && rclcpp::ok(); ++i) {
      jog.header.stamp = this->now();
      joint_jog_pub_->publish(jog);
      rate.sleep();
    }

    RCLCPP_INFO(this->get_logger(), "Servo point raise done.");
  }

  void executeGripper(double position)
  {
    if (!gripper_client_->wait_for_action_server(std::chrono::seconds(2))) {
      RCLCPP_WARN(this->get_logger(),
        "Gripper action server not available: /denso_hand_controller/gripper_cmd");
      return;
    }

    auto goal = GripperCommandAction::Goal();
    goal.command.position   = position;
    goal.command.max_effort = 50.0;  // N — sufficient for gripper; ignored in simulation

    RCLCPP_INFO(this->get_logger(), "Sending gripper to %.4f rad...", position);

    // Fire and forget: the gripper controller handles completion
    gripper_client_->async_send_goal(goal);

    // Give the gripper time to move before the next command can be accepted
    std::this_thread::sleep_for(std::chrono::milliseconds(1500));
    RCLCPP_INFO(this->get_logger(), "Gripper command sent.");
  }

  void executeStop()
  {
    if (use_servo_) {
      // Servo auto-halts after incoming_command_timeout (0.1s) — nothing to do
      RCLCPP_INFO(this->get_logger(), "Servo mode: halting (stop sending commands).");
    } else {
      RCLCPP_INFO(this->get_logger(), "Stopping all arm motion (hold position)...");
      move_group_->stop();
      RCLCPP_INFO(this->get_logger(), "Motion stopped.");
    }
  }
};

// ─────────────────────────────────────────────────────────────────────────────

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<GestureCommanderNode>();

  // The executor must be spinning before MoveGroupInterface connects to
  // /move_group services/actions, so start spinning in a background thread.
  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  std::thread spin_thread([&executor]() { executor.spin(); });

  // Initialise MoveGroupInterface now that the executor is running.
  // Cast to base class pointer as required by MoveGroupInterface constructor.
  node->setupMoveGroup(std::static_pointer_cast<rclcpp::Node>(node));

  RCLCPP_INFO(rclcpp::get_logger("gesture_commander"), "Ready — listening for gestures.");

  spin_thread.join();
  rclcpp::shutdown();
  return 0;
}
