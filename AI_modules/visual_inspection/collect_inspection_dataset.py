#!/usr/bin/env python3
"""
collect_inspection_dataset.py
Automatic dataset collection for visual inspection retraining.

Drives the robot arm through inspection poses P1–P5 using the same joint
values stored in inspection_config.yaml, captures images at each pose,
and saves them in the dataset/raw/{PASS|FAIL}/ directory with the same
file-naming convention used by the original collect_dataset.py.

Must be run inside a sourced ROS2 workspace (Python 3.10 environment).
MoveIt2 does NOT need to be running — uses FollowJointTrajectory directly.

Usage examples
--------------
# Collect PASS samples for a new sample s02
python3 collect_inspection_dataset.py --label PASS --sample-id s02

# Collect FAIL samples (scratch defect) for sample s10
python3 collect_inspection_dataset.py --label FAIL --defect-type scratch --sample-id s10

# Only collect at P1 and P3, 20 images each, 0.8 s interval
python3 collect_inspection_dataset.py --label PASS --sample-id s02 \\
    --poses p1 p3 --images-per-pose 20 --capture-interval 0.8

Output files (example)
----------------------
dataset/raw/PASS/PASS_none_s02_P1_001.jpg
dataset/raw/PASS/PASS_none_s02_P1_002.jpg
...
dataset/raw/FAIL/FAIL_scratch_s10_P2_001.jpg
"""

import os
import sys
import time
import argparse
import glob as _glob
import yaml
import cv2
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory, GripperCommand
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

# ── Constants ──────────────────────────────────────────────────────────────────

JOINT_NAMES = ['X_joint', 'Y_joint', 'Z_joint', 'A_joint', 'B_joint', 'C_joint']
CONTROLLER_ACTION = '/denso_arm_controller/follow_joint_trajectory'
GRIPPER_ACTION    = '/denso_hand_controller/gripper_cmd'

# Duration for the arm to complete the move (seconds)
# Keep generous so the controller doesn't reject the goal
MOVE_DURATION_SEC = 5.0

CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    '../../visual_inspection/config/inspection_config.yaml'
)

ALL_POSES = ['p1', 'p2', 'p3', 'p4', 'p5']


# ── Camera helpers ─────────────────────────────────────────────────────────────

def _find_camera():
    prefer = ('ugreen', 'ultra hd', '4k')
    for p in sorted(_glob.glob('/sys/class/video4linux/video*/name')):
        try:
            name = open(p).read().strip().lower()
            idx  = int(os.path.basename(os.path.dirname(p)).replace('video', ''))
        except Exception:
            continue
        if any(k in name for k in prefer):
            return idx
    for idx in range(8):
        c = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if c.isOpened():
            c.release()
            return idx
    return None


# ── ROS2 node ──────────────────────────────────────────────────────────────────

class DatasetCollectorNode(Node):
    def __init__(self):
        super().__init__('inspection_dataset_collector')
        self._arm_client     = ActionClient(self, FollowJointTrajectory, CONTROLLER_ACTION)
        self._gripper_client = ActionClient(self, GripperCommand, GRIPPER_ACTION)

        self.get_logger().info(f'Waiting for {CONTROLLER_ACTION}...')
        if not self._arm_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error('Arm controller action server not available.')
            raise RuntimeError('Arm controller not available')

        self.get_logger().info(f'Waiting for {GRIPPER_ACTION}...')
        if not self._gripper_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().warn('Gripper action server not available — gripper commands will be skipped.')

        self.get_logger().info('Controllers ready.')

    def move_to_joints(self, joint_values: list, label: str = '') -> bool:
        """Send a FollowJointTrajectory goal and block until done."""
        point = JointTrajectoryPoint()
        point.positions = [float(v) for v in joint_values]
        point.velocities = [0.0] * len(JOINT_NAMES)
        point.time_from_start = Duration(
            sec=int(MOVE_DURATION_SEC),
            nanosec=int((MOVE_DURATION_SEC % 1) * 1e9))

        traj = JointTrajectory()
        traj.joint_names = JOINT_NAMES
        traj.points = [point]

        goal = FollowJointTrajectory.Goal()
        goal.trajectory = traj

        self.get_logger().info(f'Moving to {label}  joints={[round(v,4) for v in joint_values]}')
        future = self._arm_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error(f'Goal rejected for {label}')
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        return True

    def send_gripper(self, position: float, max_effort: float = 0.0):
        """Send a GripperCommand goal and block until done."""
        if not self._gripper_client.server_is_ready():
            self.get_logger().warn('Gripper server not ready — skipping.')
            return
        goal = GripperCommand.Goal()
        goal.command.position   = position
        goal.command.max_effort = max_effort
        self.get_logger().info(f'Gripper → {position:.4f} rad')
        future = self._gripper_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)
        goal_handle = future.result()
        if goal_handle.accepted:
            rclpy.spin_until_future_complete(self, goal_handle.get_result_async())
        time.sleep(0.8)   # let gripper physically settle


# ── Main collection logic ──────────────────────────────────────────────────────

def load_config(config_path: str) -> dict:
    resolved = os.path.abspath(config_path)
    if not os.path.exists(resolved):
        raise FileNotFoundError(f'Config not found: {resolved}')
    with open(resolved) as f:
        cfg = yaml.safe_load(f)
    return cfg['inspection_commander_node']['ros__parameters']


def collect(args):
    # ── Load config ───────────────────────────────────────────────────────────
    cfg = load_config(args.config)
    waypoints          = cfg['waypoints']
    gripper_open_pos   = cfg.get('gripper_open_pos',   1.48)
    gripper_closed_pos = cfg.get('gripper_closed_pos', 0.02)
    pose_map = {
        'p1': ('inspect_p1', 'P1'),
        'p2': ('inspect_p2', 'P2'),
        'p3': ('inspect_p3', 'P3'),
        'p4': ('inspect_p4', 'P4'),
        'p5': ('inspect_p5', 'P5'),
    }

    selected = [p.lower() for p in args.poses]
    for p in selected:
        key = pose_map[p][0]
        if key not in waypoints:
            raise KeyError(f'Waypoint "{key}" not found in config.')

    # ── Output directory ───────────────────────────────────────────────────────
    out_dir = os.path.join(args.output_dir, args.label)
    os.makedirs(out_dir, exist_ok=True)

    # ── Camera ────────────────────────────────────────────────────────────────
    cam_idx = args.camera_id if args.camera_id >= 0 else _find_camera()
    if cam_idx is None:
        print('ERROR: No camera found. Specify --camera-id explicitly.')
        sys.exit(1)
    cap = cv2.VideoCapture(cam_idx, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        print(f'ERROR: Cannot open camera {cam_idx}.')
        sys.exit(1)
    print(f'Camera opened on index {cam_idx}')

    # ── Zoom ──────────────────────────────────────────────────────────────────
    zoom = max(1.0, args.zoom)

    def apply_zoom(frame):
        if zoom <= 1.0:
            return frame
        h, w = frame.shape[:2]
        ch, cw = int(h / zoom), int(w / zoom)
        y0, x0 = (h - ch) // 2, (w - cw) // 2
        return cv2.resize(frame[y0:y0 + ch, x0:x0 + cw], (w, h),
                          interpolation=cv2.INTER_LINEAR)

    # ── ROS2 node ──────────────────────────────────────────────────────────────
    rclpy.init()
    node = DatasetCollectorNode()

    total_saved = 0
    session_label = f'{args.label}_{args.defect_type}_{args.sample_id}'

    print(f'\n{"=" * 60}')
    print(f'Session: {session_label}')
    print(f'Poses:   {selected}')
    print(f'Images per pose: {args.images_per_pose}')
    print(f'Zoom: {zoom}x')
    print(f'Output: {out_dir}')
    print('=' * 60)

    try:
        # ── Pick: open gripper first, then approach and grasp ─────────────────
        print('\n[PICK] Opening gripper before approach...')
        node.send_gripper(gripper_open_pos)
        print('\n[PICK] Moving to pick pose...')
        node.move_to_joints(waypoints['pick'], label='pick')
        time.sleep(cfg.get('settle_time_sec', 2.0))
        print(f'[PICK] Closing gripper → {gripper_closed_pos:.4f} rad')
        node.send_gripper(gripper_closed_pos)
        print('[PICK] Object grasped. Starting inspection poses...')

        for pose_key in selected:
            wp_name, pose_label = pose_map[pose_key]
            joints = waypoints[wp_name]

            # ── Move arm ──────────────────────────────────────────────────────
            print(f'\n[{pose_label}] Moving arm...')
            node.move_to_joints(joints, label=wp_name)

            # ── Settle ────────────────────────────────────────────────────────
            print(f'[{pose_label}] Settling {args.settle_time:.1f}s...')
            deadline = time.time() + args.settle_time
            while time.time() < deadline:
                ret, frame = cap.read()
                if ret:
                    frame = apply_zoom(frame)
                    remaining = max(0.0, deadline - time.time())
                    cv2.putText(frame,
                                f'Settling... {remaining:.1f}s  [{pose_label}]',
                                (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                                (0, 200, 255), 2)
                    cv2.imshow('Dataset Collector', frame)
                cv2.waitKey(30)

            # ── Capture ───────────────────────────────────────────────────────
            print(f'[{pose_label}] Capturing {args.images_per_pose} images...')
            captured = 0
            while captured < args.images_per_pose:
                ret, frame = cap.read()
                if not ret:
                    print(f'  WARNING: camera read failed at image {captured + 1}')
                    time.sleep(0.1)
                    continue

                frame = apply_zoom(frame)
                # Filename: PASS_none_s02_P1_001.jpg
                idx = total_saved + captured + 1
                filename = (
                    f'{args.label}_{args.defect_type}_{args.sample_id}'
                    f'_{pose_label}_{captured + 1:03d}.jpg'
                )
                save_path = os.path.join(out_dir, filename)
                cv2.imwrite(save_path, frame)
                captured += 1

                # Overlay
                text = (f'[{pose_label}] {captured}/{args.images_per_pose}  '
                        f'Saved: {filename}')
                display = frame.copy()
                cv2.putText(display, text, (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow('Dataset Collector', display)
                cv2.waitKey(1)

                print(f'  [{captured:3d}/{args.images_per_pose}] {filename}')
                time.sleep(args.capture_interval)

            total_saved += captured
            print(f'[{pose_label}] Done — {captured} images saved.')

        # ── Release: return to pick pose and open gripper ─────────────────────
        print('\n[RELEASE] Returning to pick pose to release object...')
        node.move_to_joints(waypoints['pick'], label='pick')
        time.sleep(cfg.get('settle_time_sec', 2.0))
        print(f'[RELEASE] Opening gripper → {gripper_open_pos:.4f} rad')
        node.send_gripper(gripper_open_pos)

        # ── Return home ───────────────────────────────────────────────────────
        print('[HOME] Returning to home...')
        node.move_to_joints(waypoints['home'], label='home')

    finally:
        cap.release()
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

    print(f'\n{"=" * 60}')
    print(f'Collection complete.')
    print(f'Total images saved: {total_saved}')
    print(f'Output directory:   {out_dir}')
    print(f'\nNext steps:')
    print(f'  1. Verify images in {out_dir}')
    print(f'  2. python3 prepare_dataset.py    # re-split train/val/test')
    print(f'  3. python3 train.py              # retrain MobileNetV2')
    print(f'  4. python3 convert_to_tflite.py  # convert to TFLite + EdgeTPU')
    print('=' * 60)


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Automatic inspection dataset collection at P1–P5 poses.')

    parser.add_argument('--label', choices=['PASS', 'FAIL'], required=True,
                        help='Ground truth label for the object being collected.')
    parser.add_argument('--defect-type', default='none',
                        help='Defect name for FAIL objects (e.g. scratch, dent, blob). '
                             'Use "none" for PASS objects. (default: none)')
    parser.add_argument('--sample-id', default='s01',
                        help='Sample identifier, e.g. s01, s02. (default: s01)')
    parser.add_argument('--poses', nargs='+', default=ALL_POSES,
                        choices=ALL_POSES,
                        help='Which poses to collect. (default: p1 p2 p3 p4 p5)')
    parser.add_argument('--images-per-pose', type=int, default=10,
                        help='Number of images captured at each pose. (default: 30)')
    parser.add_argument('--capture-interval', type=float, default=0.5,
                        help='Seconds between captures at each pose. (default: 0.5)')
    parser.add_argument('--settle-time', type=float, default=2.0,
                        help='Seconds to wait after arm arrives before capturing. '
                             '(default: 2.0)')
    parser.add_argument('--zoom', type=float, default=1.5,
                        help='Digital zoom factor (1.0 = no zoom, 2.0 = 2x, etc.). '
                             '(default: 1.0)')
    parser.add_argument('--camera-id', type=int, default=6,
                        help='Camera device index. (default: 6)')
    parser.add_argument('--output-dir', default='dataset/raw',
                        help='Root dataset directory. (default: dataset/raw)')
    parser.add_argument('--config',
                        default=CONFIG_PATH,
                        help='Path to inspection_config.yaml. '
                             '(default: auto-resolved relative path)')

    args = parser.parse_args()

    # Validate
    if args.label == 'FAIL' and args.defect_type == 'none':
        print('WARNING: --label FAIL but --defect-type is "none". '
              'Consider setting --defect-type scratch/dent/blob/...')

    collect(args)
