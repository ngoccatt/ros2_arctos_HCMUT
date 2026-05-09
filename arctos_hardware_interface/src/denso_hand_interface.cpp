#include "arctos_hardware_interface/denso_hand_interface.hpp"
#include <pluginlib/class_list_macros.hpp>
#include <string>
#include <vector>
#include <chrono>

// ANSI color codes for terminal output
#define RESET "\033[0m"
#define RED "\033[31m"
#define BOLD_RED "\033[1;31m"

using hardware_interface::CallbackReturn;
using hardware_interface::return_type;

namespace denso_hand_interface
{

    DensoHandInterface::DensoHandInterface()
        : SystemInterface(),
          node_(std::make_shared<rclcpp::Node>("denso_hand_interface"))
    {
        uart_protocol_ = std::make_shared<arctos_motor_driver::UartProtocol>();
        servo_driver_ = std::make_shared<arctos_motor_driver::ServoDriver>(node_);
        servo_driver_->setProtocol(uart_protocol_);
    }

    DensoHandInterface::~DensoHandInterface() = default;

    /* Here, you should initialize all member variables and process the parameters from the info argument, and memory dynamic should be allocated */
    /* HardwareInfo info could be collected under <ros2_control> tag, and the joints are <joint>. We then seek each joint params via arctos_hardware_interface/ros__parameters */
    CallbackReturn DensoHandInterface::on_init(const hardware_interface::HardwareInfo &info)
    {
        if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS)
        {
            return CallbackReturn::ERROR;
        }

        // Initialize state storage vectors
        servo_position_.resize(info_.joints.size(), 0.0);
        servo_velocity_.resize(info_.joints.size(), 0.0);
        servo_position_command_.resize(info_.joints.size(), 0.1);
        motor_ids_.resize(info_.joints.size());

        // Clear previous interface mappings
        servo_interfaces["position"].clear();
        servo_interfaces["velocity"].clear();

        // Collect joint names for service initialization
        std::vector<std::string> joint_names;
        joint_names.reserve(info_.joints.size());

        // Process joints and their interfaces
        for (size_t i = 0; i < info_.joints.size(); i++)
        {
            const auto &joint = info_.joints[i];
            joint_names.push_back(joint.name);

            // Create parameter name for this joint's settings
            std::string param_prefix = "gripper." + joint.name + ".";

            // Declare parameters for this joint
            node_->declare_parameter(param_prefix + "motor_id", -1);             // Motor/CAN ID
            node_->declare_parameter(param_prefix + "hardware_type", "MKS_42D"); // Default MKS Servo
            node_->declare_parameter(param_prefix + "gear_ratio", 1.0);          // Default 1:1 gear ratio
            node_->declare_parameter(param_prefix + "inverted", false);          // Default no inverted in application side
            node_->declare_parameter(param_prefix + "inverted_feedback", false); // Default no inverted in physical side
            node_->declare_parameter(param_prefix + "requires_homing", false);   // Default no homing needed
            node_->declare_parameter(param_prefix + "lower_limit", 0.0);
            node_->declare_parameter(param_prefix + "upper_limit", 0.0);
            node_->declare_parameter(param_prefix + "velocity", 0.0);
            node_->declare_parameter(param_prefix + "acceleration", 0.0);

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

            if (!node_->get_parameter(param_prefix + "velocity", velocity_))
            {
                RCLCPP_ERROR(node_->get_logger(), "Failed to get velocity for joint %s", joint.name.c_str());
                return CallbackReturn::ERROR;
            }

            if (!node_->get_parameter(param_prefix + "acceleration", acceleration_))
            {
                RCLCPP_ERROR(node_->get_logger(), "Failed to get acceleration for joint %s", joint.name.c_str());
                return CallbackReturn::ERROR;
            }

            // Track available interfaces
            for (const auto &interface : joint.state_interfaces)
            {
                servo_interfaces[interface.name].push_back(joint.name);
                if (interface.name == "position")
                    has_position_interface_ = true;
                if (interface.name == "velocity")
                    has_velocity_interface_ = true;
            }
            // has_velocity_interface_ = false; // Force disable velocity interface as we are not using it for now
        }

        return CallbackReturn::SUCCESS;
    }

    /* setup the communication to the hardware and set everything up so that the hardware can be activated */
    CallbackReturn DensoHandInterface::on_configure(const rclcpp_lifecycle::State &previous_state)
    {
        RCLCPP_INFO(node_->get_logger(), "Transitioning to CONFIGURE state from %s", previous_state.label().c_str());

        try
        {
            initializeServos();
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
    CallbackReturn DensoHandInterface::on_activate(const rclcpp_lifecycle::State &previous_state)
    {
        RCLCPP_INFO(node_->get_logger(), "Transitioning to ACTIVE state from %s", previous_state.label().c_str());

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

    CallbackReturn DensoHandInterface::on_deactivate(const rclcpp_lifecycle::State &previous_state)
    {
        RCLCPP_INFO(node_->get_logger(), "Transitioning to INACTIVE state from %s", previous_state.label().c_str());
        // join the threads
        allowSpin.store(false);
        spinThread.join();
        return CallbackReturn::SUCCESS;
    }

    // Add joint state interfaces
    /*The StateInterface objects are read only data handles.
    // has to create velocity state interface, since ros2_control definition for the gripper joint have both position and velocity.
    Their constructors require an (interface name, interface type, and a pointer to a double data value)*/
    std::vector<hardware_interface::StateInterface> DensoHandInterface::export_state_interfaces()
    {
        std::vector<hardware_interface::StateInterface> state_interfaces;
        for (size_t i = 0; i < info_.joints.size(); i++)
        {
            if (has_position_interface_)
            {
                state_interfaces.emplace_back(
                    info_.joints[i].name, hardware_interface::HW_IF_POSITION, &servo_position_[i]);
            }

            if (has_velocity_interface_)
            {
                state_interfaces.emplace_back(
                    info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &servo_velocity_[i]);
            }
        }

        return state_interfaces;
    }

    std::vector<hardware_interface::CommandInterface> DensoHandInterface::export_command_interfaces()
    {
        std::vector<hardware_interface::CommandInterface> command_interfaces;

        // Add joint command interfaces
        for (size_t i = 0; i < info_.joints.size(); i++)
        {
            if (has_position_interface_)
            {
                command_interfaces.emplace_back(
                    info_.joints[i].name, hardware_interface::HW_IF_POSITION, &servo_position_command_[i]);
            }
        }

        return command_interfaces;
    }

    /* core method in ros2_control loop
    During the main loop, ros2_control loops over all hardware components and calls the read method.
    -> responsible for updating the data values of the *state_interfaces*, by updating the *class member variable*
    */
    return_type DensoHandInterface::read(const rclcpp::Time &time, const rclcpp::Duration &period)
    {
        (void)time;

        servo_driver_->writeQueryCommand();
        // Process UART messages
        servo_driver_->processUartMessage();

        for (size_t i = 0; i < info_.joints.size(); i++)
        {
            const std::string &joint_name = info_.joints[i].name;
            try
            {
                RCLCPP_DEBUG(node_->get_logger(), "Reading state for joint %s", joint_name.c_str());

                if (has_position_interface_)
                {
                    double old_pos = servo_position_[i];
                    double pos = servo_driver_->getServoPosition(joint_name, true);
                    double dt = period.seconds();
                    if (has_velocity_interface_)
                    {
                        servo_velocity_[i] = (dt > 1e-6) ? (pos - old_pos) / dt : 0.0;
                    }
                    servo_position_[i] = pos;
                    RCLCPP_DEBUG(node_->get_logger(), "Updated position for joint %s: %.3f vel: %.4f", joint_name.c_str(), pos, servo_velocity_[i]);
                }

                rclcpp::Duration time_since_update = servo_driver_->getTimeSinceLastUpdate(joint_name);
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
    return_type DensoHandInterface::write(const rclcpp::Time & /*time*/, const rclcpp::Duration & period)
    {
        static bool isPositionUpdated;
        isPositionUpdated = false;
        // Resize last command vectors if not already done
        if (last_position_command_.size() != info_.joints.size())
        {
            // force homing on first activation
            last_position_command_.resize(info_.joints.size(), -1.0); 
            RCLCPP_INFO(node_->get_logger(), "Initialized last command vectors.");
        }

        for (size_t i = 0; i < info_.joints.size(); i++)
        {
            try
            {
                if (has_position_interface_)
                {
                    if (std::abs(servo_position_command_[i] - last_position_command_[i]) > position_tolerance_)
                    {
                        servo_driver_->setServoPosition(info_.joints[i].name, servo_position_command_[i], acceleration_, velocity_);
                        RCLCPP_INFO(node_->get_logger(),
                                    "Set position command %.5f rad to joint %s. Last command: %.5f.",
                                    servo_position_command_[i], info_.joints[i].name.c_str(),
                                    last_position_command_[i]);
                        // last valid position command is saved here.
                        last_position_command_[i] = servo_position_command_[i];
                            
                        isPositionUpdated = true;
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
            servo_driver_->writeCommand();
        }

        return return_type::OK;
    }

    void DensoHandInterface::initializeServos()
    {
        for (size_t i = 0; i < info_.joints.size(); i++)
        {
            const auto &joint = info_.joints[i];
            uint8_t motor_id = motor_ids_[i];

            std::string param_prefix = "gripper." + joint.name + ".";

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
            servo_driver_->addServo(joint.name, motor_id, hardware_type, gear_ratio, inverted, inverted_feedback);

            // Configure motor parameters
            if (!setupServoParameters(joint, motor_id))
            {
                throw std::runtime_error("Failed to configure motor for joint " + joint.name);
            }

            RCLCPP_INFO(node_->get_logger(), "Initialized motor for joint %s with ID %d and gear ratio %.2f:1",
                        joint.name.c_str(), motor_id, gear_ratio);
        }
    }

    bool DensoHandInterface::setupServoParameters(
        const hardware_interface::ComponentInfo &joint_info, uint8_t motor_id)
    {
        try
        {
            // Default parameters
            double gear_ratio = 1.0;
            double lower_limit = 0.0;
            double upper_limit = 0.0;

            std::string param_prefix = "gripper." + joint_info.name + ".";

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

            // Set joint limits using home position and opposite limit
            servo_driver_->setServoLimits(joint_info.name, lower_limit, upper_limit);

            RCLCPP_INFO(node_->get_logger(), "Set joint limits for joint %s of motor %d: pos=[%.2f, %.2f]",
                        joint_info.name.c_str(), motor_id, lower_limit, upper_limit);

            return true;
        }
        catch (const std::exception &e)
        {
            RCLCPP_ERROR(node_->get_logger(), "Failed to setup motor parameters for joint %s: %s",
                         joint_info.name.c_str(), e.what());
            return false;
        }
    }

} // namespace denso_hand_interface

PLUGINLIB_EXPORT_CLASS(
    denso_hand_interface::DensoHandInterface,
    hardware_interface::SystemInterface)