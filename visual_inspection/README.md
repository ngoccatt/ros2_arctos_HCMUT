# visual_inspection

ROS2 package for automated visual inspection of cylinder objects using an eye-in-hand USB camera and a TFLite binary classifier (PASS / FAIL).

## Architecture

```
arctos_bringup  ──►  denso_arm_controller  ──►  UART motors
                          ▲
                          │  FollowJointTrajectory
                          │
          inspection_commander_node (C++)
                    │              │
          /run_inspection      /denso_hand_controller/gripper_cmd
          action server        (GripperCommand)
                    │
          /inspection_result  ◄──  inspection_node (Python 3.10)
                                         │
                                  subprocess pipe (JSON)
                                         │
                              inspection_inference_backend.py
                              (Python 3.9  gesture_env)
                                         │
                                  TFLite model (CPU / EdgeTPU)
```

### Why two Python processes?

`pycoral` (EdgeTPU) requires Python 3.9, but `rclpy` requires Python 3.10. The inference backend runs as a subprocess under `gesture_env` (Python 3.9) and communicates via stdout JSON lines.

---

## Nodes

### `inspection_commander_node` (C++)

Action server `/run_inspection`. Drives the arm through the inspection sequence, collects AI votes, classifies, then sorts.

**State machine:**
```
IDLE
 → OPENING_GRIPPER
 → MOVING_TO_PICK  → PICKING (close gripper)
 → MOVING_TO_INSPECT_P1 → COLLECTING_P1
 → MOVING_TO_INSPECT_P2 → COLLECTING_P2
 → MOVING_TO_INSPECT_P3 → COLLECTING_P3
 → MOVING_TO_INSPECT_P4 → COLLECTING_P4
 → MOVING_TO_INSPECT_P5 → COLLECTING_P5
 → CLASSIFYING
 → MOVING_TO_PRE_PLACE
 → MOVING_TO_SORT_PASS | MOVING_TO_SORT_FAIL
 → release gripper
 → MOVING_HOME
 → IDLE
```

**Key parameters** (set in `config/inspection_config.yaml`):

| Parameter | Default | Description |
|---|---|---|
| `confidence_threshold` | 0.50 | Min AI confidence to count a vote |
| `frames_per_pose` | 5 | Frames collected at each inspection pose |
| `settle_time_sec` | 2.0 | Seconds to wait after arm arrives before collecting |
| `enable_pick` | true | Whether to pick the object before inspecting |
| `gripper_open_pos` | 1.2 | Gripper open position (rad) — calibrated for cylinder |
| `gripper_closed_pos` | 0.45 | Gripper closed/grip position (rad) — calibrated for cylinder |

### `inspection_node` (Python 3.10)

Bridges ROS2 to the inference backend. Spawns `inspection_inference_backend.py` as a subprocess, reads its JSON stdout, and publishes results on `/inspection_result`.

**Key parameters:**

| Parameter | Default | Description |
|---|---|---|
| `inference_mode` | `cpu` | `cpu`, `edgetpu`, or `keras` |
| `camera_id` | `-1` | Camera index (-1 = auto-detect UGREEN) |
| `publish_rate` | 10.0 | Hz |
| `zoom` | 1.0 | Digital centre-crop zoom (1.0 = off) |
| `fail_threshold` | 0.5 | Min FAIL score to predict FAIL |

---

## Waypoints (`config/inspection_config.yaml`)

All joint values are `[X, Y, Z, A, B, C]` in radians.

| Waypoint | Angles [X,Y,Z,A,B,C] | Calibrated | Purpose |
|---|---|---|---|
| `home` | [0°, 0°, 0°, 0°, 0°, 0°] | — | Safe resting pose |
| `pick` | [0°, 32°, 150°, 0°, 0°, 0°] | 2026-05-16 | Above object, pre-grasp |
| `inspect_p1` | [-1°, 30°, 80°, 0°, 65°, 91°] | 2026-05-15 | Side view +90° |
| `inspect_p2` | [-1°, 30°, 80°, 0°, 70°, -10°] | 2026-05-13 | Front face 0° |
| `inspect_p3` | [-1°, 30°, 80°, 0°, 70°, -90°] | 2026-05-13 | Side view −90° |
| `inspect_p4` | [-1°, 30°, 80°, 25°, 70°, 74°] | 2026-05-15 | Tilt up +25° |
| `inspect_p5` | [-1°, 30°, 80°, -20°, 65°, 90°] | 2026-05-15 | Tilt down −20° |
| `pre_place` | [0°, -10°, 128°, 0°, 62°, 90°] | 2026-05-13 | Retract before sort — clears camera |
| `sort_pass` | [-90°, 30°, 120°, 0°, 30°, -1°] | 2026-05-13 | PASS tray |
| `sort_fail` | [90°, 30°, 120°, 0°, 30°, -1°] | 2026-04-10 | FAIL tray |

---

## AI Models (`AI_modules/visual_inspection/models/`)

| File | Description |
|---|---|
| `inspection_model.h5` | Keras MobileNetV2 (float32) |
| `inspection_model_int8.tflite` | INT8 quantized TFLite — CPU inference |
| `inspection_model_int8_edgetpu_src_edgetpu.tflite` | EdgeTPU-compiled — Coral USB |
| `model_metadata.json` | Class labels, input shape, training metrics |

**Current model performance (test set, 368 images — balanced 188 FAIL / 180 PASS):**
```
Accuracy      : 99.73 %
FAIL recall   : 99 %  (1 missed defect out of 188)
PASS recall   : 100 % (0 false rejects out of 180)
```

Trained with MobileNetV2 + focal loss (γ=2.0) + label smoothing 0.1.
See `~/Coding/inspection/README.md` for full training details.

Classes: **PASS** (index 1), **FAIL** (index 0)

---

## Running

### Prerequisites

Hardware bringup must be running:
```bash
ros2 launch arctos_bringup arctos_bringup.launch.py
```

### Launch inspection pipeline

```bash
# CPU inference (no Coral needed)
ros2 launch visual_inspection visual_inspection.launch.py \
  use_sim_time:=false inference_mode:=cpu

# EdgeTPU (Coral USB plugged in)
ros2 launch visual_inspection visual_inspection.launch.py \
  use_sim_time:=false inference_mode:=edgetpu
```

### Trigger an inspection

```bash
ros2 action send_goal /run_inspection visual_inspection/action/RunInspection \
  "{object_id: 'part_001'}"
```

### Monitor

```bash
ros2 topic echo /inspection_result        # AI votes per frame
ros2 topic echo /run_inspection/_action/feedback  # state machine progress
```

### `inspection_metrics_node` (Python, optional)

Logs per-session PASS/FAIL vote statistics. Enable with `enable_metrics:=true`.

---

## Empty-frame handling

When no object is in the camera field of view the backend outputs `NO_OBJECT` instead
of running inference (frames with grayscale std-dev < 8 are skipped). This prevents
an empty white background being classified as PASS.
The commander node ignores `NO_OBJECT` frames automatically because their confidence
is 0.0, which is below `confidence_threshold`.

---

## Dataset Collection

Collect new training images using the same inspection poses:

```bash
cd AI_modules/visual_inspection

# PASS samples
python3 collect_inspection_dataset.py \
  --label PASS --sample-id s01 \
  --camera-id 6 --images-per-pose 30 --zoom 1.5

# FAIL samples (scratch defect)
python3 collect_inspection_dataset.py \
  --label FAIL --defect-type scratch --sample-id s01 \
  --camera-id 6 --images-per-pose 30 --zoom 1.5
```

The script reads waypoints directly from `inspection_config.yaml` — no code changes needed after re-calibration.

### Retrain after new data

```bash
cd AI_modules/visual_inspection
python3 prepare_dataset.py       # re-split train/val/test
python3 train.py                 # retrain MobileNetV2
python3 convert_to_tflite.py     # INT8 TFLite + EdgeTPU compile
```

---

## Gripper Calibration

Safe range for cylinder object: **0.45 rad (closed) … 1.2 rad (open)**.

To find your safe limits interactively:
```bash
# Test a specific position (rad)
ros2 action send_goal /denso_hand_controller/gripper_cmd \
  control_msgs/action/GripperCommand \
  "{command: {position: 0.8, max_effort: 0.0}}"

# Update at runtime without restarting
ros2 param set /inspection_commander_node gripper_open_pos 1.2
ros2 param set /inspection_commander_node gripper_closed_pos 0.45
```

Then save in `config/inspection_config.yaml`.

---

## Files

```
visual_inspection/
├── src/
│   └── inspection_commander_node.cpp   # C++ state machine
├── visual_inspection/
│   ├── inspection_node.py              # Python 3.10 ROS2 bridge
│   └── inspection_metrics_node.py      # Optional metrics logger
├── scripts/
│   └── inspection_inference_backend.py # Python 3.9 TFLite runner
├── config/
│   └── inspection_config.yaml          # Waypoints + parameters
├── launch/
│   └── visual_inspection.launch.py
├── msg/
│   └── InspectionResult.msg
└── action/
    └── RunInspection.action
```
