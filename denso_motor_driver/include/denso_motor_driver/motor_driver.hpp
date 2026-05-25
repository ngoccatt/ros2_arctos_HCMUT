#ifndef DENSO_MOTOR_DRIVER_HPP_
#define DENSO_MOTOR_DRIVER_HPP_

#include "denso_motor_driver/motor_types.hpp"
#include "denso_motor_driver/uart_protocol.hpp"
#include "serial/serial.h"
#include <map>
#include <memory>

/**
 * @file motor_driver.hpp
 * @brief This file contains the declaration of the MotorDriver class.
 */

namespace denso_motor_driver {

// this is to define whether we need to convert from degrees to encoder steps or not.
#define ENCODER_CONVERSION_NEEDED  false

/**
 * @class MotorDriver
 * @brief The MotorDriver class provides an interface for controlling motors.
 */
class MotorDriver {
public:
    /**
     * @brief Constructs a MotorDriver object.
     * @param node A shared pointer to the ROS 2 node.
     */
    explicit MotorDriver(rclcpp::Node::SharedPtr node);

    /**
     * @brief Destroys the MotorDriver object.
     */
    ~MotorDriver();

    void processUartMessage(void);
    // Joint management

    void setProtocol(std::shared_ptr<UartProtocol> protocol);

    /**
     * @brief Adds a joint to the motor driver.
     * @param joint_name The name of the joint.
     * @param motor_id The ID of the motor.
     */
    void addJoint(const std::string& joint_name, uint8_t motor_id, std::string hardware_type, double gear_ratio = 1.0, bool inverted = false, bool inverted_feedback = false, double zero_position = 0.0);

    /**
     * @brief Removes a joint from the motor driver.
     * @param joint_name The name of the joint to remove.
     */
    void removeJoint(const std::string& joint_name);
    
    // Core control functions

    /**
     * @brief Sets the position of a joint.
     * @param joint_name The name of the joint.
     * @param position The desired position.
     * @param acceleration Acceleration of the motor movement, default to 20 (in range 0 - 255)
     */
    void setJointPosition(const std::string& joint_name, double position, double acceleration = 20, double velocity = 100);
    
    /**
     * @brief Gets the position of a joint.
     * @param joint_name The name of the joint.
     * @return The position of the joint.
     */
    double getJointPosition(const std::string& joint_name, bool convert_to_rad = true) const;
    
    // Motor control

    /**
     * @brief Stops a motor.
     * @param joint_name The name of the joint associated with the motor.
     */
    void stopMotor(const std::string& joint_name);

    /**
     * @brief Stops all motors.
     */
    void stopAllMotors();

    // Parameter management

    /**
     * @brief Sets the limits of a joint.
     * @param joint_name The name of the joint.
     * @param pos_min The minimum position.
     * @param pos_max The maximum position.
     * @param vel_max The maximum velocity.
     * @param acc_max The maximum acceleration.
     */
    void setJointLimits(const std::string& joint_name, 
                       double pos_min, double pos_max,
                       double vel_max, double acc_max);

    // Diagnostics

    /**
     * @brief Gets the position error of a joint.
     * @param joint_name The name of the joint.
     * @return The position error of the joint.
     */
    double getPositionError(const std::string& joint_name) const;

    /**
     * @brief Gets the time since the last update of a joint.
     * @param joint_name The name of the joint.
     * @return The time since the last update of the joint.
     */
    rclcpp::Duration getTimeSinceLastUpdate(const std::string& joint_name) const;

    /**
     * @brief Gets the last error message of a joint.
     * @param joint_name The name of the joint.
     * @return The last error message of the joint.
     */
    std::string getLastError(const std::string& joint_name) const;

    /**
     * @brief Write command to actuator, using buffer from each motors
     * @param 
     */
    void writeCommand();

private:
    rclcpp::Node::SharedPtr node_; /**< A shared pointer to the ROS 2 node. */
    std::shared_ptr<UartProtocol> uart_protocol_; /**< A shared pointer to the UART protocol. */
    
    std::map<std::string, JointConfig> joints_; /**< A map of joint names to joint configurations. */
    std::map<uint8_t, std::string> motor_to_joint_map_; /**< A map of motor IDs to joint names. */
    double position_tolerance_; /**< The position tolerance for joint control. */
    double velocity_tolerance_; /**< The velocity tolerance for joint control. */
    // Internal handlers

    // specify the size of encoder data for each joint
    const uint8_t ENCODER_SIZE = 1;
    // old buffer, use for comparison
    std::vector<std::vector<double>> pre_encoder_data_;

    /**
     * @brief Processes an encoder response from a motor.
     * @param motor_id The ID of the motor.
     * @param data The data received from the motor.
     */
    void processEncoderResponse(uint8_t motor_id, const std::vector<double>& data);

    /**
     * @brief Checks if the encoder data has changed.
     * @param encoder_data The current encoder data.
     * @return True if the encoder data has changed, false otherwise.
     */
    bool isEncoderDataChanged(const std::vector<double>& encoder_data, const uint8_t motor_id) const;
};

} // namespace denso_motor_driver

#endif // DENSO_MOTOR_DRIVER_HPP_