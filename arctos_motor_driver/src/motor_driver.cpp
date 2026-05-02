#include "arctos_motor_driver/motor_driver.hpp"
#include <cmath>
#include <string>
#include <sstream>

/**
 * @brief The MotorDriver class is responsible for controlling and managing multiple motors.
 * 
 * This class provides methods for adding and removing joints, setting joint position and velocity,
 * enabling and disabling motors, stopping motors, calibrating and homing motors, and retrieving
 * joint position and velocity. It also handles CAN message callbacks for processing motor responses
 * and updating joint states.
 */
namespace arctos_motor_driver {

/**
 * @brief Constructs a MotorDriver object.
 *
 * This constructor initializes a MotorDriver object with the given node.
 * It sets up a CAN message subscription and creates a timer for periodic status updates.
 *
 * @param node A shared pointer to the rclcpp::Node object.
 */
MotorDriver::MotorDriver(rclcpp::Node::SharedPtr node) 
    : node_(node),
      uart_protocol_(std::make_shared<UartProtocol>()) {
}

MotorDriver::~MotorDriver() {
    RCLCPP_INFO(node_->get_logger(), "Shutting down motor driver, stopping all motors...");
    stopAllMotors();
}

void MotorDriver::setProtocol(std::shared_ptr<UartProtocol> protocol) {
    uart_protocol_ = protocol;
}
/**
 * @brief Adds a new joint to the motor driver.
 *
 * This function adds a new joint to the motor driver with the specified joint name and motor ID.
 * It checks if the joint already exists or if the motor ID is already in use by another joint.
 * If the joint is successfully added, it creates a new joint configuration and initializes the motor.
 *
 * @param joint_name The name of the joint to be added.
 * @param motor_id The ID of the motor associated with the joint.
 */
void MotorDriver::addJoint(const std::string& joint_name, uint8_t motor_id, std::string hardware_type, double gear_ratio, bool inverted,bool inverted_feedback, double zero_position) {
    // Check if joint already exists
    if (joints_.find(joint_name) != joints_.end()) {
        RCLCPP_WARN(node_->get_logger(), "Joint %s already exists", joint_name.c_str());
        return;
    }

    // Check if motor_id is already in use
    if (motor_to_joint_map_.find(motor_id) != motor_to_joint_map_.end()) {
        RCLCPP_ERROR(node_->get_logger(), "Motor ID %d is already in use by joint %s", 
                     motor_id, motor_to_joint_map_[motor_id].c_str());
        return;
    }

    // Validate gear ratio
    if (gear_ratio <= 0.0) {
        RCLCPP_ERROR(node_->get_logger(), "Invalid gear ratio %.2f for joint %s", gear_ratio, joint_name.c_str());
        return;
    }

    // Create and insert new joint
    joints_.insert({joint_name, JointConfig(motor_id, joint_name, node_->get_clock())});
    joints_[joint_name].hardware_type = hardware_type;
    joints_[joint_name].gear_ratio = gear_ratio;
    joints_[joint_name].inverted = inverted;
    joints_[joint_name].inverted_feedback = inverted_feedback;
    joints_[joint_name].zero_position = zero_position;
    motor_to_joint_map_[motor_id] = joint_name;

    joints_[joint_name].last_update = node_->get_clock()->now();  // Initialize timestamp
    // add a vector of "encoder" data for each joint, emplace_back() at the pre_encoder_data
    // make sure that the datatype used in emplace_back here match the definition!
    pre_encoder_data_.emplace_back(std::vector<double>(1, 0));

    RCLCPP_INFO(node_->get_logger(), "Added joint %s with motor ID %d and gear ratio %.2f:1", 
                joint_name.c_str(), motor_id, gear_ratio);

    // Log current joints and motor-to-joint map
    RCLCPP_DEBUG(node_->get_logger(), "Current Joints:");
    for (const auto& joint : joints_) {
        RCLCPP_DEBUG(node_->get_logger(), "  Joint Name: %s, Motor ID: %d, Gear Ratio: %.2f:1",
                    joint.first.c_str(), joint.second.motor_id, joint.second.gear_ratio);
    }

    RCLCPP_DEBUG(node_->get_logger(), "Motor-to-Joint Map:");
    for (const auto& entry : motor_to_joint_map_) {
        RCLCPP_DEBUG(node_->get_logger(), "  Motor ID %d -> Joint %s", entry.first, entry.second.c_str());
    }
}

/**
 * @brief Removes a joint from the MotorDriver.
 * 
 * This function removes a joint from the MotorDriver based on the provided joint name.
 * If the joint is found, the associated motor is stopped, and the joint is removed from the internal data structures.
 * 
 * @param joint_name The name of the joint to be removed.
 */
void MotorDriver::removeJoint(const std::string& joint_name) {
    auto it = joints_.find(joint_name);
    if (it != joints_.end()) {
        uint8_t motor_id = it->second.motor_id;
        stopMotor(joint_name);
        motor_to_joint_map_.erase(motor_id);
        joints_.erase(it);
        RCLCPP_INFO(node_->get_logger(), "Removed joint %s", joint_name.c_str());
    }
}

/**
 * @brief Sets the position of the joint.
 *
 * This function sets the desired position of the joint.
 * application only care about what joint. 
 * the driver has to handle logic how to successfully rotate the joint.
 *
 * @param position The desired position of the joint in radians.
 * @param acceleration The desired acceleration in degrees/s^2.
 */
void MotorDriver::setJointPosition(const std::string& joint_name, double position, double acceleration, double velocity) {
    auto it = joints_.find(joint_name);
    if (it == joints_.end()) {
        RCLCPP_ERROR(node_->get_logger(), "Joint %s not found", joint_name.c_str());
        return;
    }

    auto& joint = it->second;

    if (joint.inverted) {
        position = -position;
    }

    // Scale the position by the gear ratio
    double motor_position = position * joint.gear_ratio;

    // Convert motor position from radians to degrees
    double motor_position_deg = motor_position * MotorConstants::RAD_TO_DEG;

    RCLCPP_INFO(node_->get_logger(), "Setting joint %s position to (%s) %.2f radians (%.2f degrees on motor protactor) with gear ratio %.2f:1",
                joint_name.c_str(), joint.inverted ? "inverted" : "normal", position, motor_position_deg, joint.gear_ratio);

    // minimum speed is 30 to prevent sending speed = 0, which will stop the motor!
    uint16_t speed = static_cast<uint16_t>(std::clamp(velocity, 30.0, 3000.0));  
    uint8_t acc_value = static_cast<uint8_t>(std::clamp(acceleration, 10.0, 255.0));

    // Write to the data buffer, ready to send.
    joint.command_velocity = speed;
    joint.command_acceleration = acc_value;
    joint.command_position = motor_position_deg;
}

/**
 * @brief Write command to actuator, using buffer from each motors
 * @param 
 */
void MotorDriver::writeCommand() {
    std::string command = "";
    std::vector<double> commandPositions(joints_.size(), 0.0);
    for (auto& [joint_name, joint] : joints_) {
        // motor_id start from 1, so we need to minus 1 to get the correct index
        commandPositions[joint.motor_id-1] = joint.command_position;
        joint.last_command = node_->get_clock()->now();
    }
    for (size_t i = 0; i < commandPositions.size(); i++) {
        command += std::to_string(commandPositions[i]) + ";";
    }
    RCLCPP_INFO(node_->get_logger(), "Write command to actuator: %s", command.c_str());
    
    uart_protocol_->sendPosition(commandPositions);
}

/**
 * @brief Retrieves the position of a joint.
 * 
 * This function returns the position of the specified joint. If the joint is not found, an error message is logged and 0.0 is returned.
 * 
 * @param joint_name The name of the joint to retrieve the position from.
 * @return The position of the joint.
 */
double MotorDriver::getJointPosition(const std::string& joint_name, bool convert_to_rad) const {
    auto it = joints_.find(joint_name);
    if (it == joints_.end()) {
        RCLCPP_ERROR(node_->get_logger(), "Joint %s not found", joint_name.c_str());
        return 0.0;
    }

    RCLCPP_DEBUG(node_->get_logger(), "Retrieved position for joint %s: %.3f", joint_name.c_str(), it->second.position);
    if(convert_to_rad)
        return it->second.position * MotorConstants::DEG_TO_RAD;
    else
        return it->second.position;
    
}

/**
 * Stops the motor associated with the given joint name.
 *
 * @param joint_name The name of the joint.
 */
void MotorDriver::stopMotor(const std::string& joint_name) {
    auto it = joints_.find(joint_name);
    if (it == joints_.end()) {
        RCLCPP_ERROR(node_->get_logger(), "Joint %s not found", joint_name.c_str());
        return;
    }

    // Send emergency stop command
    
    // Reset command values
    it->second.command_velocity = 0.0;
    it->second.command_position = it->second.position;
}

/**
 * @brief Stops all motors.
 *
 * This function stops all motors controlled by the MotorDriver class.
 * It iterates over all joints and calls the stopMotor function for each joint.
 */
void MotorDriver::stopAllMotors() {
    for (const auto& joint : joints_) {
        stopMotor(joint.first);
    }
}

void MotorDriver::processUartMessage() {
    std::string message;
    std::vector<double> decodedPositions(6, 0.0);
    do {
        message = uart_protocol_->getFromBuffer();
        if (message != "") {
            if (!uart_protocol_->decodeMessage(message, decodedPositions)) {
                RCLCPP_ERROR(node_->get_logger(), "Failed to decode UART message: %s", message.c_str());
                continue;
            }
            if ((decodedPositions.size()) != joints_.size())
            {
                RCLCPP_ERROR(node_->get_logger(), "The number of decoded joints does not match with the configured joints!");
            }
            else
            {
                
                for (auto& [joint_name, joint] : joints_) 
                {
                    std::vector<double> decodedPosition = {decodedPositions[joint.motor_id - 1]};
                    processEncoderResponse(joint.motor_id, decodedPosition);      
                    
                }
            }
            
        }
    }
    while (message != "");
}

/**
 * @brief Process the response from the encoder for a specific motor.
 *
 * This function extracts the encoder data from the received data and updates the joint state accordingly.
 * It calculates the position error by subtracting the current joint position from the commanded position.
 *
 * @param motor_id The ID of the motor.
 * @param data The received data from the encoder. currently, data is just a vector of double with size 1.
 */
void MotorDriver::processEncoderResponse(uint8_t motor_id, const std::vector<double>& data) {
    auto it = motor_to_joint_map_.find(motor_id);
    if (it == motor_to_joint_map_.end()) {
        RCLCPP_WARN(node_->get_logger(), "No joint found for motor ID: %d", motor_id);
        return;
    }

    const std::string& joint_name = it->second;
    auto& joint = joints_[joint_name];

    // if the encoder response is exactly the same as previous encoder data, no need to process.
    if (isEncoderDataChanged(data, motor_id) == false) {
        // RCLCPP_INFO(node_->get_logger(), "No new data for %d", motor_id);
        return;
    } else {
        pre_encoder_data_[motor_id-1] = data;
    }

    try {
        // **Log raw data for debugging**
        RCLCPP_DEBUG(node_->get_logger(), "Raw Encoder Data for %s", joint_name.c_str());
        for (size_t i = 0; i < data.size(); i++) {
            RCLCPP_DEBUG(node_->get_logger(), "Byte %zu: 0x%02f", i, data[i]);
        }

        // **Get the decoded data as the first element**
        double motor_angle_deg = data.front();
        RCLCPP_DEBUG(node_->get_logger(), "Decoded motor angle (degrees): %.2f", motor_angle_deg);

        // **Check for invalid values (NaN/Inf)**
        if (!std::isfinite(motor_angle_deg)) {
            RCLCPP_WARN(node_->get_logger(), "Invalid motor angle detected for joint %s. Skipping update.", joint_name.c_str());
            return;
        }

        // **Sanity check for absurd values**
        constexpr double MAX_MOTOR_DEGREES = 360.0 * 1000;  // 1000 revolutions
        if (motor_angle_deg > MAX_MOTOR_DEGREES || motor_angle_deg < -MAX_MOTOR_DEGREES) {
            RCLCPP_WARN(node_->get_logger(), "Discarding out-of-range motor angle: %.2f degrees for motor ID %d", 
                        motor_angle_deg, motor_id);
            return;
        }

        // **Convert motor angle to joint angle**
        double joint_angle_deg = motor_angle_deg / joint.gear_ratio;

        // **Apply inversion_feedback BEFORE zero position offset**
        if (joint.inverted_feedback) {
            joint_angle_deg = -joint_angle_deg;
        }

        RCLCPP_DEBUG(node_->get_logger(), "Final computed joint angle: %.3f degrees", joint_angle_deg);

        // // **Filter sudden jumps using a moving average**
        // constexpr double FILTER_ALPHA = 0.3;
        // joint.position = FILTER_ALPHA * joint_angle_deg + (1.0 - FILTER_ALPHA) * joint.position;

        // **Print Joint Limits for Debugging**
        RCLCPP_DEBUG(node_->get_logger(), "Joint %s: Min = %.3f, Max = %.3f, Current = %.3f", 
                    joint_name.c_str(), joint.position_min, joint.position_max, joint.position);

        
        // **Check if joint limits are valid**
        constexpr double TOLERANCE = 0.1;
        if (joint_angle_deg < (joint.position_min - TOLERANCE) || joint_angle_deg > (joint.position_max + TOLERANCE)) {
            RCLCPP_WARN(node_->get_logger(), "Ignoring out-of-bounds encoder value %.3f degrees for joint %s (limits: %.3f to %.3f)", 
                        joint_angle_deg, joint_name.c_str(), joint.position_min, joint.position_max);
            return;
        }

        joint.position = joint_angle_deg;

        // **Update Joint State**
        joint.position_error = joint.command_position - joint.position;

        // **Apply Deadband Filtering (to remove tiny errors)**
        constexpr double POSITION_DEADBAND = 0.0001;
        if (std::abs(joint.position) < POSITION_DEADBAND) {
            joint.position = 0.0;
        }
        RCLCPP_INFO(node_->get_logger(), "Updated motor %d (%s) position: %.2f degrees", 
                    joint.motor_id, joint.inverted_feedback ? "inverted feedback" : "normal", joint.position);

        joint.last_update = node_->get_clock()->now();
    } catch (const std::exception& e) {
        RCLCPP_ERROR(node_->get_logger(), "Error processing encoder response: %s", e.what());
    }
}

/**
 * @brief Checks if the encoder data has changed.
 * @param encoder_data The current encoder data. expect a 6-byte vector
 * @return True if the encoder data has changed, false otherwise.
 */
bool MotorDriver::isEncoderDataChanged(const std::vector<double>& encoder_data, const uint8_t motor_id) const {
    if (motor_id < 1 || motor_id > pre_encoder_data_.size()) {
        RCLCPP_WARN(node_->get_logger(), "Invalid motor ID or wrong encoder data size: %d", motor_id);
        return false;
    }
    // Compare first bytes
    for (uint8_t i = 0; i < ENCODER_SIZE; ++i) {
        if (encoder_data[i] != pre_encoder_data_[motor_id - 1][i]) {
            return true;
        }
    }
    return false;
}

/**
 * @brief Sets the limits for a specific joint.
 * 
 * This function sets the position, velocity, and acceleration limits for a specific joint.
 * If the joint is not found, an error message is logged and the function returns.
 * 
 * @param joint_name The name of the joint.
 * @param pos_min The minimum position limit for the joint.
 * @param pos_max The maximum position limit for the joint.
 * @param vel_max The maximum velocity limit for the joint.
 * @param acc_max The maximum acceleration limit for the joint.
 */
void MotorDriver::setJointLimits(const std::string& joint_name, 
                                double pos_min, double pos_max,
                                double vel_max, double acc_max) {
    auto it = joints_.find(joint_name);
    if (it == joints_.end()) {
        RCLCPP_ERROR(node_->get_logger(), "Joint %s not found", joint_name.c_str());
        return;
    }

    // Validate limits
    if (pos_min > pos_max) {
        RCLCPP_ERROR(node_->get_logger(), 
                    "Invalid position limits for joint %s: min (%.2f) > max (%.2f)",
                    joint_name.c_str(), pos_min, pos_max);
        return;
    }

    // Update joint limits
    it->second.position_min = pos_min;
    it->second.position_max = pos_max;

    if (vel_max < 0.0) {
        RCLCPP_ERROR(node_->get_logger(), 
                    "Invalid velocity limit for joint %s: %.2f",
                    joint_name.c_str(), vel_max);
        return;
    }

    it->second.velocity_max = vel_max;

    if (acc_max < 0.0) {
        RCLCPP_ERROR(node_->get_logger(), 
                    "Invalid acceleration limit for joint %s: %.2f",
                    joint_name.c_str(), acc_max);
        return;
    }

    it->second.acceleration_max = acc_max;

    RCLCPP_INFO(node_->get_logger(), 
                "Updated limits for joint %s: pos=[%.2f, %.2f], vel=%.2f, acc=%.2f",
                joint_name.c_str(), pos_min, pos_max, vel_max, acc_max);
}

/**
 * @brief Get the position error for a specific joint.
 * 
 * This function retrieves the position error for a given joint name.
 * If the joint is not found, an error message is logged and 0.0 is returned.
 * 
 * @param joint_name The name of the joint.
 * @return The position error of the joint.
 */
double MotorDriver::getPositionError(const std::string& joint_name) const {
    auto it = joints_.find(joint_name);
    if (it == joints_.end()) {
        RCLCPP_ERROR(node_->get_logger(), "Joint %s not found", joint_name.c_str());
        return 0.0;
    }
    return it->second.position_error;
}

/**
 * @brief Get the time elapsed since the last update for a specific joint.
 * 
 * This function returns the duration between the current time and the last update time
 * for the specified joint. If the joint is not found, an error message is logged and
 * a zero duration is returned.
 * 
 * @param joint_name The name of the joint.
 * @return The duration between the current time and the last update time for the joint.
 */
rclcpp::Duration MotorDriver::getTimeSinceLastUpdate(const std::string& joint_name) const {
    auto it = joints_.find(joint_name);
    if (it == joints_.end()) {
        RCLCPP_ERROR(node_->get_logger(), "Joint %s not found", joint_name.c_str());
        return rclcpp::Duration(0, 0);
    }
    
    // Use the same clock source
    auto clock = node_->get_clock();
    return clock->now() - it->second.last_update;
}

/**
 * Retrieves the last error message for a specific joint.
 *
 * @param joint_name The name of the joint.
 * @return The last error message for the specified joint. If the joint is not found, "Joint not found" is returned.
 */
std::string MotorDriver::getLastError(const std::string& joint_name) const {
    auto it = joints_.find(joint_name);
    if (it == joints_.end()) {
        return "Joint not found";
    }
    return it->second.status.error_message;
}

} // namespace arctos_motor_driver