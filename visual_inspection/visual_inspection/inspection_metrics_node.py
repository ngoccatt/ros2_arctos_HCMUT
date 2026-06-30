#!/usr/bin/env python3
"""
inspection_metrics_node.py

System-level performance metrics for the visual inspection pipeline.
Tracks per-cycle timing, per-phase latency breakdown, system accuracy,
and False Negative Rate across N ≥ 30 actual runs.

HOW TO USE
----------
1. Launch the full inspection stack as usual.
2. Launch this node (or use enable_metrics:=true in the launch file).
3. Trigger a labeled run by publishing object_id to the trigger topic.
   Prefix PASS_ or FAIL_ encodes the ground truth verdict:

   ros2 topic pub --once /inspection_metrics/trigger std_msgs/String \
       "data: 'FAIL_scratch_s01_001'"
   ros2 topic pub --once /inspection_metrics/trigger std_msgs/String \
       "data: 'PASS_sample_s01_001'"

4. The node calls /run_inspection for you, records all timing/accuracy,
   and writes CSV + JSON on shutdown.

Topics
------
  Subscribe:  /inspection_result        — per-frame inference results
  Subscribe:  /inspection_metrics/trigger (std_msgs/String) — labeled run trigger
  Action client: /run_inspection

Outputs  (log_dir, default ~/inspection_metrics/)
-------
  runs_<session>.csv        — one row per completed inspection cycle
  detections_<session>.csv  — one row per /inspection_result frame during active runs
  session_<session>.json    — aggregate session statistics

Key metrics reported
--------------------
  cycle_time_s              — wall time from goal accepted → result (per object)
  system_accuracy_pct       — verdict accuracy across N labeled runs
  false_negative_rate_pct   — fraction of FAIL objects incorrectly passed (missed defects)
  false_positive_rate_pct   — fraction of PASS objects incorrectly rejected
  phase_latency_s           — per-phase timing: motion / collection / classify / sort / home
  inference_latency_ms      — model-only inference time stats (p50, p95, p99)
  pipe_latency_ms           — camera capture → ROS publish latency
"""

import os
import csv
import json
import threading
from collections import defaultdict
from datetime import datetime

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup

from std_msgs.msg import String
from visual_inspection.msg import InspectionResult
from visual_inspection.action import RunInspection


class InspectionMetricsNode(Node):
    def __init__(self):
        super().__init__('inspection_metrics_node')

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter('confidence_threshold', 0.70)
        self.declare_parameter('log_dir', os.path.expanduser('~/inspection_metrics'))
        self.declare_parameter('stats_interval_sec', 60.0)

        self.confidence_threshold = self.get_parameter('confidence_threshold').value
        log_dir  = self.get_parameter('log_dir').value
        interval = self.get_parameter('stats_interval_sec').value

        # ── Log files ─────────────────────────────────────────────────────────
        os.makedirs(log_dir, exist_ok=True)
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        runs_path = os.path.join(log_dir, f'runs_{session_id}.csv')
        det_path  = os.path.join(log_dir, f'detections_{session_id}.csv')
        self.json_path = os.path.join(log_dir, f'session_{session_id}.json')

        self._runs_file = open(runs_path, 'w', newline='')
        self._runs_w    = csv.writer(self._runs_file)
        self._runs_w.writerow([
            'run_id', 'object_id', 'expected', 'verdict',
            'pass_votes', 'fail_votes', 'correct',
            'cycle_time_s',
            't_motion_s', 't_collection_s', 't_classify_s', 't_sort_s', 't_home_s',
            'frame_count', 'mean_inference_ms', 'mean_pipe_ms', 'mean_confidence',
        ])

        self._det_file = open(det_path, 'w', newline='')
        self._det_w    = csv.writer(self._det_file)
        self._det_w.writerow([
            'run_id', 'ros_time_s', 'capture_time_unix', 'pipe_latency_ms',
            'label', 'class_id', 'confidence', 'inference_ms', 'above_threshold',
        ])

        # ── Run state ─────────────────────────────────────────────────────────
        self._lock       = threading.Lock()
        self._run_id     = 0
        self._active_run = None   # dict while a cycle is in-flight, else None
        self._runs       = []     # list of completed run dicts

        # ── Aggregate stats (all frames, all runs) ─────────────────────────────
        self._total_frames    = 0
        self._above_threshold = 0
        self._inf_samples     = []   # capped at 20 000
        self._pipe_samples    = []

        # ── ROS interfaces ─────────────────────────────────────────────────────
        cb = ReentrantCallbackGroup()

        self.create_subscription(
            InspectionResult, '/inspection_result',
            self._on_result_frame, 10, callback_group=cb)

        self.create_subscription(
            String, '/inspection_metrics/trigger',
            self._on_trigger, 10, callback_group=cb)

        self._action_client = ActionClient(
            self, RunInspection, '/run_inspection', callback_group=cb)

        self.create_timer(interval, self._print_stats, callback_group=cb)

        self.get_logger().info(
            f'InspectionMetricsNode started\n'
            f'  runs CSV:       {runs_path}\n'
            f'  detections CSV: {det_path}\n'
            f'  JSON summary:   {self.json_path}\n'
            f'  Trigger a labeled run:\n'
            f'    ros2 topic pub --once /inspection_metrics/trigger '
            f'std_msgs/String "data: \'FAIL_scratch_01\'"')

    # ── Trigger callback ───────────────────────────────────────────────────────

    def _on_trigger(self, msg: String):
        object_id = msg.data.strip()
        with self._lock:
            if self._active_run is not None:
                self.get_logger().warn(
                    f'Run already in progress ({self._active_run["object_id"]}). '
                    f'Ignoring: {object_id}')
                return

        upper = object_id.upper()
        if upper.startswith('PASS'):
            expected = 'PASS'
        elif upper.startswith('FAIL'):
            expected = 'FAIL'
        else:
            expected = 'UNKNOWN'
            self.get_logger().warn(
                f'object_id "{object_id}" has no PASS/FAIL prefix — '
                f'accuracy will not be counted for this run.')

        with self._lock:
            self._run_id += 1
            self._active_run = {
                'run_id':      self._run_id,
                'object_id':   object_id,
                'expected':    expected,
                'start_time':  self.get_clock().now().nanoseconds * 1e-9,
                'phase_times': {},   # state_name → ros_time_s
                'frames':      [],
            }

        self.get_logger().info(
            f'[RUN {self._run_id}] Starting  object_id="{object_id}"  expected={expected}')

        if not self._action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('/run_inspection action server not available.')
            with self._lock:
                self._active_run = None
            return

        goal = RunInspection.Goal()
        goal.object_id = object_id
        future = self._action_client.send_goal_async(
            goal, feedback_callback=self._on_feedback)
        future.add_done_callback(self._on_goal_response)

    # ── Action callbacks ───────────────────────────────────────────────────────

    def _on_goal_response(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().error('Goal rejected by /run_inspection server.')
            with self._lock:
                self._active_run = None
            return
        handle.get_result_async().add_done_callback(self._on_cycle_result)

    def _on_feedback(self, fb_msg):
        state = fb_msg.feedback.state
        now   = self.get_clock().now().nanoseconds * 1e-9
        with self._lock:
            if self._active_run is not None:
                self._active_run['phase_times'][state] = now
        self.get_logger().debug(
            f'  phase={state}  pass={fb_msg.feedback.pass_votes}'
            f'  fail={fb_msg.feedback.fail_votes}')

    def _on_cycle_result(self, future):
        end_time = self.get_clock().now().nanoseconds * 1e-9
        res_wrap = future.result()

        with self._lock:
            run = self._active_run
            self._active_run = None

        if run is None:
            return

        verdict  = res_wrap.result.verdict
        pass_v   = res_wrap.result.pass_votes
        fail_v   = res_wrap.result.fail_votes
        expected = run['expected']
        correct  = (verdict == expected) if expected != 'UNKNOWN' else None
        cycle_s  = end_time - run['start_time']
        phase    = run['phase_times']
        frames   = run['frames']

        t = self._compute_phase_times(phase, run['start_time'], end_time)

        inf_list  = [f['inference_ms'] for f in frames]
        pipe_list = [f['pipe_ms'] for f in frames if f['pipe_ms'] is not None]
        conf_list = [f['confidence'] for f in frames]
        mean_inf  = sum(inf_list) / len(inf_list)   if inf_list  else 0.0
        mean_pipe = sum(pipe_list) / len(pipe_list) if pipe_list else 0.0
        mean_conf = sum(conf_list) / len(conf_list) if conf_list else 0.0

        self._runs_w.writerow([
            run['run_id'], run['object_id'], expected, verdict,
            pass_v, fail_v,
            (int(correct) if correct is not None else ''),
            f'{cycle_s:.3f}',
            f'{t["motion_s"]:.3f}', f'{t["collection_s"]:.3f}',
            f'{t["classify_s"]:.3f}', f'{t["sort_s"]:.3f}', f'{t["home_s"]:.3f}',
            len(frames), f'{mean_inf:.2f}', f'{mean_pipe:.2f}', f'{mean_conf:.4f}',
        ])
        self._runs_file.flush()

        missed = (expected == 'FAIL' and verdict == 'PASS')
        self.get_logger().info(
            f'[RUN {run["run_id"]}] DONE  verdict={verdict}  expected={expected}'
            f'  correct={correct}  cycle={cycle_s:.1f}s'
            + ('  !! MISSED DEFECT (FN) !!' if missed else ''))

        self._runs.append({
            'run_id':        run['run_id'],
            'object_id':     run['object_id'],
            'expected':      expected,
            'verdict':       verdict,
            'pass_votes':    pass_v,
            'fail_votes':    fail_v,
            'correct':       correct,
            'cycle_time_s':  round(cycle_s, 3),
            'phase_times_s': t,
            'frame_count':   len(frames),
            'mean_inference_ms': round(mean_inf, 2),
            'mean_pipe_ms':  round(mean_pipe, 2),
        })

    # ── /inspection_result subscriber ─────────────────────────────────────────

    def _on_result_frame(self, msg: InspectionResult):
        ros_time = self.get_clock().now().nanoseconds * 1e-9
        capture  = msg.capture_time_unix
        pipe_ms  = (ros_time - capture) * 1000.0 if capture > 0.0 else None
        above    = int(msg.confidence >= self.confidence_threshold)

        with self._lock:
            run = self._active_run

        if run is not None:
            frame_rec = {
                'ros_time':     ros_time,
                'capture_time': capture,
                'pipe_ms':      pipe_ms,
                'label':        msg.label,
                'class_id':     msg.class_id,
                'confidence':   msg.confidence,
                'inference_ms': msg.latency_ms,
            }
            with self._lock:
                run['frames'].append(frame_rec)

            self._det_w.writerow([
                run['run_id'],
                f'{ros_time:.6f}',
                f'{capture:.6f}' if capture > 0.0 else '',
                f'{pipe_ms:.2f}' if pipe_ms is not None else '',
                msg.label, msg.class_id,
                f'{msg.confidence:.4f}',
                f'{msg.latency_ms:.2f}',
                above,
            ])
            self._det_file.flush()

        self._total_frames    += 1
        self._above_threshold += above
        if len(self._inf_samples) < 20_000:
            self._inf_samples.append(msg.latency_ms)
        if pipe_ms is not None and len(self._pipe_samples) < 20_000:
            self._pipe_samples.append(pipe_ms)

    # ── Phase duration extraction ──────────────────────────────────────────────

    @staticmethod
    def _compute_phase_times(phase: dict, t_start: float, t_end: float) -> dict:
        """Compute per-phase durations from action feedback state timestamps."""

        def ts(key, default):
            return phase.get(key, default)

        # Motion time: sum of MOVING_TO_INSPECT_Px → COLLECTING_INSPECT_Px intervals
        move_states = sorted(
            [s for s in phase if 'MOVING_TO_INSPECT_' in s or s == 'MOVING_TO_PICK'],
            key=lambda s: phase[s])
        coll_states = sorted(
            [s for s in phase if 'COLLECTING_' in s],
            key=lambda s: phase[s])

        motion_s = 0.0
        collect_s = 0.0

        for i, mv in enumerate(move_states):
            if i < len(coll_states):
                motion_s += max(0.0, phase[coll_states[i]] - phase[mv])
            if i < len(coll_states) and (i + 1) < len(move_states):
                collect_s += max(0.0, phase[move_states[i + 1]] - phase[coll_states[i]])

        # Last collection → CLASSIFYING
        t_classify_start = ts('CLASSIFYING', t_end)
        if coll_states:
            collect_s += max(0.0, t_classify_start - phase[coll_states[-1]])

        # Classify → start of sort move
        sort_key = next(
            (s for s in ('MOVING_TO_SORT_PASS', 'MOVING_TO_SORT_FAIL') if s in phase),
            None)
        t_sort_start = phase[sort_key] if sort_key else t_classify_start
        classify_s = max(0.0, t_sort_start - t_classify_start)

        # Sort move → MOVING_HOME
        t_home_start = ts('MOVING_HOME', t_end)
        sort_s = max(0.0, t_home_start - t_sort_start) if sort_key else 0.0

        # MOVING_HOME → DONE
        t_done = ts('DONE', t_end)
        home_s = max(0.0, t_done - t_home_start)

        return {
            'motion_s':     round(motion_s, 3),
            'collection_s': round(collect_s, 3),
            'classify_s':   round(classify_s, 3),
            'sort_s':       round(sort_s, 3),
            'home_s':       round(home_s, 3),
        }

    # ── Periodic stats print ───────────────────────────────────────────────────

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
        runs = list(self._runs)
        n    = len(runs)

        self.get_logger().info(
            f'[METRICS] runs={n}  inference_frames={self._total_frames}')

        if n == 0:
            self.get_logger().info(
                '  Waiting for labeled runs on /inspection_metrics/trigger')
            return

        labeled   = [r for r in runs if r['expected'] != 'UNKNOWN']
        fail_runs = [r for r in labeled if r['expected'] == 'FAIL']
        pass_runs = [r for r in labeled if r['expected'] == 'PASS']
        fn_runs   = [r for r in fail_runs if r['verdict'] == 'PASS']
        fp_runs   = [r for r in pass_runs if r['verdict'] == 'FAIL']

        if labeled:
            correct = sum(1 for r in labeled if r['correct'])
            acc = correct / len(labeled) * 100
            fnr = len(fn_runs) / len(fail_runs) * 100 if fail_runs else 0.0
            fpr = len(fp_runs) / len(pass_runs) * 100 if pass_runs else 0.0
            self.get_logger().info(
                f'  System accuracy:  {acc:.1f}% ({correct}/{len(labeled)} labeled runs)')
            self.get_logger().info(
                f'  False Neg Rate:   {fnr:.1f}% ({len(fn_runs)} missed defects)  '
                f'[target: 0%]')
            self.get_logger().info(
                f'  False Pos Rate:   {fpr:.1f}% ({len(fp_runs)} false rejections)')

        cycle_times = [r['cycle_time_s'] for r in runs]
        mean_c = sum(cycle_times) / len(cycle_times)
        self.get_logger().info(
            f'  Cycle time:       mean={mean_c:.1f}s  '
            f'min={min(cycle_times):.1f}s  max={max(cycle_times):.1f}s  '
            f'(throughput={3600/mean_c:.0f} parts/hr)')

        # Average phase breakdown
        phase_keys = ['motion_s', 'collection_s', 'classify_s', 'sort_s', 'home_s']
        for k in phase_keys:
            vals = [r['phase_times_s'][k] for r in runs if k in r.get('phase_times_s', {})]
            if vals:
                self.get_logger().info(
                    f'    {k:<15s}: {sum(vals)/len(vals):.2f}s avg')

        if self._inf_samples:
            st = self._latency_stats(self._inf_samples)
            self.get_logger().info(
                f'  Inference latency: mean={st["mean"]:.1f}ms  '
                f'p95={st["p95"]:.1f}ms  p99={st["p99"]:.1f}ms')
        if self._pipe_samples:
            st = self._latency_stats(self._pipe_samples)
            self.get_logger().info(
                f'  Pipe latency:      mean={st["mean"]:.1f}ms  '
                f'p95={st["p95"]:.1f}ms')

        if len(labeled) < 30:
            remaining = 30 - len(labeled)
            self.get_logger().info(
                f'  [NOTE] {remaining} more labeled runs needed to reach N=30 '
                f'for statistically meaningful system accuracy.')

    # ── Session summary ────────────────────────────────────────────────────────

    def _save_summary(self):
        runs    = list(self._runs)
        labeled = [r for r in runs if r['expected'] != 'UNKNOWN']
        fail_r  = [r for r in labeled if r['expected'] == 'FAIL']
        pass_r  = [r for r in labeled if r['expected'] == 'PASS']
        fn_r    = [r for r in fail_r if r['verdict'] == 'PASS']
        fp_r    = [r for r in pass_r if r['verdict'] == 'FAIL']

        correct    = sum(1 for r in labeled if r['correct']) if labeled else 0
        acc        = correct / len(labeled) * 100 if labeled else 0.0
        fnr        = len(fn_r) / len(fail_r) * 100 if fail_r else 0.0
        fpr        = len(fp_r) / len(pass_r) * 100 if pass_r else 0.0
        cycle_t    = [r['cycle_time_s'] for r in runs]

        # Average phase breakdown across all runs
        phase_avg = defaultdict(list)
        for r in runs:
            for k, v in r.get('phase_times_s', {}).items():
                if v > 0:
                    phase_avg[k].append(v)

        summary = {
            'session_end':             datetime.now().isoformat(),
            'confidence_threshold':    self.confidence_threshold,
            'total_runs':              len(runs),
            'labeled_runs':            len(labeled),
            'system_accuracy_pct':     round(acc, 2),
            'false_negative_rate_pct': round(fnr, 2),
            'false_positive_rate_pct': round(fpr, 2),
            'missed_defects':          len(fn_r),
            'false_rejections':        len(fp_r),
            'n30_reached':             len(labeled) >= 30,
            'cycle_time_s': {
                'mean': round(sum(cycle_t) / len(cycle_t), 3) if cycle_t else 0.0,
                'min':  round(min(cycle_t), 3) if cycle_t else 0.0,
                'max':  round(max(cycle_t), 3) if cycle_t else 0.0,
            },
            'phase_latency_avg_s': {
                k: round(sum(v) / len(v), 3) for k, v in phase_avg.items()
            },
            'inference_latency_ms': self._latency_stats(self._inf_samples),
            'pipe_latency_ms':      self._latency_stats(self._pipe_samples),
            'total_inference_frames': self._total_frames,
            'runs': runs,
        }

        with open(self.json_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        self.get_logger().info(f'Session summary saved → {self.json_path}')

    # ── Cleanup ────────────────────────────────────────────────────────────────

    def destroy_node(self):
        self._print_stats()
        self._save_summary()
        self._runs_file.close()
        self._det_file.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = InspectionMetricsNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
