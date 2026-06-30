# gesture_control

ROS2 package for gesture-based robot arm control using an eye-in-hand USB camera, a TFLite classifier, and MoveIt2.

## Architecture

```
Camera (USB)
    │
gesture_inference_backend.py   ← Python 3.9 (gesture_env)
    │  stdout JSON lines
gesture_recognition_node.py    ← Python 3.10 (ROS2)
    │  /gesture_detection  (GestureDetection.msg)
gesture_commander_node (C++)
    │
    ├── MoveGroupInterface  → denso_arm_controller
    └── GripperCommand      → denso_hand_controller
```

### Why two Python processes?

`pycoral` (EdgeTPU) requires Python 3.9, but `rclpy` requires Python 3.10. The inference backend runs as a subprocess under `gesture_env` Python 3.9 and communicates via stdout JSON lines (~0.1 ms latency).

---

## Gesture Mapping

| Gesture | Action |
|---|---|
| `thumbs_up` | MoveIt2 named pose `home` (all joints = 0) |
| `point` | Y_joint += 0.3 rad (raise arm) |
| `open` | Open gripper → 0.015 rad |
| `fist` | Close gripper → 0.0 rad |
| `none` | `move_group.stop()` |

---

## Nodes

### `gesture_recognition_node` (Python 3.10)

Spawns the inference backend subprocess, reads JSON output, and publishes to `/gesture_detection`.

### `gesture_commander_node` (C++)

Subscribes to `/gesture_detection`, applies stability filter, and sends motion commands via MoveGroupInterface.

---

## Parameters (`config/gesture_config.yaml`)

| Parameter | Default | Description |
|---|---|---|
| `confidence_threshold` | 0.7 | Min confidence to accept a gesture vote |
| `stability_frames` | 5 | Consecutive identical frames before executing |
| `cooldown` | 2.0 s | Minimum time between successive commands |
| `inference_mode` | `cpu` | `cpu` or `edgetpu` |

---

## AI Models (`AI_modules/gesture_recognition/models/`)

| File | Description |
|---|---|
| `gesture_retrained.h5` | Keras float32 model |
| `gesture_retrained_int8_edgetpu.tflite` | EdgeTPU-compiled INT8 model |

Classes: `fist`, `open`, `point`, `thumbs_up`, `none`

Inference latency: **5–10 ms** (EdgeTPU) / **30–50 ms** (CPU)

---

## Running

Hardware bringup must be running first:
```bash
ros2 launch arctos_bringup arctos_bringup.launch.py
```

### CPU inference (no Coral needed)
```bash
ros2 launch gesture_control gesture_control.launch.py inference_mode:=cpu
```

### EdgeTPU inference (Coral USB plugged in)
```bash
ros2 launch gesture_control gesture_control.launch.py inference_mode:=edgetpu
```

### Launch arguments

| Argument | Default | Description |
|---|---|---|
| `inference_mode` | `cpu` | `cpu` or `edgetpu` |
| `camera_id` | `0` | Camera device index |
| `python_binary` | `~/.pyenv/versions/gesture_env/bin/python` | Python 3.9 interpreter |

### Monitor topics
```bash
ros2 topic echo /gesture_detection   # raw inference output
ros2 topic echo /gesture_command     # commands sent to robot
```

---

## Files

```
gesture_control/
├── gesture_control/
│   └── gesture_recognition_node.py    # Python 3.10 ROS2 bridge node
├── src/
│   └── gesture_commander_node.cpp     # C++ MoveIt2 commander
├── scripts/
│   └── gesture_inference_backend.py   # Python 3.9 TFLite runner
├── config/
│   └── gesture_config.yaml
├── launch/
│   └── gesture_control.launch.py
└── msg/
    └── GestureDetection.msg
```

---

## Notes

- `ros-humble-moveit-py` does not exist — the commander uses C++ `MoveGroupInterface`.
- Do **not** call `ament_python_install_package(gesture_control)` alongside `rosidl_generate_interfaces` in CMakeLists — rosidl registers the Python package internally, causing a duplicate target error.
