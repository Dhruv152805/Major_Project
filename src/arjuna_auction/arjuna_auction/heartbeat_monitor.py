#!/usr/bin/env python3
"""
TerrainFleet - Phase 1: Heartbeat / failure detection (+ dashboard soft-kill)

Each robot publishes its own heartbeat on /fleet/heartbeat/<robot_id> at a
fixed rate, and watches every other known robot's heartbeat topic. If a
robot's heartbeat goes silent past the timeout, this node publishes a
failure event on /fleet/robot_failure.

NEW: supports a dashboard-driven "soft kill" - publishing
{"killed": true} on /fleet/soft_kill/<robot_id> makes THIS robot stop
publishing its own heartbeat, which the other robot detects exactly as
if it had actually lost power - same code path, same timing metrics.
This is a SIMULATED fault, distinct from physically powering the robot
off - keep physical power-off as your primary demo; use soft-kill for
repeatable stress-testing.

USAGE (run one instance per robot, with a different robot_id):
  ros2 run arjuna_auction heartbeat_monitor --ros-args \
      -p robot_id:=arjuna_1 \
      -p fleet_robot_ids:="['arjuna_1','arjuna_2']" \
      -p heartbeat_interval_sec:=0.5 \
      -p failure_timeout_sec:=3.0

Dashboard/manual soft-kill test:
  ros2 topic pub /fleet/soft_kill/arjuna_1 std_msgs/String \
      '{data: "{\"killed\": true}"}' --once

  # revive:
  ros2 topic pub /fleet/soft_kill/arjuna_1 std_msgs/String \
      '{data: "{\"killed\": false}"}' --once
"""

import json
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


import sys

class HeartbeatMonitor(Node):
    def __init__(self, node_name: str = 'heartbeat_monitor'):
        super().__init__(node_name)

        self.declare_parameter('robot_id', 'arjuna_unknown')
        self.declare_parameter('fleet_robot_ids', ['arjuna_1', 'arjuna_2'])
        self.declare_parameter('heartbeat_interval_sec', 0.5)
        self.declare_parameter('failure_timeout_sec', 8.0)

        self.robot_id = self.get_parameter('robot_id').value
        self.fleet_robot_ids = self.get_parameter('fleet_robot_ids').value
        self.heartbeat_interval = float(self.get_parameter('heartbeat_interval_sec').value)
        self.failure_timeout = float(self.get_parameter('failure_timeout_sec').value)

        self.other_robot_ids = [r for r in self.fleet_robot_ids if r != self.robot_id]

        # --- Soft-kill state (dashboard-controlled) ---
        self.soft_killed = False
        self.create_subscription(
            String, f'/fleet/soft_kill/{self.robot_id}', self.soft_kill_callback, 10
        )

        # Publisher for own heartbeat
        self.heartbeat_pub = self.create_publisher(
            String, f'/fleet/heartbeat/{self.robot_id}', 10
        )

        # Track peer presence: Only monitor for failure once peer has been seen at least once!
        self.last_seen = {other_id: None for other_id in self.other_robot_ids}
        self.ever_seen = set()
        self.declared_failed = set()
        self.subs = []
        for other_id in self.other_robot_ids:
            sub = self.create_subscription(
                String, f'/fleet/heartbeat/{other_id}',
                lambda msg, rid=other_id: self.heartbeat_callback(msg, rid),
                10
            )
            self.subs.append(sub)

        self.peer_soft_killed = {}
        for other_id in self.other_robot_ids:
            self.create_subscription(
                String, f'/fleet/soft_kill/{other_id}',
                lambda msg, r=other_id: self._peer_soft_kill_cb(msg, r),
                10
            )

        self.failure_pub = self.create_publisher(String, '/fleet/robot_failure', 10)

        self.create_timer(self.heartbeat_interval, self.publish_heartbeat)
        self.create_timer(0.2, self.check_for_failures)

        self.get_logger().info(
            f"HeartbeatMonitor [{node_name}] started for {self.robot_id}, watching {self.other_robot_ids}, "
            f"timeout={self.failure_timeout}s"
        )

    def _peer_soft_kill_cb(self, msg: String, robot_id: str):
        try:
            data = json.loads(msg.data)
            self.peer_soft_killed[robot_id] = bool(data.get('killed', False))
        except Exception:
            pass

    def soft_kill_callback(self, msg: String):
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            self.get_logger().warn(f"Malformed soft_kill message: {msg.data}")
            return
        killed = bool(data.get('killed', False))
        if killed != self.soft_killed:
            self.soft_killed = killed
            if killed:
                self.get_logger().warn(
                    f"{self.robot_id} SOFT-KILLED via dashboard - heartbeat stopping now."
                )
            else:
                self.get_logger().info(
                    f"{self.robot_id} REVIVED via dashboard - heartbeat resuming."
                )

    def publish_heartbeat(self):
        if self.soft_killed:
            return  # simulate death: publish nothing, let the timeout do the rest
        msg = String()
        msg.data = json.dumps({'robot_id': self.robot_id, 'timestamp': time.time()})
        self.heartbeat_pub.publish(msg)

    def heartbeat_callback(self, msg: String, robot_id: str):
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        now = time.time()
        self.last_seen[robot_id] = now
        self.ever_seen.add(robot_id)
        if robot_id in self.declared_failed:
            self.declared_failed.discard(robot_id)
            self.get_logger().info(f"💚 {robot_id} heartbeat resumed - clearing failure state")

    def check_for_failures(self):
        now = time.time()
        for robot_id, last_time in self.last_seen.items():
            # A peer cannot fail if it was never seen online yet
            if last_time is None or robot_id not in self.ever_seen:
                continue

            elapsed = now - last_time
            if elapsed > self.failure_timeout and robot_id not in self.declared_failed:
                self.declared_failed.add(robot_id)
                fault_type = 'simulated' if self.peer_soft_killed.get(robot_id, False) else 'physical'
                self.get_logger().warn(
                    f"⚠️ FAILURE DETECTED ({fault_type}): {robot_id} heartbeat silent for {elapsed:.2f}s "
                    f"(timeout={self.failure_timeout}s)"
                )
                failure_msg = String()
                failure_msg.data = json.dumps({
                    'failed_robot_id': robot_id,
                    'detected_by': self.robot_id,
                    'detection_timestamp': now,
                    'last_seen_timestamp': last_time,
                    'fault_type': fault_type,
                })
                self.failure_pub.publish(failure_msg)


def main(args=None):
    # Parse robot_id from args if passed, to avoid node name collisions in multi-robot DDS graph
    robot_id = 'arjuna_unknown'
    raw_args = sys.argv[1:] if args is None else args
    for a in raw_args:
        if 'robot_id:=' in a:
            robot_id = a.split('robot_id:=')[1].strip("'\"")
            break

    node_name = f'heartbeat_monitor_{robot_id}' if robot_id != 'arjuna_unknown' else 'heartbeat_monitor'

    rclpy.init(args=args)
    node = HeartbeatMonitor(node_name=node_name)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
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
