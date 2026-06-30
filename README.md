# ROS2 Arctos — HCMUT

## Warning

This project is still under development and is not yet ready for production use.

**USE AT YOUR OWN RISK.**

Only operate the robot if you have:
- Ensured the robot arm is securely mounted and cannot tip over.
- Ensured at least **1 metre of clearance** around the arm in all directions.
- Ensured no fragile objects are within the arm's reach.
- Stay close to the robot and be ready to cut power if unexpected motion occurs.

---

## Overview

**ROS2 Arctos HCMUT** controls a 6-DOF Arctos robot arm over UART using MKS stepper motor drivers. It supports real-hardware operation, Gazebo Ignition simulation, gesture-based control, and automated visual inspection with an AI classifier.

### Hardware
- **Robot**: 6-DOF Arctos arm — joints X, Y, Z, A, B, C
- **Gripper**: single servo jaw (`gripper_gear_right_joint`)
- **Motor drivers**: MKS57D (X, Y) and MKS42D (Z, A, B, C, gripper) via UART/Serial
- **Camera**: UGREEN USB webcam (eye-in-hand, for inspection and gesture)
- **AI accelerator**: Google Coral USB (optional, for EdgeTPU inference)

### Software stack
- **ROS2 Humble** on Ubuntu 22.04
- **MoveIt2** (OMPL + CHOMP + Pilz planners)
- **ros2_control** + JointTrajectoryController
- **Gazebo Ignition Fortress** (simulation)
- Python 3.10 (ROS2 nodes) + Python 3.9 via pyenv `gesture_env` (TFLite/EdgeTPU)

---

## Repository Structure

```
ros2_arctos_HCMUT/
├── serial/                      # UART serial library
├── arctos_description/          # URDF / xacro robot model
├── arctos_motor_driver/         # Low-level UART motor driver
├── arctos_hardware_interface/   # ros2_control hardware plugin
├── arctos_moveit_config/        # MoveIt2 config, SRDF, worlds
├── arctos_bringup/              # Top-level launch files
├── denso_interfaces/            # Custom ROS2 msgs/srvs/actions
├── denso_remote_control/        # MoveToPose action server
├── denso_moveit_servo/          # Real-time MoveIt Servo node
├── file_server2/                # ROS-Sharp / Unity URDF bridge
├── gesture_control/             # Gesture recognition → MoveIt2
├── visual_inspection/           # AI visual inspection pipeline
├── AI_modules/
│   ├── gesture_recognition/     # Gesture model training
│   ├── object_detection/        # Cube detection training + dataset_collector
│   └── visual_inspection/       # Inspection model training + dataset tools
└── scripts/                     # Utility scripts
```

---

## Installation

### Requirements

Ensure you have **Ubuntu Jammy (22.04)** installed before proceeding.

It is recommended to follow the official installation guides for ROS2 and MoveIt:

- [ROS2 Humble Installation](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html)
    - Install `ros-humble-desktop` for the full desktop installation.
    - Install `ros-dev-tools` for the development tools.
- [MoveIt! 2 Installation](https://moveit.ai/install-moveit2/binary/)
    - After installing MoveIt! 2, you might install also `CycloneDDS`. if you accidently config firewall which block UDP 7400, 7600, ros2 won't work. For convenient, consider disable your firewall:

        ```bash
        sudo ufw disable
        ```

    - or if you don't want to disable the firewall, then allow the ports. But I'm not sure if there're other ports need to enable for ROS to be stable.

        ```bash
        sudo ufw allow 7400
        sudo ufw allow 7600
        ```
- [Gazebo Fortress Installation](https://gazebosim.org/docs/fortress/install_ubuntu/)
    - Follow the instruction to install Gazebo Fortress (Ignition)

### Setting Up the Workspace

This section will guide you through setting up the ROS2 workspace and installing the remaining dependencies.
Please note, this assumes **you have already installed ROS2 Humble**.

First, install the required dependencies:
- `can-utils` for the CAN utilities.
- `python3-rosdep` for the easily installing dependencies.
- `ros-humble-can-msgs` for the CAN messages.
- `ros-humble-ros2-control` for the ROS2 control packages.
- `ros-humble-gz-ros2-control` for the Gazebo ROS2 control packages.
- `ros-humble-gz-ros2-control-demos` for the Gazebo ROS2 control demos.
- `ros-humble-gripper-controllers` for the gripper controllers.
- `ros-humble-moveit-servo` for the MoveIt! servo package.
- `ros-humble-v4l2-camera` for the V4L2 camera package.
- `ros-humble-rqt-image-view` for the RQT image view package.
- `ros-humble-image-transport-plugins` for the image transport plugins (including image compression).

```bash
sudo apt install can-utils python3-rosdep ros-humble-can-msgs ros-humble-ros2-control ros-humble-gz-ros2-control ros-humble-gz-ros2-control-demos ros-humble-gripper-controllers ros-humble-moveit-servo ros-humble-v4l2-camera ros-humble-rqt-image-view ros-humble-image-transport-plugins ros-humble-rosbridge-server -y
```

**Open new terminal**, then create a ROS2 workspace and clone the ROS2 Denso repository inside the `src/` directory:
- Note: As GitHub removed password authentication, SSH is preferred to clone this repo. Prepare your SSH key and link with github, tutorial can be find here: [Configure ssh for github authentication](https://dev.to/jajera/how-to-configure-ssh-for-github-authentication-2b53)

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone --recurse-submodules git@github.com:ngoccatt/ros2_arctos_HCMUT.git
```

**Note**: If you are on a different branch, you need to checkout the branch you want to use.

```bash
cd ros2_arctos_HCMUT
git checkout <branch_name>
```

Then navigate to the workspace root:
```bash
cd ~/ros2_ws
```

### Install the Python dependencies:

It's suggested to use Pyenv to manage environment. to install pyenv, follow [realPython tutorial](https://realpython.com/intro-to-pyenv/). Remember to register pyenv into bash.

Move into ros2_ws folder. install Python 3.10.12, then create an virtual env **denso** out of it

```bash
pyenv install 3.10.12
pyenv virtualenv 3.10.12 denso
```

You can check for installed python versions and virtualenvs using:

```bash
pyenv versions
pyenv virtualenvs
```

Then, activate **denso** as the virtual env for ros2_ws folder. activate it whenever needed.

```bash
pyenv local denso
pyenv activate
```

Install needed dependency for the project.

```bash
pip install python-can ruamel.yaml rich keyboard catkin-pkg lark PyQt5 PySide2 empy==3.3.4 tornado numpy pyyaml jinja2 typeguard pymongo Pillow netifaces cbor2
```

#### 5 — Set up Python environments with pyenv (optional for AI)

The project uses **two Python environments**:

| Environment | Python | Purpose |
|---|---|---|
| `denso` | 3.10.12 | ROS2 nodes |
| `gesture_env` | 3.9.17 | TFLite / EdgeTPU inference (pycoral requires 3.9) |

Install pyenv following the [pyenv guide](https://realpython.com/intro-to-pyenv/), then:

```bash
# Python 3.9 for AI inference
pyenv install 3.9.17
pyenv virtualenv 3.9.17 gesture_env
pyenv activate gesture_env
pip install tensorflow==2.13.0 numpy opencv-python pyyaml
# Optional — EdgeTPU (requires Coral USB plugged in):
pip install pycoral
```

### Building the Workspace

Before building the workspace, source your ROS2 installation:

**Note**:*It is recommended to add this to your `.bashrc` file*.

```bash
source /opt/ros/humble/setup.bash
```

Initialize `rosdep` and install the dependencies:

```bash
sudo rosdep init
rosdep update
```

Install the dependencies:

```bash
rosdep install --from-paths src -y --ignore-src
```

**Note**: You may encounter an error with the package `ros-humble-warehouse-ros-mongo`. You can ignore this package for now.


#### Build the serial package

Move into serial folder and build it first:

```bash
cd ~/ros2_ws/src/ros2_denso_HCMUT/serial
make
make install
```

Build the workspace using `colcon`:

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
sudo rosdep init && rosdep update
rosdep install --from-paths src -y --ignore-src

colcon build --symlink-install
source install/setup.bash
```

---

## Running the Robot

Always source the workspace first:
```bash
source ~/ros2_ws/install/setup.bash
```

#### Launch the robot

To launch the robot with real hardware, run the launch file `denso_bringup.launch.py`:

**Terminal 1 — Hardware bringup** (controllers + RViz + MoveIt):
```bash
ros2 launch denso_bringup denso_bringup.launch.py use_sim_time:=false
```

To launch the robot with gazebo sim, run the launch file `gz_denso_bringup.launch.py`:

```bash
ros2 launch denso_bringup gz_denso_bringup.launch.py use_sim_time:=true
```

---

## Optional Packages

### Real-time servo (keyboard / Cartesian control)

```bash
# Terminal 2
ros2 launch denso_moveit_servo denso_moveit_servo.launch.py use_sim_time:=false
# Terminal 3
ros2 run denso_moveit_servo servo_keyboard_input
```

### Remote control (MoveToPose action server)

```bash
ros2 launch denso_remote_control remote_control.launch.py use_sim_time:=false
```

### Unity / ROS-Sharp bridge

```bash
ros2 launch file_server2 ros_sharp_communication.launch.py
```

To allow VR application to access the RosBridge server on WSL, run the following command on Admin Powershell:

```bash
netsh interface portproxy add v4tov4 listenport=9090 listenaddress=<Windows IP> connectport=9090 connectaddress=(wsl hostname -I)
```

### Gesture control (by namdiep-239)

```bash
# CPU inference (no Coral needed)
ros2 launch gesture_control gesture_control.launch.py inference_mode:=cpu

# EdgeTPU inference (Coral USB plugged in)
ros2 launch gesture_control gesture_control.launch.py inference_mode:=edgetpu
```

| Gesture | Action |
|---|---|
| thumbs_up | Move to `home` pose |
| point | Raise arm (Y_joint +0.3 rad) |
| open | Open gripper |
| fist | Close gripper |
| none | Stop arm |

### Visual inspection (by namdiep-239)

Requires hardware bringup running first.

```bash
# Terminal 2 — Inspection nodes
ros2 launch visual_inspection visual_inspection.launch.py use_sim_time:=false

# Terminal 3 — Trigger one inspection cycle
ros2 action send_goal /run_inspection visual_inspection/action/RunInspection \
  "{object_id: 'part_001'}"
```

The node drives the arm through 5 inspection poses, collects AI votes at each, classifies the object (PASS/FAIL), then sorts it to the corresponding tray.

See [visual_inspection/README.md](visual_inspection/README.md) for the full pipeline.

---

## Package READMEs

- [arctos_bringup](arctos_bringup/README.md)
- [arctos_description](arctos_description/README.md)
- [arctos_hardware_interface](arctos_hardware_interface/README.md)
- [arctos_motor_driver](arctos_motor_driver/README.md)
- [arctos_moveit_config](arctos_moveit_config/README.md)
- [denso_moveit_servo](denso_moveit_servo/README.md)
- [denso_remote_control](denso_remote_control/README.md)
- [visual_inspection](visual_inspection/README.md)
- [AI_modules/object_detection](AI_modules/object_detection/README.md)

---

## Contributing

Please follow the [Contributing Guidelines](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

## License

This project is licensed under the [Apache License](LICENSE).

