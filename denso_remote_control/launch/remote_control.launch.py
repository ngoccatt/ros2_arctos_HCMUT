from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command, FindExecutable
from launch.actions import RegisterEventHandler, DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription, LogInfo

def generate_launch_description():
    # MoveItConfigsBuilder automatically do the following:
    # .robot_description: create urdf file using command: xacro denso.urdf.xacro
    # .robot_description_semantic
    moveit_config = (
        MoveItConfigsBuilder("denso")
        .robot_description(file_path="config/denso.urdf.xacro")
        .robot_description_semantic(file_path="config/denso.srdf")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .planning_pipelines(pipelines=["ompl", "chomp"])
        .to_moveit_configs()
    )

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )


    # seem like we need a launch file and pass all robot config to the c file.
    # can't run c file independently
    # MoveGroupInterface demo executable
    remote_control_demo = Node(
        name="remote_control_server_executer",
        package="denso_remote_control",
        executable="remote_control_server_executer",
        output="screen",
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            {"use_sim_time" : use_sim_time}
        ],
    )

    return LaunchDescription([
        declare_use_sim_time,
        LogInfo(msg=["Launching remoteControl with..."]),
        LogInfo(msg=["use_sim_time: ", use_sim_time]),
        remote_control_demo
        ])
