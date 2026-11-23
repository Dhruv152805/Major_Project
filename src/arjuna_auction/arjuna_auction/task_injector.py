#!/usr/bin/env python3
"""
TerrainFleet Task Injector
==========================
Runs on the control laptop. Reads a task list (e.g., tasks_setA.csv) and
announces tasks to the fleet over `/fleet/task_announcement`.

Key Design Rule:
  It ONLY announces tasks. It NEVER assigns tasks or specifies which robot
  should execute them. The fleet robots resolve assignments autonomously
  via decentralized auction (or centralized master if in baseline mode).

Announcement Pacing Modes:
  - on_completion (default): Announces a task, waits until it is claimed / completed,
    then announces the next task.
  - interval: Announces tasks at a fixed time interval (e.g., --interval 20.0).
  - manual: Waits for the operator to press [Enter] to announce each next task.

Usage:
  ros2 run arjuna_auction task_injector --ros-args -p task_file:=tasks_setA.csv
  ros2 run arjuna_auction task_injector --task-file tasks_setA.csv --mode on_completion
  ros2 run arjuna_auction task_injector --task-file tasks_setA.csv --mode interval --interval 15.0
  ros2 run arjuna_auction task_injector --task-file tasks_setA.csv --mode manual
"""

import os
import sys
import csv
import json
import time
import threading
import argparse
from pathlib import Path

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class TaskInjector(Node):
    def __init__(
        self,
        task_file: str,
        mode: str = 'on_completion',
        interval_sec: float = 20.0,
        start_id: str = None,
        concurrency: int = 2,
        task_timeout_sec: float = 600.0,
    ):
        super().__init__('task_injector')

        self.declare_parameter('task_file', task_file)
        self.declare_parameter('pacing_mode', mode)
        self.declare_parameter('interval_sec', interval_sec)
        self.declare_parameter('concurrency', concurrency)
        self.declare_parameter('fleet_robot_ids', ['arjuna_1', 'arjuna_2'])
        self.declare_parameter('claim_timeout_sec', 6.0)
        self.declare_parameter('task_timeout_sec', task_timeout_sec)

        self.task_file = self.get_parameter('task_file').value
        self.pacing_mode = self.get_parameter('pacing_mode').value
        self.interval_sec = float(self.get_parameter('interval_sec').value)
        self.concurrency = max(1, int(self.get_parameter('concurrency').value))
        self.fleet_robot_ids = self.get_parameter('fleet_robot_ids').value
        self.claim_timeout = float(self.get_parameter('claim_timeout_sec').value)
        self.task_timeout = float(self.get_parameter('task_timeout_sec').value)
        self.start_id = start_id

        # Publishers & Subscribers
        self.announce_pub = self.create_publisher(String, '/fleet/task_announcement', 10)
        self.claim_sub = self.create_subscription(String, '/fleet/task_claims', self.claim_callback, 10)
        self.completion_sub = self.create_subscription(String, '/fleet/task_completion', self.completion_callback, 10)
        self.failure_sub = self.create_subscription(String, '/fleet/robot_failure', self.failure_callback, 10)

        # Task list loading
        self.tasks = self._load_tasks(self.task_file)
        self.current_idx = 0
        if self.start_id:
            for idx, t in enumerate(self.tasks):
                if t['task_id'] == self.start_id:
                    self.current_idx = idx
                    break

        # State tracking for multi-robot concurrent execution
        self.active_tasks = {}       # task_id -> dict(status, claimed_by, announced_t, claimed_t)
        self.completed_tasks = {}    # task_id -> dict(robot_id, success, duration, completed_t)
        self.task_retries = {}       # task_id -> int (re-auction attempts)
        self.is_running = True

        self.get_logger().info("=" * 60)
        self.get_logger().info("🚀 TERRAIN FLEET TASK INJECTOR INITIALIZED (SIMULTANEOUS EXECUTION)")
        self.get_logger().info(f"Task file: {self.task_file} ({len(self.tasks)} total tasks)")
        self.get_logger().info(f"Pacing mode: {self.pacing_mode}")
        self.get_logger().info(f"Fleet Concurrency: {self.concurrency} simultaneous active robots")
        self.get_logger().info(f"Fleet robots: {self.fleet_robot_ids}")
        if self.pacing_mode == 'interval':
            self.get_logger().info(f"Interval: {self.interval_sec} seconds")
        self.get_logger().info(f"Starting at index: {self.current_idx} ({self.tasks[self.current_idx]['task_id'] if self.tasks else 'EMPTY'})")
        self.get_logger().info("=" * 60)

        # Worker thread for injecting tasks
        self.worker_thread = threading.Thread(target=self._run_injection_loop, daemon=True)
        self.worker_thread.start()

    def _load_tasks(self, filepath: str):
        path = Path(filepath)
        if not path.exists():
            self.get_logger().error(f"Task file not found: {filepath}")
            sys.exit(1)

        tasks = []
        with open(path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    task = {
                        'task_id': row['task_id'].strip(),
                        'x': float(row['x']),
                        'y': float(row['y']),
                        'heading': float(row.get('heading', 0.0))
                    }
                    tasks.append(task)
                except Exception as e:
                    self.get_logger().warn(f"Skipping malformed row {row}: {e}")
        return tasks

    def claim_callback(self, msg: String):
        try:
            data = json.loads(msg.data)
            tid = data.get('task_id')
            rid = data.get('robot_id')
            if tid:
                if tid in self.active_tasks:
                    self.active_tasks[tid]['status'] = 'claimed'
                    self.active_tasks[tid]['claimed_by'] = rid
                    self.active_tasks[tid]['claimed_t'] = time.time()
                self.get_logger().info(
                    f"🎯 Task [{tid}] CLAIMED by robot [{rid}] "
                    f"(Active in fleet: {len(self.active_tasks)}/{self.concurrency})"
                )
        except Exception:
            pass

    def completion_callback(self, msg: String):
        try:
            data = json.loads(msg.data)
            tid = data.get('task_id')
            rid = data.get('robot_id')
            success = bool(data.get('success', False))
            duration = float(data.get('duration', 0.0) or 0.0)
            distance = float(data.get('distance', 0.0) or 0.0)
            avg_speed = float(data.get('avg_speed', 0.0) or 0.0)
            timestamp = float(data.get('timestamp', time.time()) or time.time())
            if tid:
                was_active = self.active_tasks.pop(tid, None)

                # Re-auction failed tasks to fleet peers if retry count allows
                retries = self.task_retries.get(tid, 0)
                if not success and retries < 1 and was_active and 'task' in was_active:
                    self.task_retries[tid] = retries + 1
                    self.get_logger().warn(
                        f"🔁 Task [{tid}] FAILED by [{rid}]! Triggering FLEET RE-AUCTION (Attempt {self.task_retries[tid]})..."
                    )
                    # Re-insert into active tasks as announced
                    self.active_tasks[tid] = {
                        'task': was_active['task'],
                        'status': 'announced',
                        'claimed_by': None,
                        'announced_t': time.time(),
                        'claimed_t': None
                    }
                    # Announce re-auction to peer robots
                    re_task = dict(was_active['task'])
                    re_task['is_reauction'] = True
                    re_task['failed_by'] = rid
                    self.announce_task(re_task)
                    return

                self.completed_tasks[tid] = {
                    'robot_id': rid,
                    'success': success,
                    'duration': duration,
                    'completed_t': time.time(),
                }
                remaining_active = len(self.active_tasks)
                self.get_logger().info(
                    f"🏁 Task [{tid}] COMPLETED by [{rid}]: "
                    f"success={success}, duration={duration}s "
                    f"| Remaining active: {remaining_active}/{self.concurrency}"
                )
                self._record_completion_to_csv(tid, rid, success, duration, distance, avg_speed, timestamp)
        except Exception:
            pass

    def _record_completion_to_csv(self, tid, rid, success, duration, distance, avg_speed, timestamp):
        log_file = Path('auction_log.csv')
        write_header = not log_file.exists()
        fieldnames = [
            'timestamp', 'task_id', 'observing_robot_id', 'my_bid', 'all_bids_json',
            'winner', 'is_reauction', 'planner_id', 'task_x', 'task_y',
            'nav_success', 'nav_duration_s', 'mode',
            'distance_traveled_m', 'avg_speed_mps',
        ]
        try:
            with open(log_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if write_header:
                    writer.writeheader()
                writer.writerow({
                    'timestamp': timestamp,
                    'task_id': tid,
                    'observing_robot_id': 'task_injector',
                    'my_bid': '',
                    'all_bids_json': '',
                    'winner': rid,
                    'is_reauction': '',
                    'planner_id': 'GridBased',
                    'task_x': '',
                    'task_y': '',
                    'nav_success': success,
                    'nav_duration_s': round(float(duration), 3),
                    'mode': 'decentralized',
                    'distance_traveled_m': round(float(distance), 3),
                    'avg_speed_mps': round(float(avg_speed), 3),
                })
        except Exception as e:
            self.get_logger().warn(f"Failed to record completion to auction_log.csv: {e}")

    def failure_callback(self, msg: String):
        try:
            data = json.loads(msg.data)
            failed_id = data.get('failed_robot_id')
            self.get_logger().warn(f"⚠️ Fleet failure alert: robot [{failed_id}] went offline!")
            for tid, info in self.active_tasks.items():
                if info.get('claimed_by') == failed_id:
                    self.get_logger().warn(f"Task [{tid}] was held by offline robot [{failed_id}], waiting for survivor re-auction.")
                    info['status'] = 're-auctioning'
                    info['claimed_by'] = None
        except Exception:
            pass

    def announce_task(self, task: dict):
        announcement = {
            'task_id': task['task_id'],
            'x': task['x'],
            'y': task['y'],
            'heading': task.get('heading', 0.0),
            'is_reauction': False,
            'timestamp': time.time()
        }
        msg = String()
        msg.data = json.dumps(announcement)
        self.announce_pub.publish(msg)
        self.get_logger().info(
            f"📢 ANNOUNCED Task [{task['task_id']}]: x={task['x']:.2f}, y={task['y']:.2f}, heading={task['heading']:.2f}"
        )

    def _run_injection_loop(self):
        # Allow subscribers time to connect
        time.sleep(1.5)

        total = len(self.tasks)

        if self.pacing_mode == 'manual':
            while rclpy.ok() and self.is_running and self.current_idx < total:
                task = self.tasks[self.current_idx]
                tid = task['task_id']
                print(f"\n--- Injecting Task {self.current_idx + 1}/{total} [{tid}] ---")
                self.active_tasks[tid] = {
                    'task': task, 'status': 'announced', 'claimed_by': None,
                    'announced_t': time.time(), 'claimed_t': None
                }
                self.announce_task(task)
                self.current_idx += 1
                try:
                    user_input = input("Press [Enter] to announce next task (or 'q' to stop)... ")
                    if user_input.strip().lower() == 'q':
                        break
                except EOFError:
                    break

        elif self.pacing_mode == 'interval':
            while rclpy.ok() and self.is_running and self.current_idx < total:
                task = self.tasks[self.current_idx]
                tid = task['task_id']
                print(f"\n--- Injecting Task {self.current_idx + 1}/{total} [{tid}] ---")
                self.active_tasks[tid] = {
                    'task': task, 'status': 'announced', 'claimed_by': None,
                    'announced_t': time.time(), 'claimed_t': None
                }
                self.announce_task(task)
                self.current_idx += 1
                t_end = time.time() + self.interval_sec
                while time.time() < t_end and rclpy.ok() and self.is_running:
                    time.sleep(0.5)

        elif self.pacing_mode == 'on_completion':
            # Pipelined concurrent task execution:
            # Keeps up to `self.concurrency` robots simultaneously active!
            while rclpy.ok() and self.is_running and (self.current_idx < total or len(self.active_tasks) > 0):
                now = time.time()

                # Watchdog: clean up tasks that timed out completely
                for tid, info in list(self.active_tasks.items()):
                    elapsed = now - info['announced_t']
                    if elapsed > self.task_timeout:
                        self.get_logger().error(f"⏱️ Task [{tid}] timed out after {elapsed:.1f}s. Freeing slot.")
                        self.active_tasks.pop(tid, None)

                # Are there any announced tasks currently waiting to be claimed?
                pending_claims = [tid for tid, info in self.active_tasks.items() if info['status'] == 'announced']

                # Can we announce the next task?
                # 1. More tasks available in list
                # 2. Number of active tasks < concurrency limit (e.g. 2 robots)
                # 3. No pending auction in progress (ensures previous winner claimed and set busy penalty)
                if self.current_idx < total and len(self.active_tasks) < self.concurrency and not pending_claims:
                    task = self.tasks[self.current_idx]
                    tid = task['task_id']
                    active_count = len(self.active_tasks) + 1
                    print(f"\n--- Injecting Task {self.current_idx + 1}/{total} [{tid}] | Fleet Active: {active_count}/{self.concurrency} ---")
                    self.active_tasks[tid] = {
                        'task': task,
                        'status': 'announced',
                        'claimed_by': None,
                        'announced_t': time.time(),
                        'claimed_t': None
                    }
                    self.announce_task(task)
                    self.current_idx += 1

                    # Wait for this task to be claimed before announcing another,
                    # so the winning robot updates its busy penalty first!
                    t_claim_start = time.time()
                    claimed = False
                    while rclpy.ok() and self.is_running and (time.time() - t_claim_start < self.claim_timeout):
                        if self.active_tasks.get(tid, {}).get('status') == 'claimed':
                            claimed = True
                            # Brief 0.5s settling pause for DDS network propagation
                            time.sleep(0.5)
                            break
                        time.sleep(0.1)

                    if not claimed:
                        attempts = self.active_tasks.get(tid, {}).get('claim_attempts', 1)
                        if attempts < 3:
                            self.get_logger().warn(
                                f"⏳ Task [{tid}] was NOT claimed after {self.claim_timeout:.1f}s (Attempt {attempts}/3). "
                                f"Re-announcing to fleet..."
                            )
                            self.active_tasks[tid]['claim_attempts'] = attempts + 1
                            self.announce_task(task)
                        else:
                            self.get_logger().error(
                                f"❌ Task [{tid}] was NOT claimed after {attempts} attempts! "
                                f"Check that auction_node or nearest_robot_controller is running. Skipping task."
                            )
                            self.active_tasks.pop(tid, None)
                    continue

                # When fleet is full or all tasks announced, sleep briefly and wait for completions
                time.sleep(0.2)

        self.get_logger().info("=" * 60)
        self.get_logger().info("🏁 All tasks in list have completed execution!")
        self.get_logger().info(f"Summary: {len(self.completed_tasks)} tasks completed.")
        for tid, cinfo in self.completed_tasks.items():
            self.get_logger().info(f"  • {tid}: robot={cinfo.get('robot_id')}, success={cinfo.get('success')}, duration={cinfo.get('duration')}s")
        self.get_logger().info("=" * 60)


def main(args=None):
    parser = argparse.ArgumentParser(description="TerrainFleet Task Injector")
    parser.add_argument('--task-file', '-f', type=str, default='tasks_setA.csv', help="Path to tasks CSV file")
    parser.add_argument('--mode', '-m', choices=['on_completion', 'interval', 'manual'], default='on_completion')
    parser.add_argument('--interval', '-i', type=float, default=20.0, help="Interval seconds for timed mode")
    parser.add_argument('--start-id', '-s', type=str, default=None, help="Start from specific task ID (e.g. T05)")
    parser.add_argument('--concurrency', '-c', type=int, default=2, help="Max simultaneous active tasks across fleet (default: 2)")
    parser.add_argument('--task-timeout', '-t', type=float, default=600.0, help="Watchdog timeout seconds per task (default: 600.0)")

    filtered_args = []
    ros_args = []
    is_ros = False
    for a in sys.argv[1:]:
        if a == '--ros-args':
            is_ros = True
        if is_ros:
            ros_args.append(a)
        else:
            filtered_args.append(a)

    parsed = parser.parse_args(filtered_args)

    rclpy.init(args=ros_args)
    node = TaskInjector(
        task_file=parsed.task_file,
        mode=parsed.mode,
        interval_sec=parsed.interval,
        start_id=parsed.start_id,
        concurrency=parsed.concurrency,
        task_timeout_sec=parsed.task_timeout
    )
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.is_running = False
        try:
            node.destroy_node()
        except Exception:
            pass
        if rclpy.ok():
            try:
                rclpy.shutdown()
            except Exception:
                pass


if __name__ == '__main__':
    main()
