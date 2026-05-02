#include "arctos_hardware_interface/arctos_interface.hpp"
// #include "arctos_hardware_interface/arctos_services.hpp"
#include <pluginlib/class_list_macros.hpp>
#include <string>
#include <vector>
#include <chrono>

// ANSI color codes for terminal output
#define RESET "\033[0m"
#define RED "\033[31m"
#define BOLD_RED "\033[1;31m"

using arctos_motor_driver::MotorMode;
using hardware_interface::CallbackReturn;
using hardware_interface::return_type;

namespace arctos_interface
{

    ArctosInterface::ArctosInterface()
        : SystemInterface(),
          node_(std::make_shared<rclcpp::Node>("arctos_hardware_interface"))
    {
        uart_protocol_ = std::make_shared<arctos_motor_driver::UartProtocol>();
        motor_driver_ = std::make_shared<arctos_motor_driver::MotorDriver>(node_);
        motor_driver_->setProtocol(uart_protocol_);
    }

    ArctosInterface::~ArctosInterface() = default;

    /* Here, you should initialize all member variables and process the parameters from the info argument, and memory dynamic should be allocated */
    /* HardwareInfo info could be collected under <ros2_control> tag, and the joints are <joint>. We then seek each joint params via arctos_hardware_interface/ros__parameters */
    CallbackReturn ArctosInterface::on_init(const hardware_interface::HardwareInfo &info)
    {
        if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS)
        {
            return CallbackReturn::ERROR;
        }

        // Initialize state storage vectors
        joint_position_.resize(info_.joints.size(), 0.0);
        joint_velocities_.resize(info_.joints.size(), 0.0);
        joint_position_command_.resize(info_.joints.size(), 0.0);
        joint_velocities_command_.resize(info_.joints.size(), 0.0);
        motor_ids_.resize(info_.joints.size());

        // Force/torque sensor has 6 readings
        ft_states_.assign(6, 0);
        ft_command_.assign(6, 0);

        // Clear previous interface mappings
        joint_interfaces["position"].clear();
        joint_interfaces["velocity"].clear();

        // Collect joint names for service initialization
        std::vector<std::string> joint_names;
        joint_names.reserve(info_.joints.size());

        // Process joints and their interfaces
        for (size_t i = 0; i < info_.joints.size(); i++)
        {
            const auto &joint = info_.joints[i];
            joint_names.push_back(joint.name);

            // Create parameter name for this joint's settings
            std::string param_prefix = "motors." + joint.name + ".";

            // Declare parameters for this joint
            node_->declare_parameter(param_prefix + "motor_id", -1);
            node_->declare_parameter(param_prefix + "hardware_type", "MKS_42D");
            node_->declare_parameter(param_prefix + "gear_ratio", 1.0);
            node_->declare_parameter(param_prefix + "inverted", false);
            node_->declare_parameter(param_prefix + "inverted_feedback", false);
            node_->declare_parameter(param_prefix + "requires_homing", false);
            node_->declare_parameter(param_prefix + "lower_limit", 0.0);
            node_->declare_parameter(param_prefix + "upper_limit", 0.0);

            // Get motor ID from parameters
            int motor_id;
            if (!node_->get_parameter(param_prefix + "motor_id", motor_id))
            {
                RCLCPP_ERROR(node_->get_logger(), "Failed to get motor_id for joint %s", joint.name.c_str());
                return CallbackReturn::ERROR;
            }

            if (motor_id < 0)
            {
                RCLCPP_ERROR(node_->get_logger(), "Invalid motor_id (%d) for joint %s", motor_id, joint.name.c_str());
                return CallbackReturn::ERROR;
            }

            motor_ids_[i] = static_cast<uint8_t>(motor_id);

            RCLCPP_INFO(node_->get_logger(), "Configured joint %s with motor_id %d",
                        joint.name.c_str(), motor_id);

            // Track available interfaces
            for (const auto &interface : joint.state_interfaces)
            {
                joint_interfaces[interface.name].push_back(joint.name);
                if (interface.name == "position")
                    has_position_interface_ = true;
                if (interface.name == "velocity")
                    has_velocity_interface_ = true;
            }
        }

        node_->declare_parameter("position_tolerance", 0.001);
        node_->declare_parameter("velocity_tolerance", 0.01);

        // Get parameter values
        node_->get_parameter("position_tolerance", position_tolerance_);
        node_->get_parameter("velocity_tolerance", velocity_tolerance_);

        return CallbackReturn::SUCCESS;
    }

    /* setup the communication to the hardware and set everything up so that the hardware can be activated */
    CallbackReturn ArctosInterface::on_configure(const rclcpp_lifecycle::State &previous_state)
    {
        RCLCPP_INFO(node_->get_logger(), "Transitioning to CONFIGURE state from %s", previous_state.label().c_str());

        try
        {
            initializeMotors();
        }
        catch (const std::exception &e)
        {
            RCLCPP_ERROR(node_->get_logger(), "Failed to initialize motors: %s", e.what());
            return CallbackReturn::ERROR;
        }

        // Initialize UART connection
        try
        {
            // Get params from Ros2_control/hardware/param in urdf
            std::string device = info_.hardware_parameters["device"];
            int baud_rate = std::stoi(info_.hardware_parameters["baud_rate"]);
            int timeout = std::stoi(info_.hardware_parameters["timeout"]);
            // then setup uart connection
            uart_protocol_->setup(device, baud_rate, timeout);
        }
        catch (const std::exception &e)
        {
            RCLCPP_ERROR(node_->get_logger(), BOLD_RED "FATAL: Failed to initialize UART connection, assuming using simulation: %s" RESET, e.what());
        }

        return CallbackReturn::SUCCESS;
    }

    /* Reset the robot position to 0 and start the UART reception thread */
    CallbackReturn ArctosInterface::on_activate(const rclcpp_lifecycle::State &previous_state)
    {
        RCLCPP_INFO(node_->get_logger(), "Transitioning to ACTIVE state from %s", previous_state.label().c_str());

        // Enable all motors (if required)

        for (size_t i = 0; i < info_.joints.size(); i++)
        {
            // force home on first activation
            joint_position_command_[i] = 0.0;
        }

        // thread spin is required for continously reading UART strings,
        allowSpin.store(true);
        spinThread = std::thread(
            [&]()
            {
                while (allowSpin.load())
                {
                    uart_protocol_->readToBuffer(false);
                    std::this_thread::sleep_for(std::chrono::milliseconds(5));
                }
            });

        return CallbackReturn::SUCCESS;
    }

    CallbackReturn ArctosInterface::on_deactivate(const rclcpp_lifecycle::State &previous_state)
    {
        RCLCPP_INFO(node_->get_logger(), "Transitioning to INACTIVE state from %s", previous_state.label().c_str());
        // Disable the motors (if required)
        allowSpin.store(false);
        spinThread.join();
        return CallbackReturn::SUCCESS;
    }

    std::vector<hardware_interface::StateInterface> ArctosInterface::export_state_interfaces()
    {
        std::vector<hardware_interface::StateInterface> state_interfaces;

        // Add joint state interfaces
        /*The StateInterface objects are read only data handles.
        Their constructors require an (interface name, interface type, and a pointer to a double data value)*/
        for (size_t i = 0; i < info_.joints.size(); i++)
        {
            if (has_position_interface_)
            {
                state_interfaces.emplace_back(
                    info_.joints[i].name, hardware_interface::HW_IF_POSITION, &joint_position_[i]);
            }
            if (has_velocity_interface_)
            {
                state_interfaces.emplace_back(
                    info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &joint_velocities_[i]);
            }
        }

        return state_interfaces;
    }

    std::vector<hardware_interface::CommandInterface> ArctosInterface::export_command_interfaces()
    {
        std::vector<hardware_interface::CommandInterface> command_interfaces;

        // Add joint command interfaces
        for (size_t i = 0; i < info_.joints.size(); i++)
        {
            if (has_position_interface_)
            {
                command_interfaces.emplace_back(
                    info_.joints[i].name, hardware_interface::HW_IF_POSITION, &joint_position_command_[i]);
            }
            if (has_velocity_interface_)
            {
                command_interfaces.emplace_back(
                    info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &joint_velocities_command_[i]);
            }
        }

        return command_interfaces;
    }

    /* core method in ros2_control loop
    During the main loop, ros2_control loops over all hardware components and calls the read method.
    -> responsible for updating the data values of the *state_interfaces*, by updating the *class member variable*
    */
    return_type ArctosInterface::read(const rclcpp::Time &time, const rclcpp::Duration & /*period*/)
    {
        // Process UART messages
        motor_driver_->processUartMessage();
        static rclcpp::Time last_update_time = time;
        auto elapsed_time = time - last_update_time;
        for (size_t i = 0; i < info_.joints.size(); i++)
        {
            const std::string &joint_name = info_.joints[i].name;
            try
            {
                RCLCPP_DEBUG(node_->get_logger(), "Reading state for joint %s", joint_name.c_str());

                if (has_position_interface_)
                {
                    double pos = motor_driver_->getJointPosition(joint_name, true);
                    joint_position_[i] = pos;
                    RCLCPP_DEBUG(node_->get_logger(), "Updated position for joint %s: %.3f", joint_name.c_str(), pos);
                }

                if (has_velocity_interface_)
                {
                    // double vel = motor_driver_->getJointVelocity(joint_name);
                    // joint_velocities_[i] = vel;
                    // RCLCPP_DEBUG(node_->get_logger(), "Updated velocity for joint %s: %.3f rad/s", joint_name.c_str(), vel);
                }

                rclcpp::Duration time_since_update = motor_driver_->getTimeSinceLastUpdate(joint_name);
                if (time_since_update.seconds() > 1.0)
                {
                    // RCLCPP_WARN(node_->get_logger(),"Stale data for joint %s: %.3f seconds since last update",joint_name.c_str(), time_since_update.seconds());
                }
            }
            catch (const std::exception &e)
            {
                RCLCPP_ERROR(node_->get_logger(), "Failed to read state from joint %s: %s",
                             joint_name.c_str(), e.what());
                return return_type::ERROR;
            }
        }

        return return_type::OK;
    }

    /* The *write* method is another core method in the ros2_control loop.
    It is called after *update* in the realtime loop.
    responsible for updating the data values of the *command_interfaces*
    */
    return_type ArctosInterface::write(const rclcpp::Time & /*time*/, const rclcpp::Duration & period)
    {
        // Reset trend after 5 cycles of no change
        static const int TREND_RESET_THRESHOLD = 5;
        // Number of consecutive increases/decreases to confirm trend
        static const int TREND_THRESHOLD = 2;
        // Delta increase in joint position to fill up the "empty slot"
        // static const float DELTA_COMMAND_INCREASE = 0.01;

        static bool isPositionUpdated;
        isPositionUpdated = false;
        static int FLUSH_DURATION = 10000000; // Flush every 10 seconds
        static int loop_count = static_cast<int>(FLUSH_DURATION / period.nanoseconds());
        // TREND_THRESHOLD for increasing, -TREND_THRESHOLD for decreasing, 0 for unknown
        static std::vector<int> trend(info_.joints.size(), 0);
        // whether to allow position command to be sent, only set to true when trend changes or command changes significantly
        static std::vector<bool> allowPosition(info_.joints.size(), false);
        // Track idle time for trend reset
        static std::vector<int> idle_counter(info_.joints.size(), 0);
        // Calculate delta to trend of each joint
        static std::vector<float> delta_movement(info_.joints.size(), 0.0);

        // Resize last command vectors if not already done
        if (last_position_command_.size() != info_.joints.size())
        {
            // force homing on first activation
            last_position_command_.resize(info_.joints.size(), -1.0);
            last_valid_position_command_.resize(info_.joints.size(), 0.0);
            last_velocity_command_.resize(info_.joints.size(), 0.0);
            RCLCPP_INFO(node_->get_logger(), "Initialized last command vectors.");
        }

        if (loop_count > 0)
        {
            loop_count--;
        }
        else
        {
            uart_protocol_->flush();
            loop_count = static_cast<int>(FLUSH_DURATION / period.nanoseconds());
        }

        for (size_t i = 0; i < info_.joints.size(); i++)
        {
            try
            {
                if (has_velocity_interface_)
                {
                    // Only send if velocity has changed significantly
                    if (std::abs(joint_velocities_command_[i] - last_velocity_command_[i]) > velocity_tolerance_)
                    {
                        RCLCPP_DEBUG(node_->get_logger(),
                                     "Sent velocity command %.3f rad/s to joint %s. Last command: %.3f",
                                     joint_velocities_command_[i], info_.joints[i].name.c_str(),
                                     last_velocity_command_[i]);
                        last_velocity_command_[i] = joint_velocities_command_[i];
                    }
                    else
                    {
                        RCLCPP_DEBUG(node_->get_logger(),
                                     "Velocity command for joint %s unchanged: %.3f",
                                     info_.joints[i].name.c_str(), joint_velocities_command_[i]);
                    }
                }

                if (has_position_interface_)
                {
                    // reset allowPosition for each joint, only set to true when trend changes or command changes significantly
                    allowPosition[i] = false;
                    // Only send if position has changed significantly
                    if (std::abs(joint_position_command_[i] - last_position_command_[i]) > position_tolerance_)
                    {
                        // Trend learning and reversal prevention logic
                        double position_delta = joint_position_command_[i] - last_valid_position_command_[i];
                        bool is_increasing = position_delta > 0;
                        bool is_decreasing = position_delta < 0;

                        if (trend[i] >= TREND_THRESHOLD && is_increasing)
                        {
                            RCLCPP_INFO(node_->get_logger(), "Continuing increasing trend %s", info_.joints[i].name.c_str());
                            allowPosition[i] = true;
                            delta_movement[i] = std::abs(position_delta * 0.8);
                        }
                        else if (trend[i] <= -TREND_THRESHOLD && is_decreasing)
                        {
                            RCLCPP_INFO(node_->get_logger(), "Continuing decreasing trend %s", info_.joints[i].name.c_str());
                            allowPosition[i] = true;
                            delta_movement[i] = std::abs(position_delta * 0.8);
                        }
                        else if (trend[i] >= TREND_THRESHOLD && is_decreasing)
                        {
                            RCLCPP_WARN(node_->get_logger(), "Blocking trend reversal (inc->dec) %s, cur: %.5f - last %.5f", info_.joints[i].name.c_str(), joint_position_command_[i], last_valid_position_command_[i]);
                            // allowPosition[i] remains false - block the command, send last valid position instead
                        }
                        else if (trend[i] <= -TREND_THRESHOLD && is_increasing)
                        {
                            RCLCPP_WARN(node_->get_logger(), "Blocking trend reversal (dec->inc) %s, cur: %.5f - last %.5f", info_.joints[i].name.c_str(), joint_position_command_[i], last_valid_position_command_[i]);
                            // allowPosition[i] remains false - block the command, send last valid position instead
                        }
                        else if (trend[i] > -TREND_THRESHOLD && trend[i] < TREND_THRESHOLD)
                        {
                            // trend learning phase
                            if (is_increasing)
                            {
                                trend[i]++;
                                RCLCPP_INFO(node_->get_logger(), "Learning increasing trend %s (trend: %d)", info_.joints[i].name.c_str(), trend[i]);
                                allowPosition[i] = true;
                            }
                            else if (is_decreasing)
                            {
                                trend[i]--;
                                RCLCPP_INFO(node_->get_logger(), "Learning decreasing trend %s (trend: %d)", info_.joints[i].name.c_str(), trend[i]);
                                allowPosition[i] = true;
                            }
                            
                        }

                        // Decide whether to send the position command based on trend analysis
                        if (allowPosition[i])
                        {
                            motor_driver_->setJointPosition(info_.joints[i].name, joint_position_command_[i], 0, abs(joint_velocities_command_[i] * 10) * 60);
                            RCLCPP_INFO(node_->get_logger(),
                                        "Sent position command %.5f rad to joint %s. Last command: %.5f.",
                                        joint_position_command_[i], info_.joints[i].name.c_str(),
                                        last_position_command_[i]);
                            // Remember last valid position command for trend analysis and potential padding
                            last_valid_position_command_[i] = joint_position_command_[i];
                        }
                        // send last valid position command again to prevent "empty slot" that might cause the robot to flicker
                        else
                        {
                            std::string trend_text = "INCREASE";
                            if (trend[i] >= TREND_THRESHOLD) 
                            {
                                // increasing trend, so increase the padding
                                last_valid_position_command_[i] += delta_movement[i];
                            }
                            else if (trend[i] <= -TREND_THRESHOLD) 
                            {
                                // decreasing trend, so decrease the padding
                                last_valid_position_command_[i] -= delta_movement[i];
                                trend_text = "DECREASE";
                            }
                            
                            motor_driver_->setJointPosition(info_.joints[i].name, last_valid_position_command_[i], 0, abs(joint_velocities_command_[i] * 10) * 60);
                            RCLCPP_INFO(node_->get_logger(),
                                        "Sent [padding <%.5f>] for trend [%s], position command %.5f rad to joint %s. Last command: %.5f.",
                                        delta_movement[i], trend_text.c_str(), last_valid_position_command_[i], info_.joints[i].name.c_str(),
                                        last_position_command_[i]);
                        }
                        isPositionUpdated = true;
                        // last_position_command is updated to avoid stucking, where current joint_position_command_[i] always != last_position_command_[i]
                        last_position_command_[i] = joint_position_command_[i];
                        // Reset idle counter on successful command
                        idle_counter[i] = 0;
                    }
                    else
                    {
                        // Increment idle counter and reset trend if idle too long
                        idle_counter[i]++;
                        RCLCPP_DEBUG(node_->get_logger(),
                                     "Position command for joint %s unchanged: %.3f",
                                     info_.joints[i].name.c_str(), joint_position_command_[i]);
                        if (idle_counter[i] >= TREND_RESET_THRESHOLD)
                        {
                            RCLCPP_INFO(node_->get_logger(), "Resetting trend for joint %s after %d idle cycles",
                                        info_.joints[i].name.c_str(), idle_counter[i]);
                            trend[i] = 0;
                            delta_movement[i] = 0.0;
                        }
                    }
                }
            }
            catch (const std::exception &e)
            {
                RCLCPP_ERROR(node_->get_logger(),
                             "Failed to write command to joint %s: %s",
                             info_.joints[i].name.c_str(), e.what());
                return return_type::ERROR;
            }
        }

        // Write command to the actuator.
        if (isPositionUpdated)
        {
            motor_driver_->writeCommand();
        }

        return return_type::OK;
    }

    void ArctosInterface::initializeMotors()
    {
        for (size_t i = 0; i < info_.joints.size(); i++)
        {
            const auto &joint = info_.joints[i];
            uint8_t motor_id = motor_ids_[i];

            std::string param_prefix = "motors." + joint.name + ".";

            // Get hardware_type parameter
            std::string hardware_type;
            if (!node_->get_parameter(param_prefix + "hardware_type", hardware_type))
            {
                RCLCPP_WARN(node_->get_logger(), "No hardware type specified for joint %s, using default MKS_42D",
                            joint.name.c_str());
                hardware_type = "MKS_42D";
            }

            double gear_ratio;
            if (!node_->get_parameter(param_prefix + "gear_ratio", gear_ratio))
            {
                RCLCPP_WARN(node_->get_logger(), "No gear ratio specified for joint %s, using 1:1",
                            joint.name.c_str());
                gear_ratio = 1.0;
            }

            bool inverted;
            if (!node_->get_parameter(param_prefix + "inverted", inverted))
            {
                RCLCPP_WARN(node_->get_logger(), "No inverted specified for joint %s, using false",
                            joint.name.c_str());
                inverted = false;
            }

            bool inverted_feedback;
            if (!node_->get_parameter(param_prefix + "inverted_feedback", inverted_feedback))
            {
                RCLCPP_WARN(node_->get_logger(), "No inverted_feedback specified for joint %s, using false",
                            joint.name.c_str());
                inverted_feedback = false;
            }

            // Add joint to motor driver with gear ratio
            motor_driver_->addJoint(joint.name, motor_id, hardware_type, gear_ratio, inverted, inverted_feedback);

            // Configure motor parameters
            if (!setupMotorParameters(joint, motor_id))
            {
                throw std::runtime_error("Failed to configure motor for joint " + joint.name);
            }

            RCLCPP_INFO(node_->get_logger(), "Initialized motor for joint %s with ID %d and gear ratio %.2f:1",
                        joint.name.c_str(), motor_id, gear_ratio);
        }
    }

    bool ArctosInterface::setupMotorParameters(
        const hardware_interface::ComponentInfo &joint_info, uint8_t motor_id)
    {
        try
        {
            double gear_ratio;
            double lower_limit;
            double upper_limit;
            double max_rpm = 3000.0;
            std::string param_prefix = "motors." + joint_info.name + ".";

            // Get gear ratio from parameters
            if (!node_->get_parameter(param_prefix + "gear_ratio", gear_ratio))
            {
                RCLCPP_WARN(node_->get_logger(), "No gear ratio specified for joint %s, using 1:1",
                            joint_info.name.c_str());
                gear_ratio = 1.0;
            }

            // Get home position from parameters

            node_->get_parameter(param_prefix + "lower_limit", lower_limit);
            node_->get_parameter(param_prefix + "upper_limit", upper_limit);

            // Calculate maximum velocity based on gear ratio
            double max_velocity = (max_rpm * M_PI / 30.0) / gear_ratio;

            // Set joint limits using home position and opposite limit
            motor_driver_->setJointLimits(joint_info.name, lower_limit, upper_limit, max_velocity, 255.0);

            RCLCPP_INFO(node_->get_logger(), "Set joint limits for joint %s of motor %d: pos=[%.2f, %.2f], vel=%.2f, acc=%.2f",
                        joint_info.name.c_str(), motor_id, lower_limit, upper_limit, max_velocity, 255.0);

            return true;
        }
        catch (const std::exception &e)
        {
            RCLCPP_ERROR(node_->get_logger(), "Failed to setup motor parameters for joint %s: %s",
                         joint_info.name.c_str(), e.what());
            return false;
        }
    }

} // namespace arctos_interface

PLUGINLIB_EXPORT_CLASS(
    arctos_interface::ArctosInterface,
    hardware_interface::SystemInterface)