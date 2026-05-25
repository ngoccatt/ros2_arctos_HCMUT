# DENSO_MOVEIT_SERVO

This package provides a MoveIt Servo node for controlling Denso robots in real-time using MoveIt2 Realtime Servo. It allows for Cartesian and joint space control of the robot, enabling smooth and responsive motion.

## Requirements

Install the following dependencies:

```bash
sudo apt install ros-humble-moveit-servo -y
```

## Details of the package

### The Servo Node

The Servo node is implemented based on realtime_servo node demo in MoveIt2 package. It relies on `denso_config_servo.yaml` for its configuration.

To start the controlling via Servo, send a service request to 
- `/denso_moveit_servo_node/start_servo` [std_srvs/srv/Trigger]

To stop (pause) the controlling via Servo, send a service request to
- `/denso_moveit_servo_node/stop_servo` [std_srvs/srv/Trigger]

After starting the control, these topics are available for sending commands to the robot:
- `/denso_moveit_servo_node/delta_joint_cmds` [control_msgs/msg/joint_jog]: 
    - Publish request to this topic to rotate each joint at a certain velocity.
- `/denso_moveit_servo_node/delta_twist` [geometry_msgs/msg/TwistStamped]: 
    - Publish request to this topic to send Cartesian velocity commands to the robot.

Upon receiving commands, MoveIt Servo will calculate the Joint_Trajectory and publish it to `command_out_topic` (configured in yaml) for the robot to execute. In our case, it is `/denso_arm_controller/joint_trajectory` [trajectory_msgs/msg/JointTrajectory]. Command_out_topic is sent periodically, equal to `publish_period` configured in yaml.

Commands must be sent continuously (<= `incoming_command_timeout` configured in yaml) to keep the robot moving. If the node does not receive any command for a certain amount of time, the Joint_Trajectory messages sent to denso_arm_controller will be stopped.

## How to run

### Running the Servo Node

Servo node should be run after the robot bringup is launched. With the Servo node running, you have the following topics/services available:

On a new terminal:

```bash
ros2 launch denso_moveit_servo denso_moveit_servo.launch.py
```

### Run the keyboard input control (optional)

This will help you to control the robot using keyboard input. Details of how to use the keyboard input will be present when running the executable.

On a new terminal:

```bash
ros2 run denso_moveit_servo servo_keyboard_input
```

## Troubleshooting
In case if you send the command 1 time but the robot still rotates (Joint_Trajectory messages are still being sent) means that there's a mismatch in the "timestamp" received from command and the Node clock. In our case, this node use the real time and the commands timestamp is also real time, not the simulation time. So make sure to set `use_sim_time` to false in the launch file.

## References

https://moveit.picknik.ai/main/doc/examples/realtime_servo/realtime_servo_tutorial.html
https://moveit.picknik.ai/humble/doc/examples/realtime_servo/realtime_servo_tutorial.html
https://github.com/moveit/moveit2/blob/main/moveit_ros/moveit_servo/config/servo_parameters.yaml
https://github.com/moveit/moveit_msgs/blob/ros2/msg/ServoStatus.msg
