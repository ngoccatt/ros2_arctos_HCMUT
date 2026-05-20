import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from moveit_configs_utils import MoveItConfigsBuilder
from launch_param_builder import ParameterBuilder
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command, FindExecutable



def generate_launch_description():
    # MoveItConfigsBuilder automatically do the following:
    # .robot_description: create urdf file using command: xacro denso.urdf.xacro
    # .robot_description_semantic
    moveit_config = (
        MoveItConfigsBuilder("denso")
        .robot_description(file_path="config/denso.urdf.xacro")
        .robot_description_semantic(file_path="config/denso.srdf")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .robot_description_kinematics(file_path="config/kinematics.yaml")
        .planning_pipelines(pipelines=["ompl", "chomp"])
        .to_moveit_configs()
    )

    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )
    # Get parameters for the Servo node
    servo_params = (
        ParameterBuilder("denso_moveit_servo")
        .yaml(
            parameter_namespace="denso_moveit_servo",
            file_path="config/denso_config_servo.yaml",
        )
        .to_dict()
    )

    # The servo cpp interface demo
    # Creates the Servo node and publishes commands to it
    servo_node = Node(
        package="denso_moveit_servo",
        executable="denso_moveit_servo_node_exec",
        output="screen",
        parameters=[
            servo_params,
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            {"use_sim_time": use_sim_time}
        ],
    )

    return LaunchDescription(
        [declare_use_sim_time, servo_node]
    )
