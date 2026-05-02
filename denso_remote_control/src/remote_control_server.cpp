#include <cstdio>
#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <cmath>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "rclcpp_components/register_node_macro.hpp"

#include <std_msgs/msg/string.hpp>
#include "denso_interfaces/msg/joint_state_degree.hpp"
#include "denso_interfaces/action/move_to_pose.hpp"

#include <moveit/move_group_interface/move_group_interface.h>
#include <moveit/planning_scene_interface/planning_scene_interface.h>

// All source files that use ROS logging should define a file-specific
// static const rclcpp::Logger named LOGGER, located at the top of the file
// and inside the namespace with the narrowest scope (if there is one)
// static const rclcpp::Logger LOGGER = rclcpp::get_logger("remote_control");

// send_goal via command line: 
// ros2 action send_goal /move_to_pose denso_interfaces/action/MoveToPose "{pose: {position: {x: 0.3, y: 0.0, z: 0.5}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}"

namespace action_denso_control
{


class RemoteControlServer : public rclcpp::Node
{
public:
  using MoveToPose = denso_interfaces::action::MoveToPose;
  using GoalHandleMoveToPose = rclcpp_action::ServerGoalHandle<MoveToPose>;

  RemoteControlServer(const rclcpp::NodeOptions & options = rclcpp::NodeOptions())
  : Node("remote_control_server", options)
  {
    using namespace std::placeholders;

    // "move_to_pose" is essentially the action name.
    this->action_server_ = rclcpp_action::create_server<MoveToPose>(
      this,
      "move_to_pose",
      std::bind(&RemoteControlServer::handle_goal, this, _1, _2),
      std::bind(&RemoteControlServer::handle_cancel, this, _1),
      std::bind(&RemoteControlServer::handle_accepted, this, _1));

    // a seperate node should be create for movegroup spinning and monitoring, to make sure that JointState are updated.
    node_options.automatically_declare_parameters_from_overrides(true);
    move_group_node_ = rclcpp::Node::make_shared("move_group_node", node_options);
    move_group_executor_.add_node(move_group_node_);
    // In constructor, replace the detach line:
    move_group_executor_thread_ = std::thread([this]() { move_group_executor_.spin(); });
    // then we use that exact node to connect with move_group.
    move_group = new moveit::planning_interface::MoveGroupInterface(move_group_node_, PLANNING_GROUP);
    // We will use the :planning_scene_interface:`PlanningSceneInterface` class to add or remove objects in our environment
    // Raw pointers are frequently used to refer to the planning group for improved performance.
    joint_model_group_target = move_group->getCurrentState()->getJointModelGroup(PLANNING_GROUP);
  }

  // Add a destructor:
  ~RemoteControlServer()
  {
    move_group_executor_.cancel();
    if (move_group_executor_thread_.joinable()) {
      move_group_executor_thread_.join();
    }
  }

private:

  rclcpp_action::Server<MoveToPose>::SharedPtr action_server_;

  rclcpp_action::GoalResponse handle_goal(
    const rclcpp_action::GoalUUID& uuid,
    std::shared_ptr<const MoveToPose::Goal> goal)
  {
    bool goalWithPose = goal->use_pose;
    if (goalWithPose)
    {
        RCLCPP_INFO(this->get_logger(), "Received goal request with Pose position: %f %f %f, orientation: %f %f %f %f", 
        goal->pose.position.x,
        goal->pose.position.y,
        goal->pose.position.z,
        goal->pose.orientation.x,
        goal->pose.orientation.y,
        goal->pose.orientation.z,
        goal->pose.orientation.w
        );
    }
    else
    {
        if (goal->joints.size() < 6) {
            RCLCPP_WARN(this->get_logger(), "Received goal request with insufficient joint positions. Expected at least 6, but got %zu. Rejecting goal.", goal->joints.size());
            return rclcpp_action::GoalResponse::REJECT;
        } 
        RCLCPP_INFO(this->get_logger(), "Received goal request with Joint position: %f %f %f %f %f %f", 
        goal->joints[0],
        goal->joints[1],
        goal->joints[2],
        goal->joints[3],
        goal->joints[4],
        goal->joints[5]
        );
        // silently skip joints that's over 6th joint.
    }
    

    (void)uuid;
    return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
  }

  rclcpp_action::CancelResponse handle_cancel(
    const std::shared_ptr<GoalHandleMoveToPose> goal_handle)
  {
    RCLCPP_INFO(this->get_logger(), "Received request to cancel goal");
    (void)goal_handle;
    return rclcpp_action::CancelResponse::ACCEPT;
  }

  void handle_accepted(const std::shared_ptr<GoalHandleMoveToPose> goal_handle)
  {
    using namespace std::placeholders;
    
    // this needs to return quickly to avoid blocking the executor, so spin up a new thread
    // Since the execution is a long-running operation, we spawn off a 
    // thread to do the actual work and return from handle_accepted quickly.
    std::thread{
      std::bind(&RemoteControlServer::execute, this, _1), goal_handle
    }.detach();
  
  }

  void execute(const std::shared_ptr<GoalHandleMoveToPose> goal_handle)
  {
  
    RCLCPP_INFO(this->get_logger(), "Executing goal");
    rclcpp::Rate loop_rate(2);
    // the goal
    const auto goal = goal_handle->get_goal();
    // regular feedback
    auto feedback = std::make_shared<MoveToPose::Feedback>();
    auto & step = feedback->step;
    step = "none";
    // result
    auto result = std::make_shared<MoveToPose::Result>();
    std::vector<double> joint_group_positions;

    // Check if there is a cancel request
    if (goal_handle->is_canceling()) {
      result->completed = false;
      goal_handle->canceled(result);
      RCLCPP_INFO(this->get_logger(), "Goal canceled");
      return;
    }

    step = "planning";
    goal_handle->publish_feedback(feedback);
    RCLCPP_INFO(this->get_logger(), "Planning...");

    // two option for planning: use Pose or Joint
    bool planWithPose = goal->use_pose;
    if (planWithPose) 
    {
        move_group->setPoseTarget(goal->pose);
    }
    else
    {
        moveit::core::RobotStatePtr current_state = move_group->getCurrentState(10);
        current_state->copyJointGroupPositions(joint_model_group_target, joint_group_positions);
        for (size_t i = 0; i < joint_group_positions.size(); i++) {
          joint_group_positions[i] = goal->joints[i];
        }
        move_group->setJointValueTarget(joint_group_positions);
    }
    
    bool success = (move_group->plan(my_plan) == moveit::core::MoveItErrorCode::SUCCESS);

    if (!success) {
      result->completed = false;
      goal_handle->abort(result);
      step = "planning failed";
      goal_handle->publish_feedback(feedback);
      RCLCPP_INFO(this->get_logger(), "Planning failed");
      return;
    }

    step = "executing";
    goal_handle->publish_feedback(feedback);
    RCLCPP_INFO(this->get_logger(), "Executing...");
    move_group->execute(my_plan);

    // delay for some time to allow hardware to execute the plan till the end.
    loop_rate.sleep();

    if (rclcpp::ok()) {
      step = "completed";
      goal_handle->publish_feedback(feedback);

      result->completed = true;
      goal_handle->succeed(result);
      RCLCPP_INFO(this->get_logger(), "Goal succeeded");
    }
  }

  rclcpp::Publisher<denso_interfaces::msg::JointStateDegree>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  const std::string PLANNING_GROUP = "denso_arm";
  moveit::planning_interface::MoveGroupInterface* move_group = nullptr;
  moveit::planning_interface::PlanningSceneInterface planning_scene_interface;
  const moveit::core::JointModelGroup* joint_model_group_target = nullptr;
  moveit::planning_interface::MoveGroupInterface::Plan my_plan;
  rclcpp::executors::SingleThreadedExecutor move_group_executor_;
  rclcpp::Node::SharedPtr move_group_node_ = nullptr;
  std::thread move_group_executor_thread_;
  rclcpp::NodeOptions node_options;
};
  
} // namespace action_denso_control

RCLCPP_COMPONENTS_REGISTER_NODE(action_denso_control::RemoteControlServer)