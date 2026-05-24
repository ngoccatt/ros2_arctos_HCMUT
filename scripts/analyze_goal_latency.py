#!/usr/bin/env python3
"""Analyze per-goal motion latency from a bringup log.

For each "Received new action goal" interval, this script finds:
- the last "Write command to actuator:" within the interval
- each motor's final degree value and the first timestamp of that final value
- the latest settling timestamp across all motors in the interval

By default, goals involving motor 7 are skipped to filter out gripper-related motion.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


TIMESTAMP_RE = re.compile(r"\[(\d+\.\d+)\]")
GOAL_RE = re.compile(r"Received new action goal")
WRITE_RE = re.compile(r"Write command to actuator:")
MOTOR_UPDATE_RE = re.compile(
    r"Updated motor (\d+) \(normal\) position: (-?\d+(?:\.\d+)?) degrees"
)


@dataclass
class MotorFinalState:
    motor_id: int
    final_value_deg: float
    first_timestamp: float
    line_number: int


@dataclass
class GoalInterval:
    goal_index: int
    goal_timestamp: float
    goal_line: int
    last_write_timestamp: float | None = None
    last_write_line: int | None = None
    last_write_text: str | None = None
    motor_states: dict[int, MotorFinalState] = field(default_factory=dict)

    def register_motor_update(self, motor_id: int, value_deg: float, timestamp: float, line_number: int) -> None:
        current = self.motor_states.get(motor_id)
        if current is None or current.final_value_deg != value_deg:
            self.motor_states[motor_id] = MotorFinalState(
                motor_id=motor_id,
                final_value_deg=value_deg,
                first_timestamp=timestamp,
                line_number=line_number,
            )

    @property
    def latest_motor_state(self) -> MotorFinalState | None:
        if not self.motor_states:
            return None
        return max(self.motor_states.values(), key=lambda state: state.first_timestamp)

    @property
    def includes_motor_7(self) -> bool:
        return 7 in self.motor_states

    @property
    def goal_to_last_write(self) -> float | None:
        if self.last_write_timestamp is None:
            return None
        return self.last_write_timestamp - self.goal_timestamp

    @property
    def goal_to_settle(self) -> float | None:
        latest = self.latest_motor_state
        if latest is None:
            return None
        return latest.first_timestamp - self.goal_timestamp

    @property
    def last_write_to_settle(self) -> float | None:
        latest = self.latest_motor_state
        if latest is None or self.last_write_timestamp is None:
            return None
        return latest.first_timestamp - self.last_write_timestamp


def parse_log(log_path: Path) -> list[GoalInterval]:
    intervals: list[GoalInterval] = []
    current_interval: GoalInterval | None = None
    last_timestamp: float | None = None

    with log_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\n")

            timestamp_match = TIMESTAMP_RE.search(line)
            if timestamp_match:
                last_timestamp = float(timestamp_match.group(1))

            if GOAL_RE.search(line):
                if last_timestamp is None:
                    raise ValueError(f"Goal marker at line {line_number} has no preceding timestamp")
                current_interval = GoalInterval(
                    goal_index=len(intervals) + 1,
                    goal_timestamp=last_timestamp,
                    goal_line=line_number,
                )
                intervals.append(current_interval)
                continue

            if current_interval is None or last_timestamp is None:
                continue

            if WRITE_RE.search(line):
                current_interval.last_write_timestamp = last_timestamp
                current_interval.last_write_line = line_number
                current_interval.last_write_text = line.strip()
                continue

            motor_match = MOTOR_UPDATE_RE.search(line)
            if motor_match:
                motor_id = int(motor_match.group(1))
                value_deg = float(motor_match.group(2))
                current_interval.register_motor_update(motor_id, value_deg, last_timestamp, line_number)

    return intervals


def format_seconds(value: float | None) -> str:
    return "NA" if value is None else f"{value:.3f}"


def print_summary(intervals: list[GoalInterval], skip_motor_7: bool) -> None:
    filtered = [interval for interval in intervals if not (skip_motor_7 and interval.includes_motor_7)]

    if not filtered:
        print("No matching goals found.")
        return

    print("Goal,Goal Line,Last Write Line,Goal->Last Write (s),Goal->Settle (s),Last Write->Settle (s),Latest Settled Motor,Latest Settle Line")
    for interval in filtered:
        latest = interval.latest_motor_state
        latest_motor = f"motor_{latest.motor_id}" if latest else "NA"
        latest_line = latest.line_number if latest else "NA"
        print(
            f"{interval.goal_index},"
            f"{interval.goal_line},"
            f"{interval.last_write_line or 'NA'},"
            f"{format_seconds(interval.goal_to_last_write)},"
            f"{format_seconds(interval.goal_to_settle)},"
            f"{format_seconds(interval.last_write_to_settle)},"
            f"{latest_motor},"
            f"{latest_line}"
        )


def write_csv(intervals: list[GoalInterval], csv_path: Path, skip_motor_7: bool) -> None:
    filtered = [interval for interval in intervals if not (skip_motor_7 and interval.includes_motor_7)]
    fieldnames = [
        "goal_index",
        "goal_timestamp",
        "goal_line",
        "last_write_timestamp",
        "last_write_line",
        "goal_to_last_write_s",
        "goal_to_settle_s",
        "last_write_to_settle_s",
        "latest_settled_motor",
        "latest_settle_timestamp",
        "latest_settle_line",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for interval in filtered:
            latest = interval.latest_motor_state
            writer.writerow(
                {
                    "goal_index": interval.goal_index,
                    "goal_timestamp": interval.goal_timestamp,
                    "goal_line": interval.goal_line,
                    "last_write_timestamp": interval.last_write_timestamp,
                    "last_write_line": interval.last_write_line,
                    "goal_to_last_write_s": interval.goal_to_last_write,
                    "goal_to_settle_s": interval.goal_to_settle,
                    "last_write_to_settle_s": interval.last_write_to_settle,
                    "latest_settled_motor": latest.motor_id if latest else None,
                    "latest_settle_timestamp": latest.first_timestamp if latest else None,
                    "latest_settle_line": latest.line_number if latest else None,
                }
            )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_path", type=Path, help="Path to the bringup log markdown/text file")
    parser.add_argument(
        "--include-motor-7",
        action="store_true",
        help="Include goal intervals that contain motor 7 updates",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="Optional output CSV path for the filtered summary",
    )
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    if not args.log_path.is_file():
        print(f"Log file not found: {args.log_path}", file=sys.stderr)
        return 1

    intervals = parse_log(args.log_path)
    skip_motor_7 = not args.include_motor_7

    print_summary(intervals, skip_motor_7)

    if args.csv:
      write_csv(intervals, args.csv, skip_motor_7)
      print(f"\nSaved CSV summary to {args.csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())