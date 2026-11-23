#!/usr/bin/env python3
"""
TerrainFleet Point Recorder
===========================
Records home positions or task spots using RViz's "Publish Point" tool.

Modes:
  1. Home Mode (--home):
     - Click 1: Robot 1 position
     - Click 2: Point straight ahead of Robot 1 (computes heading)
     - Click 3: Robot 2 position
     - Click 4: Point straight ahead of Robot 2 (computes heading)
     - Saves to fleet_config.yaml and exits automatically.

  2. Task Mode (--task):
     - Each click records one task spot (T01, T02, ...)
     - Appends to tasks_setA.csv (or specified --output file) immediately.
     - Carries over numbering if the file already exists.
     - Press Ctrl+C when done.

Usage:
  ros2 run arjuna_auction record_points --home
  ros2 run arjuna_auction record_points --task --output tasks_setA.csv
  ./record_points.py --home
  ./record_points.py --task
"""

import os
import sys
import math
import yaml
import csv
import argparse
import threading
import time
from pathlib import Path

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PointStamped, PoseWithCovarianceStamped
from nav_msgs.msg import Odometry


def quat_to_yaw(q):
    """Calculates planar 2D yaw angle in radians from a quaternion."""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class PointRecorder(Node):
    def __init__(self, mode: str, method: str, output_path: str, robot_ids=('arjuna_1', 'arjuna_2'), teach_robot='arjuna_1'):
        super().__init__('point_recorder')
        self.mode = mode
        self.method = method  # 'rviz', 'teach', or 'manual'
        self.output_path = output_path
        self.robot_ids = list(robot_ids)
        self.teach_robot = teach_robot

        # State for Home Mode
        self.home_clicks = []  # list of (x, y)
        self.home_prompts = [
            f"[1/4] Click where {self.robot_ids[0]} STANDS (RViz 'Publish Point')...",
            f"[2/4] Click a point straight AHEAD of {self.robot_ids[0]} (for heading)...",
            f"[3/4] Click where {self.robot_ids[1]} STANDS (RViz 'Publish Point')...",
            f"[4/4] Click a point straight AHEAD of {self.robot_ids[1]} (for heading)...",
        ]

        # Latest robot poses: {robot_id: (x, y, yaw, source_str)}
        self.latest_poses = {}

        # State for Task Mode
        self.next_task_num = 1
        if self.mode == 'task':
            self._init_task_file()

        if self.method == 'rviz':
            # Subscribe to RViz Publish Point tool
            self.sub = self.create_subscription(
                PointStamped,
                '/clicked_point',
                self.point_callback,
                10
            )
        elif self.method == 'teach':
            # Subscribe to live AMCL and Odom topics for fleet robots
            for rid in self.robot_ids:
                # AMCL pose
                self.create_subscription(
                    PoseWithCovarianceStamped,
                    f'/{rid}/amcl_pose',
                    lambda msg, r=rid: self._pose_cov_callback(msg, r),
                    10
                )
                # Odometry
                self.create_subscription(
                    Odometry,
                    f'/{rid}/odom',
                    lambda msg, r=rid: self._odom_callback(msg, r),
                    10
                )

        self.get_logger().info("=" * 60)
        self.get_logger().info(f"📍 TERRAINFLEET POINT RECORDER [{self.mode.upper()} MODE] - Method: {self.method.upper()}")
        self.get_logger().info(f"Output Target: {self.output_path}")
        if self.method == 'rviz':
            self.get_logger().info("RViz mode: Click in RViz using 'Publish Point'.")
            if self.mode == 'home':
                self.get_logger().info(self.home_prompts[0])
            else:
                self.get_logger().info(f"Next task ID: T{self.next_task_num:02d}")
        elif self.method == 'teach':
            self.get_logger().info("Headless Teach Mode: Records directly from robot's real-time pose.")
        elif self.method == 'manual':
            self.get_logger().info("Headless Manual Mode: Prompting for numeric coordinates.")
        self.get_logger().info("=" * 60)

    def _pose_cov_callback(self, msg: PoseWithCovarianceStamped, robot_id: str):
        pos = msg.pose.pose.position
        yaw = quat_to_yaw(msg.pose.pose.orientation)
        cov_x = msg.pose.covariance[0]
        cov_y = msg.pose.covariance[7]
        uncertainty = round(math.sqrt(max(0.0, cov_x + cov_y)), 2)
        self.latest_poses[robot_id] = (round(pos.x, 2), round(pos.y, 2), round(yaw, 4), 'amcl', uncertainty)

    def _odom_callback(self, msg: Odometry, robot_id: str):
        # Only use odom if amcl is not yet available
        if robot_id not in self.latest_poses or self.latest_poses[robot_id][3] != 'amcl':
            pos = msg.pose.pose.position
            yaw = quat_to_yaw(msg.pose.pose.orientation)
            self.latest_poses[robot_id] = (round(pos.x, 2), round(pos.y, 2), round(yaw, 4), 'odom', None)

    def _init_task_file(self):
        """Initializes or resumes the task CSV file."""
        csv_file = Path(self.output_path)
        if csv_file.exists():
            try:
                with open(csv_file, 'r', newline='') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    max_num = 0
                    for row in reader:
                        if row and row[0].startswith('T'):
                            try:
                                num = int(row[0][1:])
                                if num > max_num:
                                    max_num = num
                            except ValueError:
                                pass
                    self.next_task_num = max_num + 1
                    self.get_logger().info(
                        f"Existing tasks file found with {max_num} tasks. Continuing from T{self.next_task_num:02d}."
                    )
            except Exception as e:
                self.get_logger().warn(f"Could not read existing task file: {e}. Starting at T01.")
                self.next_task_num = 1
        else:
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['task_id', 'x', 'y', 'heading'])

    def point_callback(self, msg: PointStamped):
        frame = msg.header.frame_id.strip('/')
        if frame != 'map':
            self.get_logger().warn(
                f"Ignored click in frame '{msg.header.frame_id}'. Must be in shared 'map' frame!"
            )
            return

        x = round(float(msg.point.x), 2)
        y = round(float(msg.point.y), 2)

        if self.mode == 'home':
            self._handle_home_click(x, y)
        elif self.mode == 'task':
            self._handle_task_click(x, y)

    def _handle_home_click(self, x: float, y: float):
        click_idx = len(self.home_clicks)
        self.home_clicks.append((x, y))
        self.get_logger().info(f"✓ Recorded click {click_idx + 1}/4 at ({x:.2f}, {y:.2f})")

        if len(self.home_clicks) < 4:
            self.get_logger().info(self.home_prompts[len(self.home_clicks)])
        else:
            p1_pos = self.home_clicks[0]
            p1_face = self.home_clicks[1]
            yaw1 = round(math.atan2(p1_face[1] - p1_pos[1], p1_face[0] - p1_pos[0]), 4)

            p2_pos = self.home_clicks[2]
            p2_face = self.home_clicks[3]
            yaw2 = round(math.atan2(p2_face[1] - p2_pos[1], p2_face[0] - p2_pos[0]), 4)

            self._save_home_config({
                self.robot_ids[0]: {'x': p1_pos[0], 'y': p1_pos[1], 'heading': yaw1},
                self.robot_ids[1]: {'x': p2_pos[0], 'y': p2_pos[1], 'heading': yaw2}
            })
            rclpy.shutdown()

    def _handle_task_click(self, x: float, y: float, heading: float = 0.0):
        task_id = f"T{self.next_task_num:02d}"
        with open(self.output_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([task_id, x, y, heading])
            f.flush()

        self.get_logger().info(f"✅ Recorded {task_id}: x={x:.2f}, y={y:.2f}, heading={heading:.2f}")
        self.next_task_num += 1
        self.get_logger().info(f"Ready for next point -> T{self.next_task_num:02d} (or Ctrl+C to finish)")

    def _save_home_config(self, config: dict):
        with open(self.output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        self.get_logger().info("=" * 60)
        self.get_logger().info(f"✅ Successfully saved fleet home positions to {self.output_path}:")
        for rid, d in config.items():
            self.get_logger().info(f"   {rid}: x={d['x']:.2f}, y={d['y']:.2f}, heading={d['heading']:.4f} rad")
        self.get_logger().info("Now run: ./scripts/set_home_poses.py")
        self.get_logger().info("=" * 60)

    def run_interactive_teach(self):
        """Runs headless interactive teach mode via terminal."""
        time.sleep(1.0)  # Wait for first topic messages
        if self.mode == 'home':
            home_config = {}
            for rid in self.robot_ids:
                print("\n" + "-" * 50)
                print(f"👉 STEP: Position '{rid}' at its desired Home spot on the floor.")
    def _format_pose_quality(self, pose):
        if not pose:
            return "🔴 NO POSE DETECTED", 0.0, 0.0, 0.0
        x, y, yaw, src, uncertainty = pose
        deg = math.degrees(yaw)
        if src == 'amcl':
            if uncertainty is not None and uncertainty <= 0.15:
                badge = f"🟢 AMCL LOCKED (Accuracy: ±{uncertainty}m)"
            elif uncertainty is not None and uncertainty <= 0.35:
                badge = f"🟡 AMCL SETTLING (Accuracy: ±{uncertainty}m - gently nudge robot if needed)"
            else:
                badge = f"🔴 AMCL UNCERTAIN (Accuracy: ±{uncertainty}m - rotate robot in place to align)"
        else:
            badge = "⚪ ODOM ONLY (AMCL not yet active)"
        return f"[{badge}] Position: x={x:.2f}m, y={y:.2f}m | Heading: {deg:.1f}°", x, y, yaw

    def run_interactive_teach(self):
        """Runs headless interactive teach mode via terminal with live AMCL quality checks."""
        time.sleep(1.0)  # Wait for first topic messages
        if self.mode == 'home':
            home_config = {}
            for rid in self.robot_ids:
                print("\n" + "-" * 60)
                print(f"👉 STEP: Position '{rid}' at its desired Home spot on the floor.")
                input(f"   Press [Enter] when '{rid}' is physically placed at its Home spot...")

                pose = self.latest_poses.get(rid)
                status_str, x, y, yaw = self._format_pose_quality(pose)
                print(f"   {status_str}")

                override = input("   Press [Enter] to confirm, or type 'r' to re-check, or 'x y [heading]' to override: ").strip()
                if override.lower() == 'r':
                    time.sleep(0.5)
                    pose = self.latest_poses.get(rid)
                    status_str, x, y, yaw = self._format_pose_quality(pose)
                    print(f"   Updated: {status_str}")
                    override = input("   Press [Enter] to confirm: ").strip()

                if override and override.lower() != 'r':
                    parts = override.split()
                    x = round(float(parts[0]), 2)
                    y = round(float(parts[1]), 2)
                    yaw = round(float(parts[2]), 4) if len(parts) > 2 else yaw

                home_config[rid] = {'x': x, 'y': y, 'heading': yaw}
                print(f"   ✓ Confirmed '{rid}': x={x:.2f}, y={y:.2f}, heading={yaw:.4f}")

            self._save_home_config(home_config)
            rclpy.shutdown()

        elif self.mode == 'task':
            teach_r = self.teach_robot
            print("\n" + "=" * 60)
            print(f"🎯 TEACHING TASKS USING ROBOT '{teach_r}'")
            print(f"Target CSV file: {self.output_path}")
            print("Move/teleop the robot to each task spot on the floor and press [Enter].")
            print("Type 'q' and press [Enter] when finished.")
            print("=" * 60)

            while rclpy.ok():
                task_id = f"T{self.next_task_num:02d}"
                user_cmd = input(f"\n👉 Move '{teach_r}' to spot for {task_id} and press [Enter] (or 'q' to stop): ").strip()
                if user_cmd.lower() == 'q':
                    print("Finished recording tasks.")
                    break

                pose = self.latest_poses.get(teach_r)
                status_str, x, y, yaw = self._format_pose_quality(pose)
                print(f"   {status_str}")

                confirm = input(f"   Confirm {task_id}? Press [Enter] to save, 'r' to re-read, or type 'x y': ").strip()
                if confirm.lower() == 'r':
                    time.sleep(0.5)
                    pose = self.latest_poses.get(teach_r)
                    status_str, x, y, yaw = self._format_pose_quality(pose)
                    print(f"   Updated: {status_str}")
                    confirm = input(f"   Confirm {task_id}? Press [Enter] to save: ").strip()

                if confirm and confirm.lower() != 'r':
                    parts = confirm.split()
                    try:
                        x = round(float(parts[0]), 2)
                        y = round(float(parts[1]), 2)
                        yaw = round(float(parts[2]), 4) if len(parts) > 2 else 0.0
                    except ValueError:
                        pass

                self._handle_task_click(x, y, yaw)

            rclpy.shutdown()

    def run_manual_input(self):
        """Allows direct numeric entry in terminal without needing active ROS robot topics."""
        if self.mode == 'home':
            home_config = {}
            print("\n" + "=" * 60)
            print("📍 MANUAL FLEET HOME POSE ENTRY")
            print("=" * 60)
            for rid in self.robot_ids:
                prompt_text = f"Enter x, y, and heading(rad) for '{rid}' (e.g. 0.0 0.0 0.0): "
                raw = input(prompt_text).strip()
                parts = raw.split() if raw else ['0.0', '0.0', '0.0']
                x = round(float(parts[0]), 2)
                y = round(float(parts[1]), 2) if len(parts) > 1 else 0.0
                yaw = round(float(parts[2]), 4) if len(parts) > 2 else 0.0
                home_config[rid] = {'x': x, 'y': y, 'heading': yaw}
                print(f"   ✓ Configured '{rid}': x={x:.2f}, y={y:.2f}, heading={yaw:.4f} rad")

            self._save_home_config(home_config)
            rclpy.shutdown()

        elif self.mode == 'task':
            print("\n" + "=" * 60)
            print(f"🎯 MANUAL TASK ENTRY (Target: {self.output_path})")
            print("Enter 'x y [heading]' for each task. Type 'q' to finish.")
            print("=" * 60)
            while True:
                task_id = f"T{self.next_task_num:02d}"
                raw = input(f"Enter x y for {task_id} (or 'q' to stop): ").strip()
                if raw.lower() == 'q':
                    break
                parts = raw.split()
                if len(parts) < 2:
                    print("Please enter at least x and y (e.g. '1.5 -0.8').")
                    continue
                try:
                    x = round(float(parts[0]), 2)
                    y = round(float(parts[1]), 2)
                    yaw = round(float(parts[2]), 4) if len(parts) > 2 else 0.0
                    self._handle_task_click(x, y, yaw)
                except ValueError:
                    print("Invalid numbers. Try again.")

            rclpy.shutdown()


def main(args=None):
    parser = argparse.ArgumentParser(description="Record home poses or task points (RViz, Teach, or Manual).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--home', action='store_true', help="Record home positions for both robots")
    group.add_argument('--task', action='store_true', help="Record task spots")

    parser.add_argument(
        '--teach', action='store_true',
        help="Headless Teach Mode: Reads robot's live pose when you hit [Enter] on terminal"
    )
    parser.add_argument(
        '--manual', action='store_true',
        help="Headless Manual Mode: Type numeric x, y coordinates directly in terminal"
    )
    parser.add_argument(
        '--robot', type=str, default='arjuna_1',
        help="Robot ID to use for teaching tasks in --teach mode (default: arjuna_1)"
    )
    parser.add_argument(
        '--output', '-o', type=str, default=None,
        help="Custom output file path (default: fleet_config.yaml for home, tasks_setA.csv for task)"
    )

    # Filter out ROS 2 args
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

    mode = 'home' if parsed.home else 'task'
    method = 'teach' if parsed.teach else ('manual' if parsed.manual else 'rviz')

    if parsed.output:
        output_file = parsed.output
    else:
        output_file = 'fleet_config.yaml' if mode == 'home' else 'tasks_setA.csv'

    rclpy.init(args=ros_args)
    node = PointRecorder(mode=mode, method=method, output_path=output_file, teach_robot=parsed.robot)

    if method == 'teach':
        # Run ROS spinning in background thread so callbacks update poses, while console prompt runs in main thread
        spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
        spin_thread.start()
        node.run_interactive_teach()
    elif method == 'manual':
        node.run_manual_input()
    else:
        # Standard RViz subscriber mode
        try:
            rclpy.spin(node)
        except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
            pass

    if rclpy.ok():
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

