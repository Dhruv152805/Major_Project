#!/usr/bin/env python3
"""
Arjuna Multi-Robot Fleet Goal Dispatcher
=========================================
Allows sending goals to:
  - Robot 1 (arjuna_1)
  - Robot 2 (arjuna_2)
  - Both robots simultaneously with different goal coordinates

Usage:
  Interactive Menu:
    ./scripts/send_fleet_goal.py

  Direct CLI commands:
    ./scripts/send_fleet_goal.py --robot arjuna_1 --x 2.0 --y 1.0
    ./scripts/send_fleet_goal.py --robot arjuna_2 --x 4.0 --y -1.5
    ./scripts/send_fleet_goal.py --both --r1 2.0 1.0 --r2 4.0 -1.5
"""

import sys
import math
import time
import argparse
import threading

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.signals import SignalHandlerOptions
from nav2_msgs.action import NavigateToPose
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped


STATUS_STRINGS = {
    GoalStatus.STATUS_UNKNOWN: "UNKNOWN",
    GoalStatus.STATUS_ACCEPTED: "ACCEPTED",
    GoalStatus.STATUS_EXECUTING: "EXECUTING",
    GoalStatus.STATUS_CANCELING: "CANCELING",
    GoalStatus.STATUS_SUCCEEDED: "SUCCEEDED",
    GoalStatus.STATUS_CANCELED: "CANCELED",
    GoalStatus.STATUS_ABORTED: "ABORTED",
}


class SingleRobotGoalClient:
    def __init__(self, node: Node, robot_id: str):
        self.node = node
        self.robot_id = robot_id
        action_name = f'/{robot_id}/navigate_to_pose'
        self.action_client = ActionClient(node, NavigateToPose, action_name)
        self.goal_handle = None
        self.done = False
        self.status = GoalStatus.STATUS_UNKNOWN
        self.distance_remaining = None
        self.last_feedback_print = 0.0

    def wait_for_server(self, timeout_sec=5.0):
        return self.action_client.wait_for_server(timeout_sec=timeout_sec)

    def send_goal(self, x: float, y: float, frame_id='map'):
        self.done = False
        self.status = GoalStatus.STATUS_UNKNOWN
        self.distance_remaining = None

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = frame_id
        goal_msg.pose.header.stamp = self.node.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(x)
        goal_msg.pose.pose.position.y = float(y)
        goal_msg.pose.pose.position.z = 0.0
        goal_msg.pose.pose.orientation.w = 1.0

        print(f"[{self.robot_id}] Transmitting goal (X: {x:.2f}, Y: {y:.2f}) to /{self.robot_id}/navigate_to_pose...")
        send_future = self.action_client.send_goal_async(
            goal_msg, feedback_callback=self._feedback_cb
        )
        send_future.add_done_callback(self._response_cb)

    def _response_cb(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            print(f"[{self.robot_id}] ❌ Goal REJECTED by Nav2!")
            self.done = True
            self.status = GoalStatus.STATUS_ABORTED
            return
        print(f"[{self.robot_id}] ✅ Goal ACCEPTED by Nav2.")
        self.goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_cb)

    def _feedback_cb(self, feedback_msg):
        dist = feedback_msg.feedback.distance_remaining
        self.distance_remaining = dist
        now = time.time()
        if now - self.last_feedback_print >= 2.0:
            rec = feedback_msg.feedback.number_of_recoveries
            rec_str = f" (recoveries: {rec})" if rec > 0 else ""
            print(f"[{self.robot_id}] Remaining distance: {dist:.2f} m{rec_str}")
            self.last_feedback_print = now

    def _result_cb(self, future):
        result = future.result()
        self.status = result.status
        self.done = True
        status_name = STATUS_STRINGS.get(self.status, f"CODE {self.status}")
        if self.status == GoalStatus.STATUS_SUCCEEDED:
            print(f"[{self.robot_id}] 🏁 SUCCESS: Goal reached!")
        else:
            print(f"[{self.robot_id}] ⚠️ Completed with status: {status_name}")

    def cancel(self):
        if self.goal_handle is not None and not self.done:
            print(f"[{self.robot_id}] Canceling goal...")
            self.goal_handle.cancel_goal_async()


def run_fleet_navigator(r1_goal=None, r2_goal=None):
    """
    Coordinates goals to Robot 1 and/or Robot 2.
    r1_goal: (x, y) tuple or None
    r2_goal: (x, y) tuple or None
    """
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = Node('fleet_goal_dispatcher')

    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    clients = []
    if r1_goal is not None:
        c1 = SingleRobotGoalClient(node, 'arjuna_1')
        clients.append((c1, r1_goal[0], r1_goal[1]))
    if r2_goal is not None:
        c2 = SingleRobotGoalClient(node, 'arjuna_2')
        clients.append((c2, r2_goal[0], r2_goal[1]))

    try:
        # Check availability of Action Servers
        for client, _, _ in clients:
            print(f"Checking Nav2 connection for '{client.robot_id}'...")
            if not client.wait_for_server(timeout_sec=4.0):
                print(f"❌ Error: Nav2 action server '/{client.robot_id}/navigate_to_pose' is not responding.")
                print(f"   Make sure bringup_launch.py with robot_id:={client.robot_id} is running.")
                return False

        # Dispatch goals
        for client, gx, gy in clients:
            client.send_goal(gx, gy)

        # Wait until all targets are done
        while rclpy.ok() and not all(c.done for c, _, _ in clients):
            time.sleep(0.2)

        print("\nAll dispatched goals finished.")
        return True

    except KeyboardInterrupt:
        print("\n[Ctrl+C] Canceling all active robot goals...")
        for client, _, _ in clients:
            client.cancel()
        time.sleep(1.0)
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


def interactive_menu():
    while True:
        print("\n" + "=" * 50)
        print("   Arjuna Multi-Robot Fleet Goal Dispatcher   ")
        print("=" * 50)
        print(" 1. Send goal to Robot 1 (arjuna_1)")
        print(" 2. Send goal to Robot 2 (arjuna_2)")
        print(" 3. Send DIFFERENT goals to BOTH robots simultaneously")
        print(" 4. Exit")
        print("=" * 50)
        choice = input("Enter choice (1-4): ").strip()

        if choice == '1':
            try:
                x = float(input("Enter X coordinate for Robot 1 (meters): "))
                y = float(input("Enter Y coordinate for Robot 1 (meters): "))
                run_fleet_navigator(r1_goal=(x, y))
            except ValueError:
                print("Invalid numeric coordinate.")

        elif choice == '2':
            try:
                x = float(input("Enter X coordinate for Robot 2 (meters): "))
                y = float(input("Enter Y coordinate for Robot 2 (meters): "))
                run_fleet_navigator(r2_goal=(x, y))
            except ValueError:
                print("Invalid numeric coordinate.")

        elif choice == '3':
            try:
                print("\n-- Robot 1 (arjuna_1) Target --")
                x1 = float(input("Enter X for Robot 1: "))
                y1 = float(input("Enter Y for Robot 1: "))
                print("\n-- Robot 2 (arjuna_2) Target --")
                x2 = float(input("Enter X for Robot 2: "))
                y2 = float(input("Enter Y for Robot 2: "))
                print("\nLaunching simultaneous goals to both robots...")
                run_fleet_navigator(r1_goal=(x1, y1), r2_goal=(x2, y2))
            except ValueError:
                print("Invalid numeric coordinate.")

        elif choice == '4' or choice.lower() == 'q':
            print("Exiting.")
            break
        else:
            print("Invalid option. Please choose 1, 2, 3, or 4.")


def main():
    parser = argparse.ArgumentParser(description="Dispatch goals to arjuna_1 and/or arjuna_2")
    parser.add_argument('--robot', choices=['arjuna_1', 'arjuna_2'], help="Target robot ID")
    parser.add_argument('--x', type=float, help="Goal X coordinate (map frame)")
    parser.add_argument('--y', type=float, help="Goal Y coordinate (map frame)")
    parser.add_argument('--both', action='store_true', help="Send goals to both robots")
    parser.add_argument('--r1', nargs=2, type=float, metavar=('X', 'Y'), help="Robot 1 goal: X Y")
    parser.add_argument('--r2', nargs=2, type=float, metavar=('X', 'Y'), help="Robot 2 goal: X Y")

    args = parser.parse_args()

    if args.both or (args.r1 and args.r2):
        if not args.r1 or not args.r2:
            print("Error: When using --both, provide both --r1 X Y and --r2 X Y.")
            sys.exit(1)
        run_fleet_navigator(r1_goal=(args.r1[0], args.r1[1]), r2_goal=(args.r2[0], args.r2[1]))
    elif args.robot:
        if args.x is None or args.y is None:
            print(f"Error: Specify --x and --y when targeting {args.robot}.")
            sys.exit(1)
        if args.robot == 'arjuna_1':
            run_fleet_navigator(r1_goal=(args.x, args.y))
        else:
            run_fleet_navigator(r2_goal=(args.x, args.y))
    else:
        interactive_menu()


if __name__ == '__main__':
    main()
