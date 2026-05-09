
#include <rclcpp/rclcpp.hpp>
#include <rclcpp/executors.hpp>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <control_msgs/msg/joint_jog.hpp>
#include <std_srvs/srv/trigger.hpp>

#include <signal.h>
#include <stdio.h>
#include <termios.h>
#include <unistd.h>

// Define used keys
#define KEYCODE_RIGHT 0x43
#define KEYCODE_LEFT 0x44
#define KEYCODE_UP 0x41
#define KEYCODE_DOWN 0x42
#define KEYCODE_PERIOD 0x2E
#define KEYCODE_SEMICOLON 0x3B
#define KEYCODE_1 0x31
#define KEYCODE_2 0x32
#define KEYCODE_3 0x33
#define KEYCODE_4 0x34
#define KEYCODE_5 0x35
#define KEYCODE_6 0x36
#define KEYCODE_7 0x37
#define KEYCODE_Q 0x71
#define KEYCODE_W 0x77
#define KEYCODE_E 0x65
#define KEYCODE_R 0x72
#define KEYCODE_S 0x73
#define KEYCODE_SPACE 0x20

// run this with
// ros2 run denso_moveit_servo servo_keyboard_input --ros-args -p use_sim_time:=true

// Some constants used in the Servo Teleop demo
const std::string TWIST_TOPIC = "/denso_moveit_servo_node/delta_twist_cmds";
const std::string JOINT_TOPIC = "/denso_moveit_servo_node/delta_joint_cmds";
const size_t ROS_QUEUE_SIZE = 10;
const std::string EEF_FRAME_ID = "gripper_body_link";
const std::string BASE_FRAME_ID = "base_link";

// A class for reading the key inputs from the terminal
class KeyboardReader
{
public:
  KeyboardReader() : kfd(0)
  {
    // get the console in raw mode
    tcgetattr(kfd, &cooked);
    struct termios raw;
    memcpy(&raw, &cooked, sizeof(struct termios));
    raw.c_lflag &= ~(ICANON | ECHO);
    // Setting a new line, then end of file
    raw.c_cc[VEOL] = 1;
    raw.c_cc[VEOF] = 2;
    tcsetattr(kfd, TCSANOW, &raw);
  }
  void readOne(char* c)
  {
    int rc = read(kfd, c, 1);
    if (rc < 0)
    {
      throw std::runtime_error("read failed");
    }
  }
  void shutdown()
  {
    tcsetattr(kfd, TCSANOW, &cooked);
  }

private:
  int kfd;
  struct termios cooked;
};

// Publisher Node for handling twist and joint messages
class PublisherNode : public rclcpp::Node
{
public:
  PublisherNode() : Node("servo_publisher_node")
  {
    twist_pub_ = this->create_publisher<geometry_msgs::msg::TwistStamped>(TWIST_TOPIC, ROS_QUEUE_SIZE);
    joint_pub_ = this->create_publisher<control_msgs::msg::JointJog>(JOINT_TOPIC, ROS_QUEUE_SIZE);
  }
  
  void publishTwist(const geometry_msgs::msg::TwistStamped& msg)
  {
    twist_pub_->publish(msg);
  }
  
  void publishJoint(const control_msgs::msg::JointJog& msg)
  {
    joint_pub_->publish(msg);
  }

private:
  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr twist_pub_;
  rclcpp::Publisher<control_msgs::msg::JointJog>::SharedPtr joint_pub_;
};

// Service Node for handling servo start/stop services
class ServiceNode : public rclcpp::Node
{
public:
  ServiceNode() : Node("servo_service_node")
  {
    start_servo_client_ = this->create_client<std_srvs::srv::Trigger>("denso_moveit_servo_node/start_servo");
    stop_servo_client_ = this->create_client<std_srvs::srv::Trigger>("denso_moveit_servo_node/stop_servo");
    
    // Wait for services to be available
    while (!start_servo_client_->wait_for_service(std::chrono::seconds(1)) || 
           !stop_servo_client_->wait_for_service(std::chrono::seconds(1))) {
      if (!rclcpp::ok()) {
        RCLCPP_ERROR(this->get_logger(), "Interrupted while waiting for the service. Exiting.");
        return;
      }
      RCLCPP_INFO(this->get_logger(), "Service not available, waiting again...");
    }
  }
  
  bool startServo()
  {
    auto request = std::make_shared<std_srvs::srv::Trigger::Request>();
    auto result = start_servo_client_->async_send_request(request);
    
    if (rclcpp::spin_until_future_complete(shared_from_this(), result) == rclcpp::FutureReturnCode::SUCCESS) {
      RCLCPP_INFO(this->get_logger(), "Start servo success: %d", result.get()->success);
      return true;
    }
    RCLCPP_ERROR(this->get_logger(), "Failed to call start servo service");
    return false;
  }
  
  bool stopServo()
  {
    auto request = std::make_shared<std_srvs::srv::Trigger::Request>();
    auto result = stop_servo_client_->async_send_request(request);
    
    if (rclcpp::spin_until_future_complete(shared_from_this(), result) == rclcpp::FutureReturnCode::SUCCESS) {
      RCLCPP_INFO(this->get_logger(), "Stop servo success: %d", result.get()->success);
      return true;
    }
    RCLCPP_ERROR(this->get_logger(), "Failed to call stop servo service");
    return false;
  }

private:
  rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr start_servo_client_;
  rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr stop_servo_client_;
};

// Converts key-presses to Twist or Jog commands for Servo, in lieu of a controller
class KeyboardServo
{
public:
  KeyboardServo();
  int keyLoop();

private:
  void spin();

  std::shared_ptr<PublisherNode> pub_node_;
  std::shared_ptr<ServiceNode> service_node_;

  std::string frame_to_publish_;
  double joint_vel_cmd_;
  double axis_pos_cmd;
};

KeyboardServo::KeyboardServo() : frame_to_publish_(BASE_FRAME_ID), joint_vel_cmd_(0.8), axis_pos_cmd(1.0)
{
  pub_node_ = std::make_shared<PublisherNode>();
  service_node_ = std::make_shared<ServiceNode>();
}

KeyboardReader input;

void quit(int sig)
{
  (void)sig;
  input.shutdown();
  rclcpp::shutdown();
  exit(0);
}

void KeyboardServo::spin()
{
  // rclcpp::executors::MultiThreadedExecutor executor;
  // executor.add_node(pub_node_);
  // executor.add_node(service_node_);    // No need to add service node to executor since it only makes service calls and doesn't have any callbacks
  
  while (rclcpp::ok())
  {
    rclcpp::spin_some(pub_node_);
  }
}

int KeyboardServo::keyLoop()
{
  char c;
  bool publish_twist = false;
  bool publish_joint = false;
  bool servo_started = false;

  double max_velocity_x = 3.0543;
  double max_velocity_y = 2.4907;
  double max_velocity_z = 3.4907;
  double max_velocity_a = 5.236;
  double max_velocity_b = 5.236;
  double max_velocity_c = 8.3776;

  double scaling = 0.3;

  rclcpp::Rate loop_rate(1);

  std::thread{ std::bind(&KeyboardServo::spin, this) }.detach();

  puts("Reading from keyboard");
  puts("---------------------------");
  puts("Use arrow keys and the '.' and ';' keys to Cartesian jog");
  puts("Use 'W' to Cartesian jog in the world frame, and 'E' for the End-Effector frame");
  puts("Use 1|2|3|4|5|6|7 keys to joint jog. 'R' to reverse the direction of jogging.");
  puts("Use 'S' to START servo, 'SPACE' to STOP servo");
  puts("'Q' to quit.");

  for (;;)
  {
    // get the next event from the keyboard
    try
    {
      input.readOne(&c);
    }
    catch (const std::runtime_error&)
    {
      perror("read():");
      return -1;
    }

    RCLCPP_DEBUG(pub_node_->get_logger(), "value: 0x%02X\n", c);

    // // Create the messages we might publish
    auto twist_msg = std::make_unique<geometry_msgs::msg::TwistStamped>();
    auto joint_msg = std::make_unique<control_msgs::msg::JointJog>();

    // Use read key-press
    switch (c)
    {
      case KEYCODE_LEFT:
        RCLCPP_DEBUG(pub_node_->get_logger(), "LEFT");
        twist_msg->twist.linear.y = -axis_pos_cmd;
        publish_twist = true;
        break;
      case KEYCODE_RIGHT:
        RCLCPP_DEBUG(pub_node_->get_logger(), "RIGHT");
        twist_msg->twist.linear.y = axis_pos_cmd;
        publish_twist = true;
        break;
      case KEYCODE_UP:
        RCLCPP_DEBUG(pub_node_->get_logger(), "UP");
        twist_msg->twist.linear.x = axis_pos_cmd;
        publish_twist = true;
        break;
      case KEYCODE_DOWN:
        RCLCPP_DEBUG(pub_node_->get_logger(), "DOWN");
        twist_msg->twist.linear.x = -axis_pos_cmd;
        publish_twist = true;
        break;
      case KEYCODE_PERIOD:
        RCLCPP_DEBUG(pub_node_->get_logger(), "PERIOD");
        twist_msg->twist.linear.z = -axis_pos_cmd;
        publish_twist = true;
        break;
      case KEYCODE_SEMICOLON:
        RCLCPP_DEBUG(pub_node_->get_logger(), "SEMICOLON");
        twist_msg->twist.linear.z = axis_pos_cmd;
        publish_twist = true;
        break;
      case KEYCODE_E:
        RCLCPP_DEBUG(pub_node_->get_logger(), "E");
        frame_to_publish_ = EEF_FRAME_ID;
        break;
      case KEYCODE_W:
        RCLCPP_DEBUG(pub_node_->get_logger(), "W");
        frame_to_publish_ = BASE_FRAME_ID;
        break;
      case KEYCODE_1:
        RCLCPP_DEBUG(pub_node_->get_logger(), "1");
        joint_msg->joint_names.push_back("X_joint");
        joint_msg->velocities.push_back(max_velocity_x * scaling);
        publish_joint = true;
        break;
      case KEYCODE_2:
        RCLCPP_DEBUG(pub_node_->get_logger(), "2");
        joint_msg->joint_names.push_back("Y_joint");
        joint_msg->velocities.push_back(max_velocity_y * scaling);
        publish_joint = true;
        break;
      case KEYCODE_3:
        RCLCPP_DEBUG(pub_node_->get_logger(), "3");
        joint_msg->joint_names.push_back("Z_joint");
        joint_msg->velocities.push_back(max_velocity_z * scaling);
        publish_joint = true;
        break;
      case KEYCODE_4:
        RCLCPP_DEBUG(pub_node_->get_logger(), "4");
        joint_msg->joint_names.push_back("A_joint");
        joint_msg->velocities.push_back(max_velocity_a * scaling);
        publish_joint = true;
        break;
      case KEYCODE_5:
        RCLCPP_DEBUG(pub_node_->get_logger(), "5");
        joint_msg->joint_names.push_back("B_joint");
        joint_msg->velocities.push_back(max_velocity_b * scaling);
        publish_joint = true;
        break;
      case KEYCODE_6:
        RCLCPP_DEBUG(pub_node_->get_logger(), "6");
        joint_msg->joint_names.push_back("C_joint");
        joint_msg->velocities.push_back(max_velocity_c * scaling);
        publish_joint = true;
        break;
      case KEYCODE_7:
        RCLCPP_DEBUG(pub_node_->get_logger(), "7");
        // joint_msg->joint_names.push_back("panda_joint7");
        // joint_msg->velocities.push_back(joint_vel_cmd_);
        publish_joint = true;
        break;
      case KEYCODE_R:
        RCLCPP_DEBUG(pub_node_->get_logger(), "R");
        scaling *= -1.0;
        break;
      case KEYCODE_S:
        RCLCPP_DEBUG(service_node_->get_logger(), "S");
        if (service_node_->startServo()) {
          servo_started = true;
        }
        break;
      case KEYCODE_SPACE:
        RCLCPP_DEBUG(service_node_->get_logger(), "SPACE");
        if (service_node_->stopServo()) {
          servo_started = false;
        }
        break;
      case KEYCODE_Q:
        RCLCPP_DEBUG(pub_node_->get_logger(), "quit");
        return 0;
      default:
        break;
    }
    // If a key requiring a publish was pressed, publish the message now
    if (publish_twist)
    {
      if (!servo_started) 
      {
        RCLCPP_WARN(pub_node_->get_logger(), "Servo has not been started yet! Press 'S' to start the servo.");
        publish_twist = false;
      }
      else
      {
        twist_msg->header.stamp = pub_node_->now();
        twist_msg->header.frame_id = frame_to_publish_;
        pub_node_->publishTwist(*twist_msg);
        publish_twist = false;
      }

    }
    else if (publish_joint)
    {
      if (!servo_started) 
      {
        RCLCPP_WARN(pub_node_->get_logger(), "Servo has not been started yet! Press 'S' to start the servo.");
        publish_joint = false;
      }
      else
      {
        joint_msg->header.stamp = pub_node_->now();
        joint_msg->header.frame_id = BASE_FRAME_ID;
        pub_node_->publishJoint(*joint_msg);
        publish_joint = false;
      }
    }

    // loop_rate.sleep();  // make sure that publish rate is only 1s
  }

  return 0;
}


int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  KeyboardServo keyboard_servo;

  signal(SIGINT, quit);

  int rc = keyboard_servo.keyLoop();
  input.shutdown();
  rclcpp::shutdown();

  return rc;
}