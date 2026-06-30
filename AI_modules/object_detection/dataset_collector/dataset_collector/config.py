"""
All configurable parameters for the dataset_collector package.
Edit this file before running the collection node.
"""

# ---------------------------------------------------------------------------
# Robot joint names — must match the controller / URDF in this workspace.
# Order: X, Y, Z, A, B, C  (same order as denso_arm_controller).
# ---------------------------------------------------------------------------
JOINT_NAMES = [
    "X_joint",
    "Y_joint",
    "Z_joint",
    "A_joint",
    "B_joint",
    "C_joint",
]

# ---------------------------------------------------------------------------
# Robot poses — joint angles in radians for each collection phase.
#   Phase A = robot far from object (wide view)
#   Phase B = robot at mid distance
#   Phase C = robot close to object (fine detail / grasp approach)
# ---------------------------------------------------------------------------
JOINT_POSES = {
    "A": [0.0, 0.0,    1.5708, 0.0, 1.5708, -0.1571],  # far  (Z=90°,  B=90°)
    # "B": [0.0, 0.1222, 2.1817, 0.0, 0.8378, -0.1571],  # mid  (Z=125°, B=48°)
    # "C": [0.0, 0.5236, 2.2689, 0.0, 0.3491, -0.1571],  # near (Z=130°, B=20°)
}

# ---------------------------------------------------------------------------
# Camera — eye-in-hand UGREEN USB webcam, read directly via OpenCV.
# NOT a ROS2 topic.  Change CAMERA_INDEX if /dev/video0 is not the webcam.
# ---------------------------------------------------------------------------
CAMERA_INDEX = 4        # TODO: confirm USB camera index on target machine
CAPTURE_WIDTH = 640
CAPTURE_HEIGHT = 480

# ---------------------------------------------------------------------------
# Capture settings
# ---------------------------------------------------------------------------
IMAGES_PER_PHASE = 60   # Number of images to capture at each pose (60 × 1 = 60 total)
CAPTURE_INTERVAL = 1.5  # Seconds between captures (allow time to reposition cube)

# ---------------------------------------------------------------------------
# Robot motion — sends joint trajectories directly to the arm controller.
# No MoveIt2 / pymoveit2 required.
# ---------------------------------------------------------------------------
CONTROLLER_ACTION = "/denso_arm_controller/follow_joint_trajectory"
MOVE_TIMEOUT = 10.0   # Seconds allocated for the robot to reach each pose

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
from pathlib import Path as _Path  # noqa: E402

# Absolute path — images always land here regardless of where ros2 run is invoked.
# Change this to any directory you prefer.
DATASET_DIR = _Path.home() / "ros2_dataset_collector"
