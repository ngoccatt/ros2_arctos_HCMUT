from launch import LaunchDescription
from launch.actions import RegisterEventHandler, DeclareLaunchArgument, LogInfo
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node
from launch.substitutions import Command, PathJoinSubstitution
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    # Correct package paths
    denso_hw = get_package_share_directory("denso_hardware_interface")
    denso_moveit = get_package_share_directory("denso_moveit_config")

    # Use URDF from MoveIt (this is the ONLY URDF that works in your workspace)
    urdf_path = PathJoinSubstitution([
        denso_moveit,
        "config",
        "denso.urdf.xacro"
    ])

    # Controllers YAML from moveit_config (same as working version)
    controllers_yaml = os.path.join(
        denso_moveit, "config", "ros2_controllers.yaml"
    )

    # robot_description
    robot_description = {
        "robot_description": Command(["xacro ", urdf_path])
    }

    # Robot controllers
    robot_controllers = controllers_yaml

    # Node: robot_state_publisher
    robot_state_pub = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    # Node: ros2_control_node
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, robot_controllers],
        output="screen",
        remappings={
            ("/controller_manager/robot_description", "/robot_description"),
        }
    )

    # Spawner: joint_state_broadcaster
    js_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    # Spawner: arm
    arm_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["denso_arm_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    # Spawner: hand (optional)
    hand_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["denso_hand_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    # Delay arm + hand after joint_state_broadcaster
    delay_arm = RegisterEventHandler(
        OnProcessExit(
            target_action=js_broadcaster,
            on_exit=[arm_controller, hand_controller],
        )
    )

    return LaunchDescription([
        LogInfo(msg=["Launching Denso Hardware Test (ROS2 Control Clean Version)..."]),
        control_node,
        robot_state_pub,
        js_broadcaster,
        delay_arm,
    ])
