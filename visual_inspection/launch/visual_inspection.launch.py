"""
visual_inspection.launch.py

Launches the full visual inspection pipeline:
  1. inspection_node        — Python 3.10 bridge node, publishes /inspection_result
  2. inspection_commander_node — C++ state machine, exposes /run_inspection action

Launch arguments:
  inference_mode   edgetpu | cpu | keras   (default: cpu)
  camera_id        int (-1 = auto-detect)  (default: -1)
  python_binary    path to Python 3.9 interpreter
  use_sim_time     true | false            (default: false)

Sim note:
  When use_sim_time:=true the commander node loads gz_arctos.urdf.xacro so that
  MoveGroupInterface connects correctly to the Gazebo move_group instance.
  Run the Gazebo stack first:
    ros2 launch arctos_bringup gz_arctos_bringup.launch.py
  Then:
    ros2 launch visual_inspection visual_inspection.launch.py use_sim_time:=true
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def launch_setup(context, *args, **kwargs):
    pkg_share = get_package_share_directory('visual_inspection')

    enable_metrics = LaunchConfiguration('enable_metrics').perform(context).lower() == 'true'

    # ── Resolve paths ──────────────────────────────────────────────────────────
    backend_script = os.path.join(pkg_share, 'scripts', 'inspection_inference_backend.py')

    workspace_root = os.path.normpath(os.path.join(pkg_share, '..', '..', '..', '..'))
    ai_models = os.path.join(
        workspace_root, 'src', 'ros2_arctos_HCMUT',
        'AI_modules', 'visual_inspection', 'models'
    )
    edgetpu_model = os.path.join(ai_models, 'inspection_model_int8_edgetpu_src_edgetpu.tflite')
    cpu_model     = os.path.join(ai_models, 'inspection_model_int8.tflite')
    keras_model   = os.path.join(ai_models, 'inspection_model.h5')
    metadata      = os.path.join(ai_models, 'model_metadata.json')

    inspection_config = os.path.join(pkg_share, 'config', 'inspection_config.yaml')

    # ── Resolve launch arguments at runtime ────────────────────────────────────
    use_sim_time_str = LaunchConfiguration('use_sim_time').perform(context)
    use_sim_time_bool = use_sim_time_str.lower() == 'true'

    inference_mode = LaunchConfiguration('inference_mode')
    camera_id      = LaunchConfiguration('camera_id')
    python_binary  = LaunchConfiguration('python_binary')
    zoom           = LaunchConfiguration('zoom')

    # ── MoveIt2 robot description — pick URDF based on sim vs real ─────────────
    urdf_file = 'config/gz_denso.urdf.xacro' if use_sim_time_bool else 'config/denso.urdf.xacro'
    moveit_config = (
        MoveItConfigsBuilder("denso", package_name="denso_moveit_config")
        .robot_description(file_path=urdf_file)
        .robot_description_semantic(file_path="config/denso.srdf")
        .to_moveit_configs()
    )

    # ── Node: inspection_node (Python 3.10 bridge) ─────────────────────────────
    inspection_node = Node(
        package='visual_inspection',
        executable='inspection_node',
        name='inspection_node',
        output='screen',
        parameters=[{
            'inference_mode':     inference_mode,
            'python_binary':      python_binary,
            'backend_script':     backend_script,
            'edgetpu_model_path': edgetpu_model,
            'cpu_model_path':     cpu_model,
            'keras_model_path':   keras_model,
            'metadata_path':      metadata,
            'camera_id':          camera_id,
            'publish_rate':       10.0,
            'zoom':               zoom,
            'fail_threshold':     LaunchConfiguration('fail_threshold'),
            'use_sim_time':       use_sim_time_bool,
        }],
    )

    # ── Node: inspection_commander_node (C++) ──────────────────────────────────
    commander_node = Node(
        package='visual_inspection',
        executable='inspection_commander_node',
        name='inspection_commander_node',
        output='screen',
        parameters=[
            inspection_config,
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            {'use_sim_time': use_sim_time_bool},
        ],
    )

    nodes = [inspection_node, commander_node]

    if enable_metrics:
        metrics_node = Node(
            package='visual_inspection',
            executable='inspection_metrics_node',
            name='inspection_metrics_node',
            output='screen',
            parameters=[{
                'confidence_threshold': 0.70,
                'stats_interval_sec':   60.0,
                'use_sim_time':         use_sim_time_bool,
            }],
        )
        nodes.append(metrics_node)

    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'inference_mode',
            default_value='cpu',
            description="Inference backend: 'edgetpu', 'cpu', or 'keras'"),

        DeclareLaunchArgument(
            'camera_id',
            default_value='-1',
            description='Camera device index (-1 = auto-detect UGREEN)'),

        DeclareLaunchArgument(
            'python_binary',
            default_value=os.path.expanduser('~/.pyenv/versions/gesture_env/bin/python'),
            description='Python 3.9 interpreter with TensorFlow/pycoral installed'),

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock (true for Gazebo, false for real hardware)'),

        DeclareLaunchArgument(
            'zoom',
            default_value='1.0',
            description='Digital center-crop zoom factor (1.0=off, 2.0=2x, 3.0=3x). '
                        'Crops the centre 1/zoom of the frame before inference.'),

        DeclareLaunchArgument(
            'fail_threshold',
            default_value='0.5',
            description='Min FAIL score to predict FAIL (0.5=argmax, raise to 0.60-0.70 to reduce false rejections)'),

        DeclareLaunchArgument(
            'enable_metrics',
            default_value='false',
            description='Launch inspection_metrics_node for system-level performance logging'),

        OpaqueFunction(function=launch_setup),
    ])
