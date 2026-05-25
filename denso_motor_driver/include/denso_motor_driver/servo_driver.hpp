#ifndef DENSO_MOTOR_DRIVER_HPP_
#define DENSO_MOTOR_DRIVER_HPP_

#include "denso_motor_driver/motor_types.hpp"
#include "denso_motor_driver/uart_protocol.hpp"
#include "serial/serial.h"
#include "denso_motor_driver/json.hpp"
#include <map>
#include <memory>

/**
 * @file motor_driver.hpp
 * @brief This file contains the declaration of the ServoDriver class.
 */

namespace denso_motor_driver {

using json = nlohmann::json;

// this is to define whether we need to convert from degrees to encoder steps or not.
#define ENCODER_CONVERSION_NEEDED  false

/**
 * @class ServoDriver
 * @brief The ServoDriver class provides an interface for controlling motors.
 */
class ServoDriver {
public:
    /**
     * @brief Constructs a ServoDriver object.
     * @param node A shared pointer to the ROS 2 node.
     */
    explicit ServoDriver(rclcpp::Node::SharedPtr node);

    /**
     * @brief Destroys the ServoDriver object.
     */
    ~ServoDriver();

    void processUartMessage(void);
    // servo management

    void setProtocol(std::shared_ptr<UartProtocol> protocol);
    
    /**
     * @brief Updates the states of the servos.
     */
    void writeQueryCommand();

    /**
     * @brief Adds a servo to the motor driver.
     * @param joint_name The name of the servo.
     * @param motor_id The ID of the motor.
     */
    void addServo(const std::string& joint_name, 
        uint8_t motor_id, 
        std::string hardware_type, 
        double gear_ratio = 1.0, 
        bool inverted = false, 
        bool inverted_feedback = false, 
        double zero_position = 0.0);

    /**
     * @brief Removes a servo from the motor driver.
     * @param joint_name The name of the servo to remove.
     */
    void removeServo(const std::string& joint_name);
    
    // Core control functions

    /**
     * @brief Sets the position of a servo.
     * @param joint_name The name of the servo.
     * @param position The desired position.
     * @param acceleration Acceleration of the motor movement, default to 20 (in range 0 - 255)
     */
    void setServoPosition(const std::string& joint_name, double position, double acceleration = 20, double velocity = 100);

    /**
     * @brief Gets the position of a servo.
     * @param joint_name The name of the servo.
     * @return The position of the servo.
     */
    double getServoPosition(const std::string& joint_name, bool convert_to_rad = true) const;
    
    // Motor control

    /**
     * @brief Stops a servo.
     * @param joint_name The name of the servo associated with the motor.
     */
    void stopMotor(const std::string& joint_name);

    /**
     * @brief Stops all motors.
     */
    void stopAllMotors();

    // Parameter management

    /**
     * @brief Sets the limits of a servo.
     * @param joint_name The name of the servo.
     * @param pos_min The minimum position.
     * @param pos_max The maximum position.
     */
    void setServoLimits(const std::string& joint_name, 
                       double pos_min, double pos_max);

    /**
     * @brief Get the load for a specific servo.
     * 
     * This function retrieves the load for a given servo name. Load is useful to know if the gripper movevement is stopped due to object.
     * If the servo is not found, an error message is logged and 0.0 is returned.
     * 
     * @param joint_name The name of the servo.
     * @return The load of the servo.
     */
    double getServoLoad(const std::string& joint_name) const;

    /**
     * @brief Gets the time since the last update of a servo.
     * @param joint_name The name of the servo.
     * @return The time since the last update of the servo.
     */
    rclcpp::Duration getTimeSinceLastUpdate(const std::string& joint_name) const;

    /**
     * @brief Gets the last error message of a servo.
     * @param joint_name The name of the servo.
     * @return The last error message of the servo.
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
    
    std::map<std::string, JointConfig> servos_; /**< A map of servo names to servo configurations. */
    std::map<uint8_t, std::string> motor_to_servo_map_; /**< A map of motor IDs to servo names. */
    double position_tolerance_; /**< The position tolerance for servo control. */
    double velocity_tolerance_; /**< The velocity tolerance for servo control. */
    // Internal handlers

    // old buffer, use for comparison
    double pre_encoder_data_;

    /**
     * @brief Processes an encoder response from a motor.
     * @param motor_id The ID of the motor.
     * @param data The data received from the motor.
     */
    void processServoResponse(uint8_t motor_id, std::string data);

    /**
     * @brief Checks if the encoder data has changed.
     * @param encoder_data The current encoder data.
     * @return True if the encoder data has changed, false otherwise.
     */
    bool isServoDataChanged(double encoder_data) const;
};

} // namespace denso_motor_driver

#endif // DENSO_MOTOR_DRIVER_HPP_