# Purpose of this package

The File server is to allow sending files to and from Unity. 

Currently, it's used to transfer URDF description of the robot to Unity.

[The RosBridgeSocket](https://github.com/siemens/ros-sharp/wiki/User_Inst_ROSOnUbuntu)

[The FileServer](https://github.com/siemens/ros-sharp/wiki/Dev_FileServer)

# How to transfer the URDF description to Unity?

1. Run this package via 

```bash
ros2 launch file_server2 ros_sharp_communication.launch.py
```

2. Then run our bringup file so that \robot_description have some data to transmit

```bash
ros2 launch denso_bringup gz_denso_bringup.launch.py use_sim_time:=true
```