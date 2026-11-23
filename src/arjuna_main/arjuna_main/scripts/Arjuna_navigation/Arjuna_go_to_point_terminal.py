#!/usr/bin/env python3
"""
Arjuna Go-To-Point Terminal Node
=================================
Allows commanding the Arjuna robot to a single 2D target (X, Y) via terminal input.
Communicates directly with the Nav2 NavigateToPose Action Server.

Usage:
  ros2 run arjuna_main go_to_point_terminal
  ros2 run arjuna_main go_to_point_terminal --ros-args -p robot_id:=arjuna_1
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


class GoToPointTerminalNode(Node):
    def __init__(self):
        super().__init__('go_to_point_terminal')

        self.declare_parameter('robot_id', 'arjuna_1')
        self.declare_parameter('frame_id', 'map')

        self.robot_id = self.get_parameter('robot_id').value.strip()
        self.frame_id = self.get_parameter('frame_id').value.strip()

        action_name = f'/{self.robot_id}/navigate_to_pose' if self.robot_id else '/navigate_to_pose'
        self.action_client = ActionClient(self, NavigateToPose, action_name)
        self.alt_client = ActionClient(self, NavigateToPose, '/navigate_to_pose')

        self.goal_done = False
        self.goal_status = None
        self.last_print_time = 0.0

        self.get_logger().info(f"Go-To-Point Terminal Node started for [{self.robot_id}] (action: {action_name})")

    def send_goal(self, x: float, y: float, heading: float = 0.0) -> bool:
        self.goal_done = False
        self.goal_status = None
        self.last_print_time = 0.0

        client = self.action_client
        if not client.wait_for_server(timeout_sec=3.0):
            if self.alt_client.wait_for_server(timeout_sec=2.0):
                client = self.alt_client
            else:
                self.get_logger().error("Nav2 Action Server not available! Ensure bringup or mapping is running.")
                return False

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = self.frame_id
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(x)
        goal_msg.pose.pose.position.y = float(y)
        goal_msg.pose.pose.position.z = 0.0

        # Orientation quaternion from yaw
        goal_msg.pose.pose.orientation.z = math.sin(heading / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(heading / 2.0)

        self.get_logger().info(f"Sending goal ({x:.2f}, {y:.2f}) in '{self.frame_id}' frame...")
        send_future = client.send_goal_async(
            goal_msg,
            feedback_callback=self._feedback_cb
        )
        send_future.add_done_callback(self._response_cb)
        return True

    def _response_cb(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Goal rejected by Nav2!")
            self.goal_done = True
            self.goal_status = GoalStatus.STATUS_ABORTED
            return

        self.get_logger().info("Goal accepted by Nav2. Navigating...")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_cb)

    def _feedback_cb(self, feedback_msg):
        now = time.time()
        if now - self.last_print_time >= 1.5:
            dist = feedback_msg.feedback.distance_remaining
            rec = feedback_msg.feedback.number_of_recoveries
            rec_str = f" | Recoveries: {rec}" if rec > 0 else ""
            self.get_logger().info(f"Progress: Remaining distance = {dist:.2f}m{rec_str}")
            self.last_print_time = now

    def _result_cb(self, future):
        result = future.result()
        self.goal_status = result.status
        self.goal_done = True


def main(args=None):
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = GoToPointTerminalNode()

    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    print("\n===========================================")
    print(" Arjuna Go-To-Point Single Terminal Node   ")
    print("===========================================")

    try:
        while rclpy.ok():
            try:
                line_x = input("\nEnter goal X coordinate (or 'q' to quit): ").strip()
                if line_x.lower() in ('q', 'exit', 'quit'):
                    break
                x = float(line_x)
                y = float(input("Enter goal Y coordinate: ").strip())
                yaw_deg_str = input("Enter target heading degrees (default 0.0): ").strip()
                yaw_rad = math.radians(float(yaw_deg_str)) if yaw_deg_str else 0.0
            except ValueError:
                print("Invalid input. Please enter numbers.")
                continue
            except (KeyboardInterrupt, EOFError):
                break

            if not node.send_goal(x, y, yaw_rad):
                continue

            try:
                while rclpy.ok() and not node.goal_done:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("Navigation canceled by user.")
                continue

            if node.goal_status == GoalStatus.STATUS_SUCCEEDED:
                print("✓ GOAL REACHED SUCCESSFULLY!")
            elif node.goal_status == GoalStatus.STATUS_ABORTED:
                print("✗ GOAL ABORTED by Nav2.")
            else:
                print(f"Goal terminated with status code: {node.goal_status}")

    finally:
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
