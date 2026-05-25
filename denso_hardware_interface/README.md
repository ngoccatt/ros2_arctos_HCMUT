# denso_hardware_interface

## Description

This package provides a ROS2 hardware interface of the denso robot.

It uses the denso_motor_driver package to control the motors and ros2_control to provide a hardware interface to ROS.

## Directories

The package is organized as follows:

```
denso_hardware_interface
├── include
│   └── denso_hardware_interface
│       ├── denso_interface.hpp # Class to control the hardware interface
│       └── denso_services.hpp  # Class to provide services to the hardware interface (Unused at the moment)
├── src
│   └── denso_interface.cpp     # Implementation of the denso_interface.hpp
│   └── denso_services.cpp      # Implementation of the denso_services.hpp (Unused at the moment)
├── launch                       # Launch files
```

## Note

This package is still in development and may have bugs.


### The cool part:
- Moveit 
    - send trajectory "once" to action server, and ros2_controller received it, parse to more detailed trajectory commands, then run the control loop (read, update, write)
    - --> Robot then rotate very smooth, since command send continously and faster than the robot arm could process, so robot arm always have commands to process and rotate continously.
- Realtime Servo
    - Did not use action server, instead send the trajectory to denso_arm_controller/joint_trajectory.
    - Every time the trajectory reach ros2_controller, it then "cancel" the previous trajectory, check the robot current state, and generate new trajectory commands
    - --> In this case, previous trajectory always faster, so greater position is sent to robot already. new trajectory created start at a smaller position, cause oscillating (joint move back and forth a lot).
        - So I tried to implement a trend detection: skip smaller position command, but this in turn cause robot flickering: 
            - at 100ms, command pos 16 sent to robot
            - at 200ms, command pos 11 sent (skip)
            - at 300ms, command pos 15 sent (skip)
            - at 400ms, command pos 18 sent to robot 
            - so there's a delay between commands sent to robot, this delay is long enough for previous action stopped, then force to run again. --> flickering.

## Disclaimer

We are not responsible for any damage caused by the use of this package. Use it at your own risk.