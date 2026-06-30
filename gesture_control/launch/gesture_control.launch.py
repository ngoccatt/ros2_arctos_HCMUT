"""
gesture_control.launch.py

Launches the gesture_control nodes:
  1. gesture_recognition_node  — Python 3.10, spawns inference backend subprocess
  2. gesture_commander_node    — C++, MoveGroupInterface + gripper action client
  3. gesture_metrics_node      — Python 3.10, CSV + JSON performance logger
                                 (disabled with  enable_metrics:=false)

Launch arguments:
  inference_mode    edgetpu | cpu       (default: cpu)
  camera_id         int                 (default: 0)
  python_binary     path                (default: gesture_env Python 3.9.17)
  use_sim_time      true | false        (default: false — set true for Gazebo)
  enable_metrics    true | false        (default: true)
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    pkg_share = get_package_share_directory('gesture_control')

    # ── Resolve paths ─────────────────────────────────────────────────────────
    backend_script = os.path.join(pkg_share, 'scripts', 'gesture_inference_backend.py')

    # AI models live in the workspace source tree (not installed to avoid
    # duplicating large binary files). Navigate from install → workspace root.
    #   install/gesture_control/share/gesture_control  →  (4 levels up)  →  workspace
    workspace_root = os.path.normpath(os.path.join(pkg_share, '..', '..', '..', '..'))
    ai_module_models = os.path.join(
        workspace_root, 'src', 'ros2_arctos_HCMUT',
        'AI_modules', 'gesture_recognition', 'models'
    )
    edgetpu_model = os.path.join(ai_module_models, 'gesture_retrained_int8_edgetpu.tflite')
    cpu_model     = os.path.join(ai_module_models, 'gesture_best.h5')
    metadata      = os.path.join(ai_module_models, 'model_metadata.json')

    gesture_config = os.path.join(pkg_share, 'config', 'gesture_config.yaml')

    # ── Robot description (needed by MoveGroupInterface) ──────────────────────
    moveit_config = (
        MoveItConfigsBuilder("denso", package_name="denso_moveit_config")
        .robot_description(file_path="config/denso.urdf.xacro")
        .robot_description_semantic(file_path="config/denso.srdf")
        .to_moveit_configs()
    )

    # ── Launch arguments ──────────────────────────────────────────────────────
    inference_mode_arg = DeclareLaunchArgument(
        'inference_mode',
        default_value='cpu',
        description="Inference backend: 'edgetpu' (Coral) or 'cpu' (TensorFlow Keras)")

    camera_id_arg = DeclareLaunchArgument(
        'camera_id',
        default_value='0',
        description='OpenCV camera device index')

    python_binary_arg = DeclareLaunchArgument(
        'python_binary',
        default_value='/home/nam/.pyenv/versions/gesture_env/bin/python',
        description='Python interpreter for the inference backend (must have pycoral/tensorflow)')

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock (true for Gazebo, false for real hardware)')

    enable_metrics_arg = DeclareLaunchArgument(
        'enable_metrics',
        default_value='true',
        description='Launch the gesture_metrics_node (CSV + JSON performance logger)')

    inference_mode = LaunchConfiguration('inference_mode')
    camera_id      = LaunchConfiguration('camera_id')
    python_binary  = LaunchConfiguration('python_binary')
    use_sim_time   = LaunchConfiguration('use_sim_time')
    enable_metrics = LaunchConfiguration('enable_metrics')

    # ── Node: gesture_recognition_node (Python 3.10) ──────────────────────────
    recognition_node = Node(
        package='gesture_control',
        executable='gesture_recognition_node',
        name='gesture_recognition_node',
        output='screen',
        parameters=[{
            'inference_mode':     inference_mode,
            'python_binary':      python_binary,
            'backend_script':     backend_script,
            'edgetpu_model_path': edgetpu_model,
            'cpu_model_path':     cpu_model,
            'metadata_path':      metadata,
            'camera_id':          camera_id,
            'publish_rate':       10.0,
            'use_sim_time':       use_sim_time,
        }],
    )

    # ── Node: gesture_commander_node (C++) ────────────────────────────────────
    commander_node = Node(
        package='gesture_control',
        executable='gesture_commander_node',
        name='gesture_commander_node',
        output='screen',
        parameters=[
            gesture_config,
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            {'use_sim_time': use_sim_time},
        ],
    )

    # ── Node: gesture_metrics_node (Python 3.10, optional) ───────────────────
    metrics_node = Node(
        package='gesture_control',
        executable='gesture_metrics_node',
        name='gesture_metrics_node',
        output='screen',
        condition=IfCondition(enable_metrics),
        parameters=[{
            'confidence_threshold': 0.70,
            'log_dir':              os.path.expanduser('~/gesture_metrics'),
            'stats_interval_sec':   30.0,
            'use_sim_time':         use_sim_time,
        }],
    )

    return LaunchDescription([
        inference_mode_arg,
        camera_id_arg,
        python_binary_arg,
        use_sim_time_arg,
        enable_metrics_arg,
        recognition_node,
        commander_node,
        metrics_node,
    ])
