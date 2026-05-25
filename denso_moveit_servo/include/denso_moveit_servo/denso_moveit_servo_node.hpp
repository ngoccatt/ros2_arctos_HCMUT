#pragma once

#include <memory>
#include <string>
#include <atomic>

// ROS
#include <rclcpp/rclcpp.hpp>

// Servo
#include <moveit_servo/servo_parameters.h>
#include <moveit_servo/servo.h>
#include <moveit/planning_scene_monitor/planning_scene_monitor.h>
#include <std_srvs/srv/trigger.hpp>

namespace denso_moveit_servo
{

class DensoMoveItServoNode : public rclcpp::Node
{
public:
  /**
   * @brief Constructor for DensoMoveItServoNode component
   * @param options Node options for ROS2 component configuration
   */
  explicit DensoMoveItServoNode(const rclcpp::NodeOptions& options = rclcpp::NodeOptions());

  /**
   * @brief Destructor - cleanup resources
   */
  ~DensoMoveItServoNode();

private:
  /**
   * @brief Initialize the planning scene monitor
   * @return true if successful, false otherwise
   */
  bool initializePlanningSceneMonitor();

  /**
   * @brief Initialize the MoveIt Servo
   * @return true if successful, false otherwise
   */
  bool initializeServo();

  /**
    * @brief Deferred initialization callback executed after construction
    */
    void deferredInitialize();

    /**
   * @brief Setup servo control services
   */
  void setupServices();

  // Service callbacks
  void startServoCallback(
    const std::shared_ptr<std_srvs::srv::Trigger::Request>& request,
    const std::shared_ptr<std_srvs::srv::Trigger::Response>& response);

  void stopServoCallback(
    const std::shared_ptr<std_srvs::srv::Trigger::Request>& request,
    const std::shared_ptr<std_srvs::srv::Trigger::Response>& response);

  void pauseServoCallback(
    const std::shared_ptr<std_srvs::srv::Trigger::Request>& request,
    const std::shared_ptr<std_srvs::srv::Trigger::Response>& response);

  void unpauseServoCallback(
    const std::shared_ptr<std_srvs::srv::Trigger::Request>& request,
    const std::shared_ptr<std_srvs::srv::Trigger::Response>& response);

  // Member variables
  std::shared_ptr<planning_scene_monitor::PlanningSceneMonitor> planning_scene_monitor_;
  std::unique_ptr<moveit_servo::Servo> servo_;
  moveit_servo::ServoParameters::SharedConstPtr servo_parameters_;
  rclcpp::TimerBase::SharedPtr deferred_init_timer_;
  std::atomic<bool> initialized_{ false };

  // Services
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr start_servo_service_;
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr stop_servo_service_;
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr pause_servo_service_;
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr unpause_servo_service_;

  // Logger
  static const rclcpp::Logger LOGGER;
};

}  // namespace denso_moveit_servo