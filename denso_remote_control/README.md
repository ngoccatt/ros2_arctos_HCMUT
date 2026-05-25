# DENSO REMOTE CONTROL

## About this package

This package create an action server called **move_to_pose**, accepting goal of type **MoveToPose** defined in \denso_interfaces.

## Launch the package

To launch MoveToPose action server, that support receiving a Pose or a Joint, and planning-execute the robot to reach that Pose/Joints:

```bash
ros2 launch denso_remote_control remote_control.launch.py use_sim_time:=false
```

## Limitation

- The implementation, expecially for moving joints only support robot with 6 joints.

- Either Joints or Pose is selected via **use_pose** in the MoveToPose goal.