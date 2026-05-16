#include "arctos_motor_driver/servo_driver.hpp"
#include <cmath>
#include <string>
#include <sstream>
#include "arctos_motor_driver/json.hpp"

/**
 * @brief The ServoDriver class is responsible for controlling and managing WaveShare drivers, communicating via UART with SERVO HAT (A)
 * 
 * This class provides methods for adding and removing servos, setting servo position and velocity,
 * enabling and disabling motors, stopping motors, calibrating and homing motors, and retrieving
 * servo position and velocity. It also handles CAN message callbacks for processing motor responses
 * and updating servo states.
 */
namespace arctos_motor_driver {

// ANSI color codes for terminal output
#define RESET "\033[0m"
#define RED "\033[31m"
#define BOLD_RED "\033[1;31m"

// Soft_Limit here should be equal to the reduction in 3D servo: the servo full range is 0 -> 90. 
// it has been reduced to 5 -> 85 to avoid servo stalling, which might burn the servo
#define SOFT_LIMIT          5
// This value should be specified after testing full open and full close position of real gripper.
// the degree of servo for full close/full open, get by (pos - 1024) * 360/4096
#define REAL_SERVO_CLOSE    (185.1855469 - SOFT_LIMIT)
#define REAL_SERVO_OPEN     (90.3515625 + SOFT_LIMIT)

/**
 * @brief Constructs a ServoDriver object.
 *
 * This constructor initializes a ServoDriver object with the given node.
 * It sets up a CAN message subscription and creates a timer for periodic status updates.
 *
 * @param node A shared pointer to the rclcpp::Node object.
 */
ServoDriver::ServoDriver(rclcpp::Node::SharedPtr node) 
    : node_(node),
      uart_protocol_(std::make_shared<UartProtocol>()) {
}

ServoDriver::~ServoDriver() {
    RCLCPP_INFO(node_->get_logger(), "Shutting down servo driver, stopping all motors...");
    stopAllMotors();
}

void ServoDriver::setProtocol(std::shared_ptr<UartProtocol> protocol) {
    uart_protocol_ = protocol;
}
/**
 * @brief Adds a new servo to the servo driver. currently only 1 servo servo is supported.
 *
 * This function adds a new servo to the servo driver with the specified servo name and motor ID.
 * It checks if the servo already exists or if the motor ID is already in use by another servo.
 * If the servo is successfully added, it creates a new servo configuration and initializes the motor.
 *
 * @param servo_name The name of the servo to be added.
 * @param motor_id The ID of the motor associated with the servo.
 */
void ServoDriver::addServo(const std::string& servo_name, 
                            uint8_t motor_id, 
                            std::string hardware_type, 
                            double gear_ratio, 
                            bool inverted,
                            bool inverted_feedback, 
                            double zero_position) 
{
    // Check if servo already exists
    if (servos_.size() > 0) {
        RCLCPP_WARN(node_->get_logger(), "Only 1 servo servo is supported!");
        return;
    }
    if (servos_.find(servo_name) != servos_.end()) {
        RCLCPP_WARN(node_->get_logger(), "servo %s already exists", servo_name.c_str());
        return;
    }

    // Check if motor_id is already in use
    if (motor_to_servo_map_.find(motor_id) != motor_to_servo_map_.end()) {
        RCLCPP_ERROR(node_->get_logger(), "Motor ID %d is already in use by servo %s", 
                     motor_id, motor_to_servo_map_[motor_id].c_str());
        return;
    }

    // Validate gear ratio
    if (gear_ratio <= 0.0) {
        RCLCPP_ERROR(node_->get_logger(), "Invalid gear ratio %.2f for servo %s", gear_ratio, servo_name.c_str());
        return;
    }

    // Create and insert new servo
    servos_.insert({servo_name, JointConfig(motor_id, servo_name, node_->get_clock())});
    servos_[servo_name].hardware_type = hardware_type;
    servos_[servo_name].gear_ratio = gear_ratio;
    servos_[servo_name].inverted = inverted;
    servos_[servo_name].inverted_feedback = inverted_feedback;
    servos_[servo_name].zero_position = zero_position;
    motor_to_servo_map_[motor_id] = servo_name;

    servos_[servo_name].last_update = node_->get_clock()->now();  // Initialize timestamp

    RCLCPP_INFO(node_->get_logger(), "Added servo %s with motor ID %d and gear ratio %.2f:1", 
                servo_name.c_str(), motor_id, gear_ratio);

    // Log current servos and motor-to-servo map
    RCLCPP_DEBUG(node_->get_logger(), "Current servos:");
    for (const auto& servo : servos_) {
        RCLCPP_DEBUG(node_->get_logger(), "  servo Name: %s, Motor ID: %d, Gear Ratio: %.2f:1",
                    servo.first.c_str(), servo.second.motor_id, servo.second.gear_ratio);
    }

    RCLCPP_DEBUG(node_->get_logger(), "Motor-to-servo Map:");
    for (const auto& entry : motor_to_servo_map_) {
        RCLCPP_DEBUG(node_->get_logger(), "  Motor ID %d -> servo %s", entry.first, entry.second.c_str());
    }
}

/**
 * @brief Removes a servo from the ServoDriver.
 * 
 * This function removes a servo from the ServoDriver based on the provided servo name.
 * If the servo is found, the associated motor is stopped, and the servo is removed from the internal data structures.
 * 
 * @param servo_name The name of the servo to be removed.
 */
void ServoDriver::removeServo(const std::string& servo_name) {
    auto it = servos_.find(servo_name);
    if (it != servos_.end()) {
        uint8_t motor_id = it->second.motor_id;
        stopMotor(servo_name);
        motor_to_servo_map_.erase(motor_id);
        servos_.erase(it);
        RCLCPP_INFO(node_->get_logger(), "Removed servo %s", servo_name.c_str());
    }
}

/**
 * @brief Sets the position of the servo.
 *
 * This function sets the desired position of the servo.
 * application only care about what servo. 
 * the driver has to handle logic how to successfully rotate the servo.
 *
 * @param position The desired position of the servo in radians.
 * @param acceleration The desired acceleration in degrees/s^2.
 */
void ServoDriver::setServoPosition(const std::string& servo_name, double position, double acceleration, double velocity) {
    auto it = servos_.find(servo_name);
    if (it == servos_.end()) {
        RCLCPP_ERROR(node_->get_logger(), "servo %s not found", servo_name.c_str());
        return;
    }

    auto& servo = it->second;

    if (servo.inverted) {
        position = -position;
    }

    // Scale the position by the gear ratio
    double model_command_position = position * servo.gear_ratio;

    // Convert motor position from radians to degrees
    double model_command_position_deg = model_command_position * MotorConstants::RAD_TO_DEG;

    RCLCPP_INFO(node_->get_logger(), "Setting servo %s position to (%s) %.2f radians (%.2f degrees on motor protactor) with gear ratio %.2f:1",
                servo_name.c_str(), servo.inverted ? "inverted" : "normal", model_command_position, model_command_position_deg, servo.gear_ratio);


    uint16_t vel_value = static_cast<uint16_t>(std::clamp(velocity, 0.0, 4096.0));  
    uint8_t acc_value = static_cast<uint8_t>(std::clamp(acceleration, 0.0, 255.0));

    // Write to the data buffer, ready to send.
    servo.command_velocity = vel_value;
    servo.command_acceleration = acc_value;
    servo.command_position = model_command_position_deg;
}

/**
 * @brief Write command to actuator, using buffer from each motors
 *
 * Convert from 3D range: 0.420 (3D_close) -> 84.9983 (3D_open)
 * to Servo range       : 185 (Real_close)    -> ~101 (Real_open)
 * # Step 1: convert 3D degree [x] into acceptable servo degree
 * servo degree = (185 - ([x] - 3D_close))
 * # Step 2: convert servo degree to radian.
 * Position is send in radians intead of degree
 * @param void
 */
void ServoDriver::writeCommand() {
    std::string command = ""; 

    for (auto& [servo_name, servo] : servos_) {
        // # Step 1:
        double servo_degree = (REAL_SERVO_CLOSE - (servo.command_position - servo.position_min));
        RCLCPP_INFO(node_->get_logger(), "Step 1: servo_degree = %.3f", servo_degree);
        // # Step 2:
        double servo_rad = servo_degree * MotorConstants::DEG_TO_RAD;

        json ojbect = {
            {"T", GripperACommand::CONTROL_SERVO},
            {"angle", servo_rad},
            {"spd", servo.command_velocity},
            {"acc", servo.command_acceleration}
        };
       command += ojbect.dump();

    }
    RCLCPP_INFO(node_->get_logger(), "Write command to actuator: %s", command.c_str());
    
    uart_protocol_->sendMsgWithCLRF(command);
}

/*
This function send a query command to servo, request its current status.
*/
void ServoDriver::writeQueryCommand() {
    std::string command = "";
    json ojbect = {
        {"T", GripperACommand::READ_ENCODER}
    };
    command += ojbect.dump();

    // RCLCPP_INFO(node_->get_logger(), "Write query to actuator: %s", command.c_str());
    
    uart_protocol_->sendMsgWithCLRF(command);
}

/**
 * @brief Retrieves the position of a servo.
 * 
 * This function returns the position of the specified servo. If the servo is not found, an error message is logged and 0.0 is returned.
 * The position can be returned in radians or degrees based on the `convert_to_rad` flag.
 * @param servo_name The name of the servo to retrieve the position from.
 * @param convert_to_rad Flag indicating whether to convert the position to radians.
 * @return The position of the servo.
 */
double ServoDriver::getServoPosition(const std::string& servo_name, bool convert_to_rad) const {
    auto it = servos_.find(servo_name);
    if (it == servos_.end()) {
        RCLCPP_ERROR(node_->get_logger(), "servo %s not found", servo_name.c_str());
        return 0.0;
    }

    RCLCPP_DEBUG(node_->get_logger(), "Retrieved position for servo %s: %.3f", servo_name.c_str(), it->second.position);
    if(convert_to_rad)
        return it->second.position * MotorConstants::DEG_TO_RAD;
    else
        return it->second.position;
    
}

/**
 * Stops the motor associated with the given servo name.
 *
 * @param servo_name The name of the servo.
 */
void ServoDriver::stopMotor(const std::string& servo_name) {
    auto it = servos_.find(servo_name);
    if (it == servos_.end()) {
        RCLCPP_ERROR(node_->get_logger(), "servo %s not found", servo_name.c_str());
        return;
    }
}

/**
 * @brief Stops all motors.
 *
 * This function stops all motors controlled by the ServoDriver class.
 * It iterates over all servos and calls the stopMotor function for each servo.
 */
void ServoDriver::stopAllMotors() {
    for (const auto& servo : servos_) {
        stopMotor(servo.first);
    }
}

/**
 * @brief Process incoming UART messages and update servo states accordingly.
 *
 * This function continuously reads messages from the UART buffer, decodes them, and updates the servo states based on the received encoder data.
 * It uses a FIFO buffer to ensure that messages are processed in the order they were received.
 * Expect message in this json format: 
 * {"T":1051,"pos":3138,"speed":0,"load":-104,"voltage":124,"current":5,"temper":45,"mode":0}
 */
void ServoDriver::processUartMessage() {
    std::string message;
    do {
        message = uart_protocol_->getFromBuffer();
        if (message != "" && message != "{\"T\":105}") {
            for (auto& [servo_name, servo] : servos_) 
            {
                processServoResponse(servo.motor_id, message);
            }
        }
    }
    while (message != "");
}

/**
 * @brief Process the response from the encoder for a specific motor.
 *
 * This function extracts the encoder data from the received data and updates the servo state accordingly.
 * It calculates the position error by subtracting the current servo position from the commanded position.
 *
 * @param motor_id The ID of the motor.
 * @param data The received data from the encoder. currently, data is just a vector of double with size 1.
 */
void ServoDriver::processServoResponse(uint8_t motor_id, std::string data) {
    auto it = motor_to_servo_map_.find(motor_id);
    if (it == motor_to_servo_map_.end()) {
        RCLCPP_WARN(node_->get_logger(), "No servo found for motor ID: %d", motor_id);
        return;
    }

    const std::string& servo_name = it->second;
    auto& servo = servos_[servo_name];
    json jsonObject;

    try
    {
        jsonObject = json::parse(data);
    }
    catch (const std::exception &e)
    {
        RCLCPP_ERROR(node_->get_logger(), BOLD_RED "Unknown format %s" RESET, e.what());
        return;
    }

    int response_type = jsonObject["T"].get<int>();

    if (response_type == GripperACommand::CONTROL_SERVO ||
        response_type == GripperACommand::READ_ENCODER ||
        response_type == GripperACommand::OPEN_SERVO ||
        response_type == GripperACommand::CLOSE_SERVO)
    {
        RCLCPP_DEBUG(node_->get_logger(), "Skip loopback command");
        return;
    }

    double current_pos = jsonObject["pos"].get<double>();

    // if the encoder response is exactly the same as previous encoder data, no need to process.
    if (isServoDataChanged(current_pos) == false) {
        // RCLCPP_INFO(node_->get_logger(), "No new data for %d", motor_id);
        return;
    } else {
        // update the pre_encoder_data_ with the new data
        pre_encoder_data_ = current_pos; 
    }

    try {
        // **Get the decoded data as the first element + specific driver decoding logic for this gripper**
        // Step 1: unpack data from raw pos:
        // servo_angle = (pos - 1024) * 360/4096
        double servo_angle_deg = (current_pos - 1024.0) * MotorConstants::DEGREES_PER_REVOLUTION / MotorConstants::SERVO_ENCODER_STEPS;

        RCLCPP_DEBUG(node_->get_logger(), "Decoded motor angle (degrees): %.2f", servo_angle_deg);

        // **Check for invalid values (NaN/Inf)**
        if (!std::isfinite(servo_angle_deg)) {
            RCLCPP_WARN(node_->get_logger(), "Invalid motor angle detected for servo %s. Skipping update.", servo_name.c_str());
            return;
        }

        // **Sanity check for absurd values**
        constexpr double MAX_MOTOR_DEGREES = 360.0 * 1000;  // 1000 revolutions
        if (servo_angle_deg > MAX_MOTOR_DEGREES || servo_angle_deg < -MAX_MOTOR_DEGREES) {
            RCLCPP_WARN(node_->get_logger(), "Discarding out-of-range motor angle: %.2f degrees for motor ID %d", 
                        servo_angle_deg, motor_id);
            return;
        }

        // Step 2: Convert to 3D degree:
        // 3D_degree = 185 - servo_degree + 3D_close
        double servo_state_deg = (REAL_SERVO_CLOSE - servo_angle_deg) + servo.position_min;

        // **Apply inversion_feedback BEFORE zero position offset**
        if (servo.inverted_feedback) {
            servo_state_deg = -servo_state_deg;
        }

        RCLCPP_DEBUG(node_->get_logger(), "Final computed servo angle: %.3f degrees", servo_state_deg);

        // **Print servo Limits for Debugging**
        RCLCPP_DEBUG(node_->get_logger(), "servo %s: Min = %.3f, Max = %.3f, Current = %.3f", 
                    servo_name.c_str(), servo.position_min, servo.position_max, servo.position);


        // **Check if servo limits are valid**
        constexpr double TOLERANCE = 0.1;
        if (servo_state_deg < (servo.position_min - TOLERANCE) || servo_state_deg > (servo.position_max + TOLERANCE)) {
            RCLCPP_WARN(node_->get_logger(), "Ignoring out-of-bounds encoder value %.3f degrees for servo %s (limits: %.3f to %.3f)", 
                        servo_state_deg, servo_name.c_str(), servo.position_min, servo.position_max);
            return;
        }

        servo.position = servo_state_deg;

        // **Update servo State**
        servo.load = jsonObject["load"].get<double>();

        // **Apply Deadband Filtering (to remove tiny errors)**
        constexpr double POSITION_DEADBAND = 0.0001;
        if (std::abs(servo.position) < POSITION_DEADBAND) {
            servo.position = 0.0;
        }
        RCLCPP_INFO(node_->get_logger(), "Updated motor %d (%s) position: %.2f degrees", 
                    servo.motor_id, servo.inverted_feedback ? "inverted feedback" : "normal", servo.position);

        servo.last_update = node_->get_clock()->now();
    } catch (const std::exception& e) {
        RCLCPP_ERROR(node_->get_logger(), "Error processing encoder response: %s", e.what());
    }
}

/**
 * @brief Checks if the encoder data has changed.
 * @param encoder_data The current encoder data. expect a 6-byte vector
 * @return True if the encoder data has changed, false otherwise.
 */
bool ServoDriver::isServoDataChanged(double encoder_data) const {
    // Compare first bytes
    return encoder_data != pre_encoder_data_;
}

/**
 * @brief Sets the limits for a specific servo.
 * 
 * This function sets the position, velocity, and acceleration limits for a specific servo.
 * If the servo is not found, an error message is logged and the function returns.
 * 
 * @param servo_name The name of the servo.
 * @param pos_min The minimum position limit for the servo.
 * @param pos_max The maximum position limit for the servo.
 * @param vel_max The maximum velocity limit for the servo.
 * @param acc_max The maximum acceleration limit for the servo.
 */
void ServoDriver::setServoLimits(const std::string& servo_name, 
                                double pos_min, double pos_max) {
    auto it = servos_.find(servo_name);
    if (it == servos_.end()) {
        RCLCPP_ERROR(node_->get_logger(), "servo %s not found", servo_name.c_str());
        return;
    }

    // Validate limits
    if (pos_min > pos_max) {
        RCLCPP_ERROR(node_->get_logger(), 
                    "Invalid position limits for servo %s: min (%.2f) > max (%.2f)",
                    servo_name.c_str(), pos_min, pos_max);
        return;
    }

    // Update servo limits
    it->second.position_min = pos_min;
    it->second.position_max = pos_max;

    RCLCPP_INFO(node_->get_logger(), 
                "Updated limits for servo %s: pos=[%.2f, %.2f]",
                servo_name.c_str(), pos_min, pos_max);
}

/**
 * @brief Get the servo load for a specific servo.
 * 
 * This function retrieves the load for a given servo name. Load is useful to know if the gripper movevement is stopped due to object.
 * If the servo is not found, an error message is logged and 0.0 is returned.
 * 
 * @param servo_name The name of the servo.
 * @return The load of the servo.
 */
double ServoDriver::getServoLoad(const std::string& servo_name) const {
    auto it = servos_.find(servo_name);
    if (it == servos_.end()) {
        RCLCPP_ERROR(node_->get_logger(), "servo %s not found", servo_name.c_str());
        return 0.0;
    }
    return it->second.load;
}

/**
 * @brief Get the time elapsed since the last update for a specific servo.
 * 
 * This function returns the duration between the current time and the last update time
 * for the specified servo. If the servo is not found, an error message is logged and
 * a zero duration is returned.
 * 
 * @param servo_name The name of the servo.
 * @return The duration between the current time and the last update time for the servo.
 */
rclcpp::Duration ServoDriver::getTimeSinceLastUpdate(const std::string& servo_name) const {
    auto it = servos_.find(servo_name);
    if (it == servos_.end()) {
        RCLCPP_ERROR(node_->get_logger(), "servo %s not found", servo_name.c_str());
        return rclcpp::Duration(0, 0);
    }
    
    // Use the same clock source
    auto clock = node_->get_clock();
    return clock->now() - it->second.last_update;
}

/**
 * Retrieves the last error message for a specific servo.
 *
 * @param servo_name The name of the servo.
 * @return The last error message for the specified servo. If the servo is not found, "servo not found" is returned.
 */
std::string ServoDriver::getLastError(const std::string& servo_name) const {
    auto it = servos_.find(servo_name);
    if (it == servos_.end()) {
        return "servo not found";
    }
    return it->second.status.error_message;
}

} // namespace arctos_motor_driver