import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution

def generate_launch_description():
    denso_description_dir = get_package_share_directory('denso_description')
    denso_hardware_interface_dir = get_package_share_directory('denso_hardware_interface')
    denso_moveit_dir = get_package_share_directory('denso_moveit_base_xyz')

    # # Launch RViz
    rviz_config_file = os.path.join(denso_description_dir, 'rviz', 'denso.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
    )

    urdf_file = os.path.join(denso_description_dir, 'urdf', 'denso.xacro')
    robot_description_content = Command(
        [
            FindExecutable(name='xacro'), ' ',
            urdf_file
        ]
    )
    robot_description = {'robot_description': ParameterValue(robot_description_content, value_type=str)}

    robot_state_pub_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description]
    )

    # Launch joint state publisher
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
    )

    # Launch MoveIt
    # moveit_launch_file = os.path.join(denso_moveit_dir, 'launch', 'move_group.launch.py')
    # moveit_launch = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(moveit_launch_file),
    # )
    can_launch_file = os.path.join(denso_hardware_interface_dir, 'launch', 'can_interface.launch.py')
    can_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(can_launch_file),
    )

    robot_controllers = PathJoinSubstitution(
        [
            # FindPackageShare("denso_description"),
            # "config",
            # "denso_controller.yaml",
            FindPackageShare("denso_moveit_base_xyz"),
            "config",
            "ros2_controller.yaml",
        ]
    )

    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_controllers],
        remappings=[
            (   
                "/controller_manager/robot_description", 
                "/robot_description",
            ),
            (
                "/forward_position_controller/commands",
                "/position_commands",
            ),
        ],
        output="both",
    )
    robot_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["denso_controller", "-c", "/controller_manager"],
    )
    nodes = [
        control_node,
        robot_controller_spawner,
        rviz_node,
        robot_state_pub_node,
        joint_state_publisher_node,
        # moveit_launch,
        can_launch,
    ]

    return LaunchDescription(nodes)
