#!/usr/bin/env python3
"""
gesture_metrics_node.py

Records every /gesture_detection frame to a CSV file and prints running
performance statistics at a configurable interval.  On shutdown it writes
a JSON session summary — both files are the primary artefacts for paper-
level performance evaluation.

Topics subscribed:
    /gesture_detection  (gesture_control/msg/GestureDetection)
    /gesture_command    (std_msgs/msg/String)   — confirmed-executed gestures

Outputs written to log_dir (default ~/gesture_metrics/):
    detections_<session>.csv   — one row per incoming detection frame
    session_<session>.json     — aggregate stats for the whole run

CSV columns:
    ros_time_s          ROS wall time when the message was received
    capture_time_unix   Unix epoch from the inference backend (camera grab)
    pipe_latency_ms     ros_time_s − capture_time_unix  (full pipeline delay)
    label               gesture class label
    class_id            model class index
    confidence          softmax score [0, 1]
    inference_ms        model-only inference time (from backend)
    above_threshold     1 if confidence >= confidence_threshold, else 0
"""

import os
import csv
import json
import rclpy
from rclpy.node import Node
from collections import defaultdict
from datetime import datetime

from gesture_control.msg import GestureDetection
from std_msgs.msg import String


class GestureMetricsNode(Node):
    def __init__(self):
        super().__init__('gesture_metrics_node')

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter('confidence_threshold', 0.70)
        self.declare_parameter('stability_frames',     3)
        self.declare_parameter('publish_rate_hz',      10.0)
        self.declare_parameter('log_dir', os.path.expanduser('~/gesture_metrics'))
        self.declare_parameter('stats_interval_sec', 30.0)

        threshold = self.get_parameter('confidence_threshold').value
        log_dir   = self.get_parameter('log_dir').value
        interval  = self.get_parameter('stats_interval_sec').value

        self.confidence_threshold = threshold

        # ── Log files ─────────────────────────────────────────────────────────
        os.makedirs(log_dir, exist_ok=True)
        session_id     = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path       = os.path.join(log_dir, f'detections_{session_id}.csv')
        self.json_path = os.path.join(log_dir, f'session_{session_id}.json')

        self._csv_file   = open(csv_path, 'w', newline='')
        self._csv_writer = csv.writer(self._csv_file)
        self._csv_writer.writerow([
            'ros_time_s', 'capture_time_unix', 'pipe_latency_ms',
            'label', 'class_id', 'confidence', 'inference_ms', 'above_threshold',
        ])

        # ── Running stats ─────────────────────────────────────────────────────
        self._total_frames    = 0
        self._above_threshold = 0

        # per_class[label] = {'count': int, 'conf_sum': float, 'inf_sum': float}
        self._per_class = defaultdict(lambda: {'count': 0, 'conf_sum': 0.0, 'inf_sum': 0.0})

        # Latency samples — capped at 20 000 to bound memory
        self._pipe_samples = []   # pipe_latency_ms values
        self._inf_samples  = []   # inference_ms values
        self._exec_samples = []   # exec_latency_ms values (all gestures combined)
        # per_gesture_exec[label] = [latency_ms, ...]
        self._exec_per_gesture = defaultdict(list)

        # Executed command log (from /gesture_command)
        self._executed_commands = []

        # ── Subscriptions ─────────────────────────────────────────────────────
        self.create_subscription(
            GestureDetection, '/gesture_detection',
            self._on_detection, 10)
        self.create_subscription(
            String, '/gesture_command',
            self._on_command, 10)
        self.create_subscription(
            String, '/gesture_exec_result',
            self._on_exec_result, 10)

        # ── Periodic stats ────────────────────────────────────────────────────
        self.create_timer(interval, self._print_stats)

        self.get_logger().info(
            f'GestureMetricsNode started\n'
            f'  CSV  → {csv_path}\n'
            f'  JSON → {self.json_path}')

    # ── Callbacks ──────────────────────────────────────────────────────────────

    def _on_detection(self, msg: GestureDetection):
        ros_time = self.get_clock().now().nanoseconds * 1e-9
        capture  = msg.capture_time_unix
        pipe_ms  = (ros_time - capture) * 1000.0 if capture > 0.0 else float('nan')
        above    = int(msg.confidence >= self.confidence_threshold)

        # CSV row
        self._csv_writer.writerow([
            f'{ros_time:.6f}',
            f'{capture:.6f}' if capture > 0.0 else '',
            f'{pipe_ms:.2f}' if capture > 0.0 else '',
            msg.label,
            msg.class_id,
            f'{msg.confidence:.4f}',
            f'{msg.latency_ms:.2f}',
            above,
        ])
        self._csv_file.flush()

        # Counters
        self._total_frames += 1
        self._above_threshold += above

        s = self._per_class[msg.label]
        s['count']    += 1
        s['conf_sum'] += msg.confidence
        s['inf_sum']  += msg.latency_ms

        if capture > 0.0 and len(self._pipe_samples) < 20_000:
            self._pipe_samples.append(pipe_ms)
        if len(self._inf_samples) < 20_000:
            self._inf_samples.append(msg.latency_ms)

    def _on_command(self, msg: String):
        ts = self.get_clock().now().nanoseconds * 1e-9
        self._executed_commands.append({'timestamp': ts, 'gesture': msg.data})
        self.get_logger().info(f'[CMD] executed: {msg.data}')

    def _on_exec_result(self, msg: String):
        try:
            label, ms_str = msg.data.split(':', 1)
            exec_ms = float(ms_str)
        except (ValueError, AttributeError):
            return
        if len(self._exec_samples) < 20_000:
            self._exec_samples.append(exec_ms)
        self._exec_per_gesture[label].append(exec_ms)
        self.get_logger().info(f'[CMD] exec_latency [{label}]: {exec_ms:.0f} ms')

    # ── Stats helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _latency_stats(samples: list) -> dict:
        if not samples:
            return {}
        s = sorted(samples)
        n = len(s)
        return {
            'count': n,
            'mean':  round(sum(s) / n, 2),
            'min':   round(s[0], 2),
            'p50':   round(s[n // 2], 2),
            'p95':   round(s[min(int(n * 0.95), n - 1)], 2),
            'p99':   round(s[min(int(n * 0.99), n - 1)], 2),
            'max':   round(s[-1], 2),
        }

    def _print_stats(self):
        total = self._total_frames
        if total == 0:
            self.get_logger().info('[METRICS] No detections yet.')
            return

        above      = self._above_threshold
        accept_pct = above / total * 100.0
        n_cmd      = len(self._executed_commands)

        self.get_logger().info(
            f'[METRICS] frames={total}  above_threshold={above} ({accept_pct:.1f}%)'
            f'  commands_executed={n_cmd}')

        for label in sorted(self._per_class):
            s = self._per_class[label]
            n = s['count']
            if n == 0:
                continue
            self.get_logger().info(
                f'  {label:<12s} n={n:5d}  '
                f'mean_conf={s["conf_sum"]/n:.3f}  '
                f'mean_inf={s["inf_sum"]/n:.1f}ms')

        if self._pipe_samples:
            st = self._latency_stats(self._pipe_samples)
            self.get_logger().info(
                f'  pipe_latency  mean={st["mean"]:.0f}ms  '
                f'p50={st["p50"]:.0f}ms  p95={st["p95"]:.0f}ms')

        if self._inf_samples:
            st = self._latency_stats(self._inf_samples)
            self.get_logger().info(
                f'  inference     mean={st["mean"]:.1f}ms  '
                f'p50={st["p50"]:.1f}ms  p95={st["p95"]:.1f}ms')

        if self._exec_samples:
            st = self._latency_stats(self._exec_samples)
            stab_ms = (self.get_parameter('stability_frames').value - 1) * 100.0
            pipe_mean = self._latency_stats(self._pipe_samples).get('mean', 0.0)
            e2e = stab_ms + pipe_mean + st['mean']
            self.get_logger().info(
                f'  exec_latency  mean={st["mean"]:.0f}ms  '
                f'p50={st["p50"]:.0f}ms  p95={st["p95"]:.0f}ms')
            for label, samples in sorted(self._exec_per_gesture.items()):
                gs = self._latency_stats(samples)
                self.get_logger().info(
                    f'    [{label:<10s}] n={gs["count"]}  '
                    f'mean={gs["mean"]:.0f}ms  p50={gs["p50"]:.0f}ms')
            self.get_logger().info(
                f'  E2E estimate  stab={stab_ms:.0f}ms + pipe={pipe_mean:.0f}ms'
                f' + exec={st["mean"]:.0f}ms = {e2e:.0f}ms')

    def _save_summary(self):
        total = self._total_frames
        above = self._above_threshold
        summary = {
            'session_end':            datetime.now().isoformat(),
            'confidence_threshold':   self.confidence_threshold,
            'total_frames':           total,
            'above_threshold_frames': above,
            'acceptance_rate_pct':    round(above / total * 100.0, 2) if total > 0 else 0.0,
            'commands_executed':      len(self._executed_commands),
            'per_class':              {},
            'stability_buffer_ms':    (self.get_parameter('stability_frames').value - 1) * 100.0,
            'pipe_latency_ms':        self._latency_stats(self._pipe_samples),
            'inference_latency_ms':   self._latency_stats(self._inf_samples),
            'exec_latency_ms':        self._latency_stats(self._exec_samples),
            'exec_latency_per_gesture': {
                label: self._latency_stats(samples)
                for label, samples in self._exec_per_gesture.items()
            },
            'e2e_latency_ms':         {},
            'command_log':            self._executed_commands,
        }

        for label, s in self._per_class.items():
            n = s['count']
            summary['per_class'][label] = {
                'count':             n,
                'mean_confidence':   round(s['conf_sum'] / n, 4) if n > 0 else 0.0,
                'mean_inference_ms': round(s['inf_sum']  / n, 2) if n > 0 else 0.0,
            }

        # E2E = stability_buffer + pipe + exec
        pipe_st = summary['pipe_latency_ms']
        exec_st = summary['exec_latency_ms']
        if pipe_st and exec_st:
            stab = summary['stability_buffer_ms']
            summary['e2e_latency_ms'] = {
                'components': {
                    'stability_buffer_ms': stab,
                    'pipe_latency_ms':     pipe_st.get('mean', 0.0),
                    'exec_latency_ms':     exec_st.get('mean', 0.0),
                },
                'total_mean_ms': round(stab + pipe_st.get('mean', 0.0) + exec_st.get('mean', 0.0), 1),
                'total_p95_ms':  round(stab + pipe_st.get('p95',  0.0) + exec_st.get('p95',  0.0), 1),
            }

        with open(self.json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        self.get_logger().info(f'Session summary saved → {self.json_path}')

    # ── Cleanup ────────────────────────────────────────────────────────────────

    def destroy_node(self):
        self._print_stats()
        self._save_summary()
        self._csv_file.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = GestureMetricsNode()
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
