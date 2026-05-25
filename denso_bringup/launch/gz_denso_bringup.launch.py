from launch import LaunchDescription
from launch.actions import RegisterEventHandler, DeclareLaunchArgument
from launch.event_handlers import OnProcessExit
from launch.actions import IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import FrontendLaunchDescriptionSource, PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command, FindExecutable
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder
import os


def generate_launch_description():
    # Get package paths
    denso_hardware_interface_dir = get_package_share_directory('denso_hardware_interface')
    denso_moveit_dir = get_package_share_directory('denso_moveit_config')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )


    # MoveItConfigsBuilder automatically do the following:
    # .robot_description: create urdf file using command: xacro gz_denso.urdf.xacro
    # .robot_description_semantic
    moveit_config = (
        MoveItConfigsBuilder("denso")
        .robot_description(file_path="config/gz_denso.urdf.xacro")
        .robot_description_semantic(file_path="config/denso.srdf")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .planning_pipelines(pipelines=["ompl", "chomp"])
        .to_moveit_configs()
    )

    rviz_base = os.path.join(get_package_share_directory("denso_moveit_config"), "config")
    rviz_full_config = os.path.join(rviz_base, "moveit_chomp.rviz")
    rviz_empty_config = os.path.join(rviz_base, "moveit.rviz")

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        output="screen",
        arguments=["-d", rviz_empty_config],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.planning_pipelines,
            moveit_config.robot_description_kinematics,
            {"use_sim_time": use_sim_time},
        ],
    )
    # Nodes
    # publish the state of robot to TF (transform)
    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="both",
        parameters=[moveit_config.robot_description, {"use_sim_time": use_sim_time}],
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )

    robot_arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["denso_arm_controller", "--controller-manager", "/controller_manager"],
    )

    robot_hand_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["denso_hand_controller", "--controller-manager", "/controller_manager"],
    )

    # control node is removed, since:

    #gz_ros2_control is installed, so the issue is architectural. Your launch file has a conflict:

    # The URDF (via denso.ros2_control.xacro) already defines a 
    # gz_ros2_control::GazeboSimROS2ControlPlugin Gazebo plugin — 
    # this plugin automatically creates and manages the controller manager 
    # inside the Gazebo process and loads GazeboSimSystem internally.

    # Your launch file also starts a standalone ros2_control_node (control_node), 
    # which tries to independently load gz_ros2_control/GazeboSimSystem — 
    # but that plugin only works inside the Gazebo context, not as a standalone process. 

    # The standalone control_node should be removed. The Gazebo plugin handles everything

    # spawn robot in Gazebo
    gz_spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=['-topic', 'robot_description',
                   '-name', 'denso', '-allow_renaming', 'true'],
    )

    # Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )

    # Include MoveIt Launch
    move_group_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([denso_moveit_dir, "launch", "move_group.launch.py"])
        ),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    world_path = PathJoinSubstitution([
        denso_moveit_dir,
        "worlds",
        "denso_world.sdf"
    ])

    # Include Gazebo launch
    gz_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [PathJoinSubstitution([FindPackageShare('ros_gz_sim'),
                                       'launch',
                                       'gz_sim.launch.py'])]),
            launch_arguments=[('gz_args', ['-r -v 1 ', world_path])])

    # Ensure joint state broadcaster starts before controllers
    # wait for "target_action to exit" before starting the next one, 
    # so that we can be sure the controllers are started after 
    # the joint state broadcaster
    delay_robot_arm_controller_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[robot_arm_controller_spawner, robot_hand_controller_spawner],
        )
    )

    # Delay rviz and moveit launch until controllers are ready
    delay_rviz_and_moveit_launch = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=robot_arm_controller_spawner,
            on_exit=[rviz_node, move_group_launch]
        )
    )

    rosbridge_server = PathJoinSubstitution(
        [get_package_share_directory('rosbridge_server'), 'launch', 'rosbridge_websocket_launch.xml']
    )

    rosbridge_server_launch = IncludeLaunchDescription(
        FrontendLaunchDescriptionSource([rosbridge_server]),
        launch_arguments={
            'port': '9090',
            'fragment_timeout': '600',
            'unregister_timeout': '10.0',
            'max_message_size': '100000000',
            'default_call_service_timeout': '10.0',
            'call_services_in_new_thread': 'true',
            'send_action_goals_in_new_thread': 'true'
        }.items()
    )

    camera_node_v4l2 = Node(
        package='v4l2_camera',
        executable='v4l2_camera_node',
        name='v4l2_camera',
        output='screen',
        parameters=[
            {
                'video_device': '/dev/video0',     
                'image_size': [640, 480],
                'pixel_format': 'YUYV',             
                'output_encoding': 'rgb8', 
                'qos_overrides': {
                    '/camera/image_raw': {
                        'publisher': {
                            'reliability': 'best_effort',
                            'history': 'keep_last',
                        }
                    }
                }
            }
        ],
        remappings=[
            ('image_raw', '/camera_1/image_raw'),
            ('camera_info', '/camera_1/camera_info'),
            ('image_raw/compressed', '/camera_1/image_raw/compressed'),
        ]
    )

    camera_node_usbcam = Node(
        package='usb_cam',
        executable='usb_cam_node_exe',
        name='usb_cam',
        output='screen',
        parameters=[
            {
                'video_device': '/dev/video0',
                'image_width': 320,
                'image_height': 240,
                'pixel_format': 'mjpeg2rgb',
                'camera_frame_id': 'camera_optical_frame',
                'framerate': 30.0,
                'brightness': 128,
                'exposure_auto': 3,       # 3 = aperture priority auto
                'autoexposure': True,
            }
        ],
        remappings=[
            ('image_raw', '/camera/image_raw'),
            ('camera_info', '/camera/camera_info'),
            ('image_raw/compressed', '/camera/image_raw/compressed'),
        ]
    )

     # Load controller parameters
    
    return LaunchDescription([
        declare_use_sim_time,
        LogInfo(msg=["Launching Gz Denso Bringup with RViz..."]),
        LogInfo(msg=["use_sim_time: ", use_sim_time]),
        gz_launch,
        gz_spawn_entity,
        bridge,
        robot_state_pub_node,
        joint_state_broadcaster_spawner,
        delay_robot_arm_controller_spawner,
        delay_rviz_and_moveit_launch,
        rosbridge_server_launch,
        camera_node_v4l2,
        # camera_node_usbcam,
        # Launch Arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value=use_sim_time,
            description='If true, use simulated clock'),
    ])
