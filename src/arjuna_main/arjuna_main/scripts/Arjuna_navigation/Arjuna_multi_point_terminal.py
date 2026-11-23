#!/usr/bin/env python3
"""
Arjuna Multi-Point Waypoint Terminal Node
==========================================
Collects multiple coordinates from terminal input, then sequences them
as Action Goals to Nav2 NavigateToPose.

Usage:
  ros2 run arjuna_main multi_point_terminal
  ros2 run arjuna_main multi_point_terminal --ros-args -p robot_id:=arjuna_1
"""

import sys
import time
import math
import threading
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.signals import SignalHandlerOptions
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from action_msgs.msg import GoalStatus


class MultiPointTerminalNode(Node):
    def __init__(self):
        super().__init__('multi_point_terminal')

        self.declare_parameter('robot_id', 'arjuna_1')
        self.declare_parameter('frame_id', 'map')

        self.robot_id = self.get_parameter('robot_id').value.strip()
        self.frame_id = self.get_parameter('frame_id').value.strip()

        action_name = f'/{self.robot_id}/navigate_to_pose' if self.robot_id else '/navigate_to_pose'
        self.action_client = ActionClient(self, NavigateToPose, action_name)
        self.alt_client = ActionClient(self, NavigateToPose, '/navigate_to_pose')

        self.current_goal_handle = None
        self.goal_done = False
        self.goal_status = None
        self.last_print_time = 0.0

        self.get_logger().info(f"Multi-Point Terminal Node started for [{self.robot_id}]")

    def navigate_to(self, x: float, y: float, heading: float = 0.0) -> bool:
        self.goal_done = False
        self.goal_status = None
        self.last_print_time = 0.0

        client = self.action_client
        if not client.wait_for_server(timeout_sec=3.0):
            if self.alt_client.wait_for_server(timeout_sec=2.0):
                client = self.alt_client
            else:
                self.get_logger().error("Nav2 Action Server not ready!")
                return False

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = self.frame_id
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(x)
        goal_msg.pose.pose.position.y = float(y)
        goal_msg.pose.pose.position.z = 0.0

        goal_msg.pose.pose.orientation.z = math.sin(heading / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(heading / 2.0)

        send_future = client.send_goal_async(
            goal_msg, feedback_callback=self._feedback_cb
        )
        send_future.add_done_callback(self._response_cb)
        return True

    def _response_cb(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Waypoint goal rejected by Nav2!")
            self.goal_done = True
            self.goal_status = GoalStatus.STATUS_ABORTED
            return

        self.current_goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_cb)

    def _feedback_cb(self, feedback_msg):
        now = time.time()
        if now - self.last_print_time >= 2.0:
            dist = feedback_msg.feedback.distance_remaining
            self.get_logger().info(f"Navigating... Distance remaining: {dist:.2f}m")
            self.last_print_time = now

    def _result_cb(self, future):
        self.current_goal_handle = None
        result = future.result()
        self.goal_status = result.status
        self.goal_done = True

    def cancel_current(self):
        if self.current_goal_handle is not None:
            self.current_goal_handle.cancel_goal_async()


def main(args=None):
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = MultiPointTerminalNode()

    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    print("\n===========================================")
    print(" Arjuna Multi-Point Waypoint Sequence CLI   ")
    print("===========================================")
    print("Enter target coordinates one by one.")
    print("Format: 'X Y' or 'X, Y' (e.g. '1.5 2.0')")
    print("Type 'done' or 'run' when finished entering points.")
    print("Type 'quit' or 'q' to exit.")
    print("===========================================\n")

    waypoints = []
    idx = 1
    while True:
        try:
            line = input(f"Waypoint #{idx} > ").strip()
            if not line:
                continue
            if line.lower() in ('done', 'run', 'go', 'start'):
                break
            if line.lower() in ('q', 'quit', 'exit'):
                waypoints = []
                break

            parts = line.replace(',', ' ').split()
            if len(parts) >= 2:
                wx = float(parts[0])
                wy = float(parts[1])
                waypoints.append((wx, wy))
                idx += 1
            else:
                print("Please enter both X and Y separated by a space (e.g. '1.5 2.0')")
        except ValueError:
            print("Invalid coordinates. Please enter numeric values.")
        except (KeyboardInterrupt, EOFError):
            waypoints = []
            break

    if not waypoints:
        print("No waypoints recorded. Exiting.")
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        return

    print(f"\nStarting sequence of {len(waypoints)} waypoints...")
    for i, (wx, wy) in enumerate(waypoints, start=1):
        print(f"\n[Waypoint {i}/{len(waypoints)}] Heading to ({wx:.2f}, {wy:.2f})...")
        if not node.navigate_to(wx, wy):
            print(f"Failed to transmit goal for waypoint {i}. Stopping sequence.")
            break

        try:
            while rclpy.ok() and not node.goal_done:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nSequence interrupted by user. Cancelling waypoint...")
            node.cancel_current()
            break

        if node.goal_status == GoalStatus.STATUS_SUCCEEDED:
            print(f"✓ Waypoint {i} REACHED!")
        else:
            print(f"⚠️ Waypoint {i} terminated with status: {node.goal_status}")

    print("\nWaypoint sequence completed.")
    executor.shutdown()
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
