# ROS2 Denso
![Discord](https://img.shields.io/discord/1099629962618748958?logo=discord&logoColor=%23FFFFFF&logoSize=auto)


## **Warning** 

This project is still under development and is not yet ready for production use. We are actively working on improving the project and adding new features. If you would like to contribute, please see the [Contributing Guidelines](CONTRIBUTING.md).

## Overview

**ROS2 Denso** is a **ROS2 package** designed for controlling the Denso robot arm using **MoveIt! for motion planning**. The project is structured into multiple packages, each handling a specific aspect of the robotic arm.

## Repository Structure

```
ros2_denso/
│── denso_bringup/              # Launch and runtime management
│── denso_description/          # URDF and robot model files
│── denso_hardware_interface/   # ROS2 control hardware abstraction
│── denso_interfaces/           # Custom Interfaces (msg, action...) used 
│── denso_motor_driver/         # motor driver (VS-6577) + servo driver (gripper) implementation
│── denso_moveit_config/        # MoveIt! motion planning configurations
│── denso_moveit_servo/         # Service implementation to use MoveIt-Servo
│── denso_remote_control/       # Action implementation to control robot via MoveToPose action
│── file_server2/               # RosBridge Server launcher for Unity to connect to Ros2
│── scripts/                    # Utility scripts
│── assets/                     # Images and other assets
│── LICENSE                     # Project license
│── README.md                   # Project documentation
```

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
colcon build --symlink-install
source install/setup.bash
```

You should now have the workspace built and ready to use.

### Getting Started

Make sure to always source the workspace that we've just built before running:

```bash
cd ~/ros2_ws
source install/setup.bash
```

#### Launch the robot

To launch the robot with real hardware, run the launch file `denso_bringup.launch.py`:

```bash
ros2 launch denso_bringup denso_bringup.launch.py use_sim_time:=false
```

To launch the robot with gazebo sim, run the launch file `gz_denso_bringup.launch.py`:

```bash
ros2 launch denso_bringup gz_denso_bringup.launch.py use_sim_time:=true
```

#### Launch the supporting packages for extra functionality:

To launch MoveToPose action server, that support receiving a Pose or a Joint, and planning-execute the robot to reach that Pose/Joints:

```bash
ros2 launch denso_remote_control remote_control.launch.py use_sim_time:=false
```

To launch real-time servo, allowing to rotate each joint (and hopefully, rotate by axis of effector), launch moveit_servo by:

```bash
ros2 launch denso_moveit_servo denso_moveit_servo.launch.py use_sim_time:=false
```

To communicate with Unity via Ros-sharp, use:

```bash
ros2 launch file_server2 ros_sharp_communication.launch.py
```

To allow VR application to access the RosBridge server on WSL, run the following command on Admin Powershell:

```bash
netsh interface portproxy add v4tov4 listenport=9090 listenaddress=<Windows IP> connectport=9090 connectaddress=(wsl hostname -I)
```

## Individual Package READMEs

Each package has its own **README.md** with more details:

- [denso\_bringup](denso_bringup/README.md)
- [denso\_description](denso_description/README.md)
- [denso\_hardware\_interface](denso_hardware_interface/README.md)
- [denso\_motor\_driver](denso_motor_driver/README.md)
- [denso\_moveit\_base\_xyz](denso_moveit_base_xyz/README.md)
- [denso\_moveit\_config](denso_moveit_config/README.md)

## Contributing

Please follow our [Contributing Guidelines](CONTRIBUTING.md) before making any changes to the project.

We also expect all contributors to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

This project is licensed under the [Apache License](LICENSE).

