"""
capture_node.py — ROS2 node that drives the robot to each collection pose
and captures images from the eye-in-hand USB webcam.

Motion backend: FollowJointTrajectory action client → denso_arm_controller
No external Python dependencies beyond standard ROS2 packages.
"""

import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
import rclpy
from builtin_interfaces.msg import Duration
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

from dataset_collector.config import (
    CAMERA_INDEX,
    CAPTURE_HEIGHT,
    CAPTURE_INTERVAL,
    CAPTURE_WIDTH,
    CONTROLLER_ACTION,
    DATASET_DIR,
    IMAGES_PER_PHASE,
    JOINT_NAMES,
    JOINT_POSES,
    MOVE_TIMEOUT,
)


class DatasetCaptureNode(Node):
    """
    Moves the robot to Phase A / B / C poses via FollowJointTrajectory,
    then captures IMAGES_PER_PHASE frames from the USB webcam at each pose.
    """

    def __init__(self) -> None:
        super().__init__("dataset_capture_node")

        # ── Joint trajectory action client ────────────────────────────────────
        self._action_client = ActionClient(
            self, FollowJointTrajectory, CONTROLLER_ACTION
        )
        self.get_logger().info(
            f"Waiting for action server: {CONTROLLER_ACTION} ..."
        )
        if not self._action_client.wait_for_server(timeout_sec=10.0):
            raise RuntimeError(
                f"Action server not available: {CONTROLLER_ACTION}\n"
                "Make sure the robot bringup is running."
            )
        self.get_logger().info("Action server ready.")

        # ── Camera ───────────────────────────────────────────────────────────
        self._cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self._cap.isOpened():
            self.get_logger().error(
                f"Cannot open camera at index {CAMERA_INDEX}. "
                "# TODO: check CAMERA_INDEX in config.py"
            )
            raise RuntimeError("Camera unavailable — check CAMERA_INDEX in config.py")

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_HEIGHT)
        # Discard the first several frames — USB cameras often return black
        # frames until the sensor auto-exposure stabilises (~10 frames).
        for _ in range(10):
            self._cap.read()
        self.get_logger().info(
            f"Camera opened: index={CAMERA_INDEX} "
            f"resolution={CAPTURE_WIDTH}x{CAPTURE_HEIGHT}"
        )

        # ── Dataset directories ───────────────────────────────────────────────
        self._dataset_root = Path(DATASET_DIR)
        for phase in JOINT_POSES:
            (self._dataset_root / f"phase_{phase}").mkdir(parents=True, exist_ok=True)
        self.get_logger().info(f"Dataset root: {self._dataset_root}")

    # ── Public entry-point ────────────────────────────────────────────────────

    def run_collection(self) -> None:
        """Execute the full A → B → C collection sequence."""
        counts: dict[str, int] = {}

        for phase, joint_angles in JOINT_POSES.items():
            self.get_logger().info(f"Moving to Phase {phase} pose...")
            if not self._move_to_joints(joint_angles):
                self.get_logger().error(
                    f"Motion failed for Phase {phase}. Stopping collection."
                )
                return

            self.get_logger().info(
                f"Arrived at Phase {phase}. Starting capture "
                f"({IMAGES_PER_PHASE} images)..."
            )
            counts[phase] = self._capture_phase(phase)

        self.get_logger().info("Dataset collection complete.")
        for phase, count in counts.items():
            phase_dir = self._dataset_root / f"phase_{phase}"
            self.get_logger().info(f"  Phase {phase}: {count} images → {phase_dir}")
        self.get_logger().info(
            "Next step: annotate with LabelImg, export as COCO JSON"
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _move_to_joints(self, joint_angles: list[float]) -> bool:
        """Send a single-point joint trajectory and block until complete."""
        point = JointTrajectoryPoint()
        point.positions = joint_angles
        point.velocities = [0.0] * len(joint_angles)
        point.time_from_start = Duration(sec=int(MOVE_TIMEOUT), nanosec=0)

        trajectory = JointTrajectory()
        trajectory.joint_names = JOINT_NAMES
        trajectory.points = [point]

        goal = FollowJointTrajectory.Goal()
        goal.trajectory = trajectory

        done_event = threading.Event()
        result_holder: list = [None]

        def feedback_cb(_feedback):
            pass

        def result_cb(future):
            result_holder[0] = future.result()
            done_event.set()

        send_future = self._action_client.send_goal_async(
            goal, feedback_callback=feedback_cb
        )

        accepted_event = threading.Event()
        goal_handle_holder: list = [None]

        def accepted_cb(future):
            goal_handle_holder[0] = future.result()
            accepted_event.set()

        send_future.add_done_callback(accepted_cb)

        if not accepted_event.wait(timeout=10.0):
            self.get_logger().error("Goal not accepted within 10 s.")
            return False

        goal_handle = goal_handle_holder[0]
        if not goal_handle.accepted:
            self.get_logger().error("Goal was rejected by the controller.")
            return False

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(result_cb)

        if not done_event.wait(timeout=MOVE_TIMEOUT + 5.0):
            self.get_logger().error("Motion timed out.")
            return False

        result = result_holder[0]
        if result.result.error_code != FollowJointTrajectory.Result.SUCCESSFUL:
            self.get_logger().error(
                f"Controller returned error code: {result.result.error_code}"
            )
            return False

        return True

    def _capture_phase(self, phase: str) -> int:
        """Capture IMAGES_PER_PHASE frames, show live preview, and save them."""
        phase_dir = self._dataset_root / f"phase_{phase}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        captured = 0
        window = f"Dataset Capture Phase {phase} (Q to abort)"

        for seq in range(1, IMAGES_PER_PHASE + 1):
            ret, frame = self._cap.read()
            if not ret:
                self.get_logger().warning(
                    f"Phase {phase}: failed to read frame {seq}, skipping."
                )
                time.sleep(CAPTURE_INTERVAL)
                continue

            overlay = frame.copy()
            cv2.putText(
                overlay,
                f"Phase {phase}  [{captured + 1}/{IMAGES_PER_PHASE}]",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow(window, overlay)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                self.get_logger().warning("Capture aborted by user (Q pressed).")
                cv2.destroyWindow(window)
                return captured

            filename = f"{phase}_{timestamp}_{seq:04d}.jpg"
            cv2.imwrite(str(phase_dir / filename), frame)
            captured += 1
            self.get_logger().info(
                f"Phase {phase}: {captured}/{IMAGES_PER_PHASE} images captured"
            )
            time.sleep(CAPTURE_INTERVAL)

        cv2.destroyWindow(window)
        return captured

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def destroy_node(self) -> None:
        if self._cap.isOpened():
            self._cap.release()
        cv2.destroyAllWindows()
        super().destroy_node()


# ── Entry-point ───────────────────────────────────────────────────────────────


def main(args=None) -> None:
    rclpy.init(args=args)

    try:
        node = DatasetCaptureNode()
    except RuntimeError:
        rclpy.shutdown()
        return

    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)

    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    try:
        node.run_collection()
    finally:
        node.destroy_node()
        rclpy.shutdown()
        spin_thread.join(timeout=2.0)


if __name__ == "__main__":
    main()
