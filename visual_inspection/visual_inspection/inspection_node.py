#!/usr/bin/env python3
"""
inspection_node.py  —  ROS2 node (Python 3.10)

Spawns inspection_inference_backend.py as a subprocess under the gesture_env
Python 3.9.17 interpreter, reads JSON results from its stdout, and publishes
them as InspectionResult messages on /inspection_result.

Topics published:
    /inspection_result  (visual_inspection/msg/InspectionResult)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Header
from visual_inspection.msg import InspectionResult

import subprocess
import threading
import queue
import json
import os
import sys


class InspectionNode(Node):
    def __init__(self):
        super().__init__('inspection_node')

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter('inference_mode', 'cpu')
        self.declare_parameter(
            'python_binary',
            os.path.expanduser('~/.pyenv/versions/gesture_env/bin/python')
        )
        self.declare_parameter('backend_script', '')
        self.declare_parameter('edgetpu_model_path', '')
        self.declare_parameter('cpu_model_path', '')
        self.declare_parameter('keras_model_path', '')
        self.declare_parameter('metadata_path', '')
        self.declare_parameter('camera_id', -1)   # -1 = auto-detect
        self.declare_parameter('publish_rate', 10.0)
        self.declare_parameter('zoom', 1.0)       # digital center-crop zoom factor
        self.declare_parameter('fail_threshold', 0.5)  # min FAIL score to predict FAIL

        self.inference_mode    = self.get_parameter('inference_mode').value
        self.python_binary     = self.get_parameter('python_binary').value
        self.backend_script    = self.get_parameter('backend_script').value
        edgetpu_model          = self.get_parameter('edgetpu_model_path').value
        cpu_model              = self.get_parameter('cpu_model_path').value
        keras_model            = self.get_parameter('keras_model_path').value
        self.metadata_path     = self.get_parameter('metadata_path').value
        self.camera_id         = self.get_parameter('camera_id').value
        publish_rate           = self.get_parameter('publish_rate').value
        self.zoom              = self.get_parameter('zoom').value
        self.fail_threshold    = self.get_parameter('fail_threshold').value

        # Select model path based on mode
        mode_model = {
            'edgetpu': edgetpu_model,
            'cpu':     cpu_model,
            'keras':   keras_model,
        }
        self.model_path = mode_model.get(self.inference_mode, cpu_model)

        # Validate
        for name, value in [
            ('backend_script', self.backend_script),
            ('model_path',     self.model_path),
            ('metadata_path',  self.metadata_path),
        ]:
            if not value:
                self.get_logger().error(f"Parameter '{name}' is not set.")
                raise RuntimeError(f"Missing required parameter: {name}")

        # ── Publisher ─────────────────────────────────────────────────────────
        self.pub = self.create_publisher(InspectionResult, '/inspection_result', 10)

        # ── Thread-safe queue: backend → ROS2 publish timer ──────────────────
        self.result_queue: queue.Queue = queue.Queue()

        # ── Start subprocess ──────────────────────────────────────────────────
        self._start_subprocess()

        # ── Publish timer ─────────────────────────────────────────────────────
        self.timer = self.create_timer(1.0 / publish_rate, self._publish_latest)

        self.get_logger().info(
            f"InspectionNode started  [mode={self.inference_mode}  rate={publish_rate:.1f}Hz]"
        )

    # ── Subprocess management ─────────────────────────────────────────────────

    def _start_subprocess(self):
        cmd = [
            self.python_binary,
            self.backend_script,
            '--mode',     self.inference_mode,
            '--model',    self.model_path,
            '--metadata', self.metadata_path,
        ]
        if self.camera_id >= 0:
            cmd += ['--camera-id', str(self.camera_id)]
        if self.zoom > 1.0:
            cmd += ['--zoom', str(self.zoom)]
        if self.fail_threshold != 0.5:
            cmd += ['--fail-threshold', str(self.fail_threshold)]

        self.get_logger().info('Launching inference backend: ' + ' '.join(cmd))
        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            self.get_logger().error(f"Cannot start backend: {exc}")
            raise

        threading.Thread(target=self._read_stdout, daemon=True, name='insp-stdout').start()
        threading.Thread(target=self._read_stderr, daemon=True, name='insp-stderr').start()

    def _read_stdout(self):
        for raw in self.proc.stdout:
            line = raw.decode('utf-8', errors='replace').strip()
            if not line:
                continue
            try:
                self.result_queue.put(json.loads(line))
            except json.JSONDecodeError:
                pass  # model loading messages, ignore

    def _read_stderr(self):
        for raw in self.proc.stderr:
            line = raw.decode('utf-8', errors='replace').strip()
            if line:
                self.get_logger().debug(f'[backend] {line}')

    # ── Timer: drain queue → publish latest ──────────────────────────────────

    def _publish_latest(self):
        if self.result_queue.empty():
            return
        latest = None
        while not self.result_queue.empty():
            latest = self.result_queue.get_nowait()
        if latest is None:
            return

        msg = InspectionResult()
        msg.header.stamp     = self.get_clock().now().to_msg()
        msg.label            = str(latest.get('label', 'FAIL'))
        msg.class_id         = int(latest.get('class_id', 0))
        msg.confidence       = float(latest.get('confidence', 0.0))
        msg.latency_ms       = float(latest.get('latency_ms', 0.0))
        msg.capture_time_unix = float(latest.get('capture_time_unix', 0.0))
        self.pub.publish(msg)

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def destroy_node(self):
        if hasattr(self, 'proc') and self.proc.poll() is None:
            self.get_logger().info('Terminating inference backend...')
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                self.get_logger().warning('Backend did not exit in time; killing.')
                self.proc.kill()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = InspectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
