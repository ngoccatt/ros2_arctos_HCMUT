#include "denso_moveit_servo/denso_moveit_servo_node.hpp"

#include <rclcpp_components/register_node_macro.hpp>

using namespace std::chrono_literals;

namespace denso_moveit_servo
{

const rclcpp::Logger DensoMoveItServoNode::LOGGER = rclcpp::get_logger("denso_moveit_servo_node");

DensoMoveItServoNode::DensoMoveItServoNode(const rclcpp::NodeOptions& options)
  : Node("denso_moveit_servo_node", options)
{
  RCLCPP_INFO(LOGGER, "Initializing DensoMoveItServoNode...");
  setupServices();

  deferred_init_timer_ = this->create_wall_timer(
      0ms, std::bind(&DensoMoveItServoNode::deferredInitialize, this));

  RCLCPP_INFO(LOGGER, "DensoMoveItServoNode constructed, waiting for deferred initialization");
}

DensoMoveItServoNode::~DensoMoveItServoNode()
{
  RCLCPP_INFO(LOGGER, "Shutting down DensoMoveItServoNode...");
  
  // Stop servo if it's running
  if (servo_)
  {
    servo_->setPaused(true);
  }
}

void DensoMoveItServoNode::deferredInitialize()
{
  if (deferred_init_timer_)
  {
    deferred_init_timer_->cancel();
  }

  if (initialized_.load())
  {
    return;
  }

  if (!initializePlanningSceneMonitor())
  {
    RCLCPP_FATAL(LOGGER, "Failed to initialize planning scene monitor");
    return;
  }

  if (!initializeServo())
  {
    RCLCPP_FATAL(LOGGER, "Failed to initialize servo");
    return;
  }

  initialized_.store(true);
  RCLCPP_INFO(LOGGER, "DensoMoveItServoNode initialized successfully");
}

bool DensoMoveItServoNode::initializePlanningSceneMonitor()
{
  // Create planning scene monitor
  planning_scene_monitor_ = std::make_shared<planning_scene_monitor::PlanningSceneMonitor>(
      shared_from_this(), "robot_description", "planning_scene_monitor");

  // Load servo parameters first to get joint topics
  servo_parameters_ = moveit_servo::ServoParameters::makeServoParameters(shared_from_this(), "denso_moveit_servo");
  if (!servo_parameters_)
  {
    RCLCPP_ERROR(LOGGER, "Failed to load servo parameters");
    return false;
  }

  // Configure planning scene monitor
  if (planning_scene_monitor_->getPlanningScene())
  {
    planning_scene_monitor_->startStateMonitor(servo_parameters_->joint_topic);
    planning_scene_monitor_->startSceneMonitor(servo_parameters_->monitored_planning_scene_topic);
    planning_scene_monitor_->startWorldGeometryMonitor();
    planning_scene_monitor_->setPlanningScenePublishingFrequency(25);
    planning_scene_monitor_->getStateMonitor()->enableCopyDynamics(true);
    planning_scene_monitor_->startPublishingPlanningScene(
        planning_scene_monitor::PlanningSceneMonitor::UPDATE_SCENE,
        std::string(this->get_fully_qualified_name()) + "/publish_planning_scene");
  }
  else
  {
    RCLCPP_ERROR(LOGGER, "Planning scene not configured");
    return false;
  }

  // Handle primary/secondary planning scene monitor
  if (servo_parameters_->is_primary_planning_scene_monitor)
    planning_scene_monitor_->providePlanningSceneService();
  else
    planning_scene_monitor_->requestPlanningSceneState();

  return true;
}

bool DensoMoveItServoNode::initializeServo()
{
  if (!servo_parameters_ || !planning_scene_monitor_)
  {
    RCLCPP_ERROR(LOGGER, "Prerequisites for servo initialization not met");
    return false;
  }

  // Initialize the Servo C++ interface
  try
  {
    servo_ = std::make_unique<moveit_servo::Servo>(
        shared_from_this(), servo_parameters_, planning_scene_monitor_);
    RCLCPP_INFO(LOGGER, "Servo initialized successfully");
    return true;
  }
  catch (const std::exception& e)
  {
    RCLCPP_ERROR(LOGGER, "Failed to initialize servo: %s", e.what());
    return false;
  }
}

void DensoMoveItServoNode::setupServices()
{
  // Set up services for interacting with Servo
  start_servo_service_ = this->create_service<std_srvs::srv::Trigger>(
      "~/start_servo", 
      std::bind(&DensoMoveItServoNode::startServoCallback, this, 
                std::placeholders::_1, std::placeholders::_2));

  stop_servo_service_ = this->create_service<std_srvs::srv::Trigger>(
      "~/stop_servo",
      std::bind(&DensoMoveItServoNode::stopServoCallback, this,
                std::placeholders::_1, std::placeholders::_2));

  pause_servo_service_ = this->create_service<std_srvs::srv::Trigger>(
      "~/pause_servo",
      std::bind(&DensoMoveItServoNode::pauseServoCallback, this,
                std::placeholders::_1, std::placeholders::_2));

  unpause_servo_service_ = this->create_service<std_srvs::srv::Trigger>(
      "~/unpause_servo",
      std::bind(&DensoMoveItServoNode::unpauseServoCallback, this,
                std::placeholders::_1, std::placeholders::_2));

  RCLCPP_INFO(LOGGER, "Services set up successfully");
}

void DensoMoveItServoNode::startServoCallback(
    const std::shared_ptr<std_srvs::srv::Trigger::Request>& /*request*/,
    const std::shared_ptr<std_srvs::srv::Trigger::Response>& response)
{
  if (!initialized_.load())
  {
    response->success = false;
    response->message = "Servo node initialization in progress or failed";
    RCLCPP_WARN(LOGGER, "Cannot start servo - node not initialized yet");
    return;
  }

  if (servo_)
  {
    servo_->start();
    response->success = true;
    response->message = "Servo started successfully";
    RCLCPP_INFO(LOGGER, "Servo started");
  }
  else
  {
    response->success = false;
    response->message = "Servo not initialized";
    RCLCPP_ERROR(LOGGER, "Cannot start servo - not initialized");
  }
}

void DensoMoveItServoNode::stopServoCallback(
    const std::shared_ptr<std_srvs::srv::Trigger::Request>& /*request*/,
    const std::shared_ptr<std_srvs::srv::Trigger::Response>& response)
{
  if (!initialized_.load())
  {
    response->success = false;
    response->message = "Servo node initialization in progress or failed";
    RCLCPP_WARN(LOGGER, "Cannot stop servo - node not initialized yet");
    return;
  }

  if (servo_)
  {
    servo_->setPaused(true);
    response->success = true;
    response->message = "Servo stopped successfully";
    RCLCPP_INFO(LOGGER, "Servo stopped");
  }
  else
  {
    response->success = false;
    response->message = "Servo not initialized";
    RCLCPP_ERROR(LOGGER, "Cannot stop servo - not initialized");
  }
}

void DensoMoveItServoNode::pauseServoCallback(
    const std::shared_ptr<std_srvs::srv::Trigger::Request>& /*request*/,
    const std::shared_ptr<std_srvs::srv::Trigger::Response>& response)
{
  if (!initialized_.load())
  {
    response->success = false;
    response->message = "Servo node initialization in progress or failed";
    RCLCPP_WARN(LOGGER, "Cannot pause servo - node not initialized yet");
    return;
  }

  if (servo_)
  {
    servo_->setPaused(true);
    response->success = true;
    response->message = "Servo paused successfully";
    RCLCPP_INFO(LOGGER, "Servo paused");
  }
  else
  {
    response->success = false;
    response->message = "Servo not initialized";
    RCLCPP_ERROR(LOGGER, "Cannot pause servo - not initialized");
  }
}

void DensoMoveItServoNode::unpauseServoCallback(
    const std::shared_ptr<std_srvs::srv::Trigger::Request>& /*request*/,
    const std::shared_ptr<std_srvs::srv::Trigger::Response>& response)
{
  if (!initialized_.load())
  {
    response->success = false;
    response->message = "Servo node initialization in progress or failed";
    RCLCPP_WARN(LOGGER, "Cannot unpause servo - node not initialized yet");
    return;
  }

  if (servo_)
  {
    servo_->setPaused(false);
    response->success = true;
    response->message = "Servo unpaused successfully";
    RCLCPP_INFO(LOGGER, "Servo unpaused");
  }
  else
  {
    response->success = false;
    response->message = "Servo not initialized";
    RCLCPP_ERROR(LOGGER, "Cannot unpause servo - not initialized");
  }
}

}  // namespace denso_moveit_servo

// Register the component with the ROS 2 component system
RCLCPP_COMPONENTS_REGISTER_NODE(denso_moveit_servo::DensoMoveItServoNode)

// For backwards compatibility, provide a main function that creates the component
int main(int argc, char* argv[])
{
  rclcpp::init(argc, argv);
  
  // Use MultiThreadedExecutor as required by MoveIt Servo
  rclcpp::executors::MultiThreadedExecutor executor;
  
  rclcpp::NodeOptions options;
  // Enable intra process comms for performance
  options.use_intra_process_comms(true);
  
  auto node = std::make_shared<denso_moveit_servo::DensoMoveItServoNode>(options);
  executor.add_node(node);
  
  try
  {
    executor.spin();
  }
  catch (const std::exception& e)
  {
    RCLCPP_ERROR(rclcpp::get_logger("main"), "Exception in executor: %s", e.what());
  }
  
  rclcpp::shutdown();
  return 0;
}
