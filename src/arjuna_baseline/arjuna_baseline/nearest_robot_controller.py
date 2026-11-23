#!/usr/bin/env python3
"""
TerrainFleet - Phase 1: Centralized Baseline Controller (Multi-Robot Remote Dispatch Fix)
========================================================================================

A single-controller, nearest-robot-first task assignment node — the "before"
comparison point against the decentralized auction.

FIX DETAILS (Addressing Part 5 requirement):
  Previously, this controller could only send goals to its own local Nav2 stack,
  logging a comment if the nearest robot was the other robot.
  In this fixed version:
  - Whichever robot is active master (selected via `/fleet/centralized_master` and
    `/fleet/mode=="centralized"`) holds ActionClients for ALL robots in the fleet
    (`/{robot_id}/navigate_to_pose`).
  - Whichever robot is nearest to the announced task is directly commanded via Nav2.
  - The controller tracks distance traveled, duration, speed, and logs results to
    `centralized_log.csv`.
  - Publishes claims on `/fleet/task_claims` so RViz markers and dashboards update live.
  - Subscribes to `/fleet/stop_all` for emergency fleet halting.

USAGE (run one instance per robot, or on the master):
  ros2 run arjuna_baseline nearest_robot_controller --ros-args \
      -p robot_id:=arjuna_1 \
      -p fleet_robot_ids:="['arjuna_1','arjuna_2']" \
      -p my_odom_topic:=/arjuna_1/odom \
      -p other_robot_odom_topics:="['/arjuna_2/odom']" \
      -p frame_id:=map

Switch mode to centralized & select master:
  ros2 topic pub /fleet/mode std_msgs/String '{data: "centralized"}' --once
  ros2 topic pub /fleet/centralized_master std_msgs/String '{data: "arjuna_1"}' --once
"""

import csv
import json
import math
import time
from pathlib import Path
from typing import Dict, Optional

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from sensor_msgs.msg import BatteryState
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped


class NearestRobotController(Node):
    def __init__(self):
        super().__init__('nearest_robot_controller')

        self.declare_parameter('robot_id', 'arjuna_1')
        self.declare_parameter('fleet_robot_ids', ['arjuna_1', 'arjuna_2'])
        self.declare_parameter('frame_id', 'map')
        self.declare_parameter('log_path', 'centralized_log.csv')

        self.robot_id = self.get_parameter('robot_id').value
        self.fleet_robot_ids = self.get_parameter('fleet_robot_ids').value
        self.frame_id = self.get_parameter('frame_id').value
        self.log_path = self.get_parameter('log_path').value

        self.other_robot_ids = [r for r in self.fleet_robot_ids if r != self.robot_id]

        self.log_fieldnames = [
            'timestamp', 'task_id', 'assigned_to', 'distances_json',
            'task_x', 'task_y', 'nav_success', 'nav_duration_s',
            'distance_traveled_m', 'avg_speed_mps',
        ]

        # Active goal tracking per robot
        self.active_goals: Dict[str, dict] = {}

        # Map-frame positions of all fleet robots: robot_id -> (x, y)
        self.positions: Dict[str, Optional[tuple]] = {rid: None for rid in self.fleet_robot_ids}

        # Subscriptions for AMCL map-frame pose and odometry fallback
        for rid in self.fleet_robot_ids:
            self.create_subscription(
                PoseWithCovarianceStamped, f'/{rid}/amcl_pose',
                lambda msg, r=rid: self.amcl_pose_callback(msg, r), 10
            )
            self.create_subscription(
                Odometry, f'/{rid}/wheel/odom',
                lambda msg, r=rid: self.odom_callback(msg, r), 10
            )

        # Dashboard / coordination subscriptions
        self.current_mode = 'decentralized'
        self.master_robot_id = 'arjuna_1'

        self.create_subscription(String, '/fleet/mode', self.mode_callback, 10)
        self.create_subscription(String, '/fleet/centralized_master', self.master_callback, 10)
        self.create_subscription(String, '/fleet/task_announcement', self.task_announcement_callback, 10)
        self.create_subscription(String, '/fleet/task_completion', self.task_completion_callback, 10)
        self.create_subscription(String, '/fleet/stop_all', self.stop_all_callback, 10)

        # Claim and completion publishers
        self.claim_pub = self.create_publisher(String, '/fleet/task_claims', 10)
        self.completion_pub = self.create_publisher(String, '/fleet/task_completion', 10)

        # Remote ActionClients for ALL robots in the fleet
        self.nav_clients: Dict[str, ActionClient] = {}
        for rid in self.fleet_robot_ids:
            action_name = f'/{rid}/navigate_to_pose'
            self.nav_clients[rid] = ActionClient(self, NavigateToPose, action_name)

        self.get_logger().info("=" * 60)
        self.get_logger().info(f"Centralized Controller initialized on [{self.robot_id}]")
        self.get_logger().info(f"Fleet robots configured: {self.fleet_robot_ids}")
        self.get_logger().info(f"Nav2 action clients prepared for: {list(self.nav_clients.keys())}")
        self.get_logger().info("=" * 60)

    def amcl_pose_callback(self, msg: PoseWithCovarianceStamped, robot_id: str):
        pos = (msg.pose.pose.position.x, msg.pose.pose.position.y)
        self.positions[robot_id] = pos

    def odom_callback(self, msg: Odometry, robot_id: str):
        pos = (msg.pose.pose.position.x, msg.pose.pose.position.y)
        if self.positions.get(robot_id) is None:
            self.positions[robot_id] = pos

        # Update distance tracking if this robot is executing a task
        if robot_id in self.active_goals:
            info = self.active_goals[robot_id]
            last_p = info.get('last_pose')
            if last_p is not None:
                dx = pos[0] - last_p[0]
                dy = pos[1] - last_p[1]
                info['distance_traveled'] += math.sqrt(dx * dx + dy * dy)
            info['last_pose'] = pos

    def mode_callback(self, msg: String):
        new_mode = msg.data.strip()
        if new_mode in ('decentralized', 'centralized') and new_mode != self.current_mode:
            self.current_mode = new_mode
            self.get_logger().warn(f"Centralized Controller mode set to: {self.current_mode}")

    def master_callback(self, msg: String):
        new_master = msg.data.strip()
        if new_master != self.master_robot_id:
            self.master_robot_id = new_master
            self.get_logger().info(f"Centralized master designated: {self.master_robot_id}")

    def is_active_master(self) -> bool:
        return self.current_mode == 'centralized' and self.master_robot_id == self.robot_id

    def stop_all_callback(self, msg: String):
        self.get_logger().warn("🚨 EMERGENCY STOP received! Cancelling all active goals in centralized fleet.")
        for rid, info in list(self.active_goals.items()):
            handle = info.get('goal_handle')
            if handle is not None:
                try:
                    handle.cancel_goal_async()
                    self.get_logger().warn(f"Cancelled active goal on [{rid}]")
                except Exception as e:
                    self.get_logger().error(f"Error cancelling goal on {rid}: {e}")
        self.active_goals.clear()

    def _log_row(self, row: dict):
        write_header = not Path(self.log_path).exists()
        with open(self.log_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.log_fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow(row)

    def task_announcement_callback(self, msg: String):
        if not self.is_active_master():
            return  # Only active master executes baseline logic

        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            self.get_logger().warn(f"Malformed task announcement: {msg.data}")
            return

        task_id = data['task_id']
        task_x = float(data['x'])
        task_y = float(data['y'])
        heading = float(data.get('heading', 0.0))

        # Check which robots are available (not currently busy)
        available_robots = [
            rid for rid in self.fleet_robot_ids
            if rid not in self.active_goals
        ]
        if not available_robots:
            # If all are busy, consider all robots
            available_robots = self.fleet_robot_ids

        distances = {}
        for rid in available_robots:
            pos = self.positions.get(rid)
            if pos is None:
                self.get_logger().warn(f"No known position for {rid} - skipping.")
                continue
            dx = task_x - pos[0]
            dy = task_y - pos[1]
            distances[rid] = math.sqrt(dx * dx + dy * dy)

        if not distances:
            self.get_logger().error(f"[{task_id}] Cannot assign: no robot positions received!")
            return

        # Choose the nearest robot
        assigned_to = min(distances.items(), key=lambda kv: kv[1])[0]

        self.get_logger().info("=" * 60)
        self.get_logger().info(
            f"🎯 [{task_id}] CENTRALIZED ASSIGNMENT: Sending closest robot [{assigned_to}]"
        )
        for rid, dist in distances.items():
            self.get_logger().info(f"   - {rid}: {dist:.2f} m")
        self.get_logger().info("=" * 60)

        # Publish claim so RViz markers & dashboard update immediately
        claim_msg = String()
        claim_msg.data = json.dumps({
            'task_id': task_id,
            'robot_id': assigned_to,
            'mode': 'centralized'
        })
        self.claim_pub.publish(claim_msg)

        # Log assignment entry
        self._log_row({
            'timestamp': time.time(),
            'task_id': task_id,
            'assigned_to': assigned_to,
            'distances_json': json.dumps({k: round(v, 2) for k, v in distances.items()}),
            'task_x': task_x,
            'task_y': task_y,
            'nav_success': '',
            'nav_duration_s': '',
            'distance_traveled_m': '',
            'avg_speed_mps': '',
        })

        # Remotely command the assigned robot via its Nav2 action client
        self.dispatch_nav_goal(assigned_to, task_id, task_x, task_y, heading)

    def dispatch_nav_goal(self, robot_id: str, task_id: str, x: float, y: float, heading: float = 0.0):
        client = self.nav_clients.get(robot_id)
        if client is None:
            self.get_logger().error(f"No ActionClient for robot {robot_id}!")
            return

        # Allow brief wait for action server discovery
        if not client.wait_for_server(timeout_sec=2.0):
            self.get_logger().error(f"[{task_id}] /{robot_id}/navigate_to_pose server not available or not ready!")
            self._record_nav_result(task_id, robot_id, False, 0.0, 0.0, 0.0)
            return

        goal_msg = NavigateToPose.Goal()
        pose = PoseStamped()
        pose.header.frame_id = self.frame_id
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        # Convert heading yaw to quaternion
        pose.pose.orientation.z = math.sin(heading / 2.0)
        pose.pose.orientation.w = math.cos(heading / 2.0)
        goal_msg.pose = pose

        t0 = time.time()
        self.active_goals[robot_id] = {
            'task_id': task_id,
            'goal_handle': None,
            't0': t0,
            'distance_traveled': 0.0,
            'last_pose': self.positions.get(robot_id),
            'target_x': x,
            'target_y': y,
        }

        send_future = client.send_goal_async(goal_msg)
        send_future.add_done_callback(
            lambda fut: self._nav_goal_response_cb(fut, robot_id, task_id, t0)
        )

    def _nav_goal_response_cb(self, future, robot_id: str, task_id: str, t0: float):
        goal_handle = future.result()
        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error(f"[{task_id}] Goal REJECTED by Nav2 on [{robot_id}]!")
            self.active_goals.pop(robot_id, None)
            dur = time.time() - t0
            self._record_nav_result(task_id, robot_id, False, dur, 0.0, 0.0)
            comp_msg = String()
            comp_msg.data = json.dumps({
                'task_id': task_id,
                'robot_id': robot_id,
                'success': False,
                'duration': round(dur, 3),
                'distance': 0.0,
                'avg_speed': 0.0,
                'timestamp': time.time(),
            })
            self.completion_pub.publish(comp_msg)
            return

        self.get_logger().info(f"[{task_id}] Goal ACCEPTED by Nav2 on [{robot_id}]. Navigating...")
        if robot_id in self.active_goals:
            self.active_goals[robot_id]['goal_handle'] = goal_handle

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            lambda fut: self._nav_result_cb(fut, robot_id, task_id, t0)
        )

    def _nav_result_cb(self, future, robot_id: str, task_id: str, t0: float):
        duration = time.time() - t0
        result = future.result()
        success = (result is not None and result.status == 4)

        info = self.active_goals.pop(robot_id, {})
        distance = info.get('distance_traveled', 0.0)
        avg_speed = distance / duration if duration > 0 else 0.0

        self.get_logger().info("=" * 60)
        self.get_logger().info(
            f"✅ [{task_id}] COMPLETED by [{robot_id}]: success={success}, "
            f"duration={duration:.2f}s, dist={distance:.2f}m, speed={avg_speed:.2f}m/s"
        )
        self.get_logger().info("=" * 60)

        self._record_nav_result(task_id, robot_id, success, duration, distance, avg_speed)

        # Broadcast completion to entire fleet and dashboard
        comp_msg = String()
        comp_msg.data = json.dumps({
            'task_id': task_id,
            'robot_id': robot_id,
            'success': success,
            'duration': round(duration, 3),
            'distance': round(distance, 3),
            'avg_speed': round(avg_speed, 3),
            'timestamp': time.time(),
        })
        self.completion_pub.publish(comp_msg)

    def task_completion_callback(self, msg: String):
        try:
            data = json.loads(msg.data)
            rid = data.get('robot_id')
            tid = data.get('task_id')
            if rid in self.active_goals and self.active_goals[rid].get('task_id') == tid:
                self.active_goals.pop(rid, None)
        except Exception:
            pass

    def _record_nav_result(self, task_id, robot_id, success, duration, distance, avg_speed):
        self._log_row({
            'timestamp': time.time(),
            'task_id': task_id,
            'assigned_to': robot_id,
            'distances_json': '',
            'task_x': '', 'task_y': '',
            'nav_success': success,
            'nav_duration_s': round(duration, 3),
            'distance_traveled_m': round(distance, 3),
            'avg_speed_mps': round(avg_speed, 3),
        })


def main(args=None):
    rclpy.init(args=args)
    node = NearestRobotController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
