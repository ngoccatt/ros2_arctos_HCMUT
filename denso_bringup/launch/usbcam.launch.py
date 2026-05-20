from launch import LaunchDescription
from launch.actions import RegisterEventHandler, DeclareLaunchArgument
from launch.event_handlers import OnProcessExit
from launch.actions import IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command, FindExecutable
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
import os

# incase laptop camera can't transmit image data in YUYV format (due to limit bandwidth in wsl)
# this can be use temporary to publish camera data using usb_cam.

def generate_launch_description():
    
    camera_node = Node(
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
    
    return LaunchDescription([
        LogInfo(msg=["Launching Denso Bringup with RViz..."]),
        camera_node,
        # can_launch
    ])
