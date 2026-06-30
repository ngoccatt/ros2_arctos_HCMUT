#!/usr/bin/env python3
"""
ROS2 gesture recognition node (Python 3.10).

Spawns gesture_inference_backend.py as a subprocess under the gesture_env Python 3.9
and reads JSON results from its stdout, publishing them as GestureDetection messages.

Topics published:
    /gesture_detection  (gesture_control/msg/GestureDetection)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Header
from gesture_control.msg import GestureDetection

import subprocess
import threading
import queue
import json
import os
import sys


class GestureRecognitionNode(Node):
    def __init__(self):
        super().__init__('gesture_recognition_node')

        # Parameters
        self.declare_parameter('inference_mode', 'cpu')
        self.declare_parameter(
            'python_binary',
            '/home/nam/.pyenv/versions/gesture_env/bin/python'
        )
        self.declare_parameter('backend_script', '')
        # Two separate model paths; the node picks the right one based on inference_mode
        self.declare_parameter('edgetpu_model_path', '')
        self.declare_parameter('cpu_model_path', '')
        self.declare_parameter('metadata_path', '')
        self.declare_parameter('camera_id', 0)
        self.declare_parameter('publish_rate', 10.0)

        self.inference_mode      = self.get_parameter('inference_mode').value
        self.python_binary       = self.get_parameter('python_binary').value
        self.backend_script      = self.get_parameter('backend_script').value
        edgetpu_model_path       = self.get_parameter('edgetpu_model_path').value
        cpu_model_path           = self.get_parameter('cpu_model_path').value
        self.metadata_path       = self.get_parameter('metadata_path').value
        self.camera_id           = self.get_parameter('camera_id').value
        publish_rate             = self.get_parameter('publish_rate').value

        # Select model path based on inference mode
        if self.inference_mode == 'edgetpu':
            self.model_path = edgetpu_model_path
        else:
            self.model_path = cpu_model_path

        # Validate required paths
        for name, value in [
            ('backend_script', self.backend_script),
            ('model_path',     self.model_path),
            ('metadata_path',  self.metadata_path),
        ]:
            if not value:
                self.get_logger().error(f"Parameter '{name}' is not set.")
                raise RuntimeError(f"Missing required parameter: {name}")

        # Publisher
        self.pub = self.create_publisher(GestureDetection, '/gesture_detection', 10)

        # Thread-safe queue: inference backend → ROS2 publish timer
        self.result_queue: queue.Queue = queue.Queue()

        # Start the inference subprocess
        self._start_subprocess()

        # Timer callback at publish_rate Hz
        self.timer = self.create_timer(1.0 / publish_rate, self._publish_latest)

        self.get_logger().info(
            f"GestureRecognitionNode started  [mode={self.inference_mode}  "
            f"rate={publish_rate:.1f}Hz]"
        )

    # ------------------------------------------------------------------
    # Subprocess management
    # ------------------------------------------------------------------

    def _start_subprocess(self):
        cmd = [
            self.python_binary,
            self.backend_script,
            '--mode',      self.inference_mode,
            '--model',     self.model_path,
            '--metadata',  self.metadata_path,
            '--camera-id', str(self.camera_id),
        ]
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

        # Daemon thread: read JSON lines from stdout
        threading.Thread(
            target=self._read_stdout, daemon=True, name='backend-stdout'
        ).start()

        # Daemon thread: log stderr from the backend
        threading.Thread(
            target=self._read_stderr, daemon=True, name='backend-stderr'
        ).start()

    def _read_stdout(self):
        """Continuously read JSON lines from the subprocess stdout."""
        for raw in self.proc.stdout:
            line = raw.decode('utf-8', errors='replace').strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                self.result_queue.put(data)
            except json.JSONDecodeError:
                # Backend may print non-JSON during model loading — ignore
                pass

    def _read_stderr(self):
        """Log stderr from the inference backend at DEBUG level."""
        for raw in self.proc.stderr:
            line = raw.decode('utf-8', errors='replace').strip()
            if line:
                self.get_logger().debug(f'[backend] {line}')

    # ------------------------------------------------------------------
    # Timer callback: drain queue → publish latest result
    # ------------------------------------------------------------------

    def _publish_latest(self):
        if self.result_queue.empty():
            return

        # Drain the queue and keep only the most recent frame
        latest = None
        while not self.result_queue.empty():
            latest = self.result_queue.get_nowait()
        if latest is None:
            return

        msg = GestureDetection()
        msg.header.stamp      = self.get_clock().now().to_msg()
        msg.label             = str(latest.get('label', 'none'))
        msg.class_id          = int(latest.get('class_id', -1))
        msg.confidence        = float(latest.get('confidence', 0.0))
        msg.latency_ms        = float(latest.get('latency_ms', 0.0))
        msg.capture_time_unix = float(latest.get('capture_time_unix', 0.0))

        self.pub.publish(msg)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

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
    node = GestureRecognitionNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, RuntimeError):
        # RuntimeError covers the Humble shutdown race on use_sim_time:=true
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()
