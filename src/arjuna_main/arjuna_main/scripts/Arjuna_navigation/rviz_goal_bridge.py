#!/usr/bin/env python3
"""
Arjuna RViz Goal Bridge Node
=============================
Bridges RViz 2D Goal Pose clicks directly to Nav2 NavigateToPose Action Server.

Subscribes to:
  - /{robot_id}/goal_pose (from multi-robot RViz)
  - /goal_pose (from standard RViz)
  - /{robot_id}/move_base_simple/goal
  - /move_base_simple/goal

Forwards goals to:
  - /{robot_id}/navigate_to_pose (or /navigate_to_pose)
"""

import math
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose
from action_msgs.msg import GoalStatus


class RvizGoalBridge(Node):
    def __init__(self):
        super().__init__('rviz_goal_bridge')

        self.declare_parameter('robot_id', '')
        self.robot_id = self.get_parameter('robot_id').value.strip()

        # Determine primary action server topic
        if self.robot_id:
            self.action_topic = f'/{self.robot_id}/navigate_to_pose'
            self.alt_action_topic = '/navigate_to_pose'
        else:
            self.action_topic = '/navigate_to_pose'
            self.alt_action_topic = '/arjuna_1/navigate_to_pose'

        self.nav_client = ActionClient(self, NavigateToPose, self.action_topic)
        self.alt_client = ActionClient(self, NavigateToPose, self.alt_action_topic)

        self.active_goal_handle = None
        self.last_feedback_time = 0.0

        # Subscriptions for goal pose
        goal_topics = []
        if self.robot_id:
            goal_topics.append(f'/{self.robot_id}/goal_pose')
            goal_topics.append(f'/{self.robot_id}/move_base_simple/goal')
        goal_topics.extend(['/goal_pose', '/move_base_simple/goal'])

        # Eliminate duplicates preserving order
        unique_topics = []
        for t in goal_topics:
            if t not in unique_topics:
                unique_topics.append(t)

        self.subs = []
        for t in unique_topics:
            sub = self.create_subscription(
                PoseStamped,
                t,
                lambda msg, src=t: self.goal_callback(msg, src),
                10
            )
            self.subs.append(sub)

        # Initial pose monitor
        init_topics = [f'/{self.robot_id}/initialpose'] if self.robot_id else []
        init_topics.append('/initialpose')
        for it in set(init_topics):
            self.create_subscription(
                PoseWithCovarianceStamped,
                it,
                lambda msg, src=it: self.initialpose_callback(msg, src),
                10
            )

        self.get_logger().info(
            f"✓ RViz Goal Bridge initialized for [{self.robot_id or 'global'}]. "
            f"Listening to: {unique_topics} -> {self.action_topic}"
        )

    def initialpose_callback(self, msg: PoseWithCovarianceStamped, source_topic: str):
        pos = msg.pose.pose.position
        self.get_logger().info(
            f"📍 Initial Pose received on [{source_topic}]: ({pos.x:.2f}, {pos.y:.2f}) in '{msg.header.frame_id}'"
        )

    def goal_callback(self, msg: PoseStamped, source_topic: str):
        pos = msg.pose.position
        ori = msg.pose.orientation

        # Calculate yaw for informational display
        siny_cosp = 2.0 * (ori.w * ori.z + ori.x * ori.y)
        cosy_cosp = 1.0 - 2.0 * (ori.y * ori.y + ori.z * ori.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        self.get_logger().info("=" * 60)
        self.get_logger().info(
            f"🎯 RViz Goal received from [{source_topic}]:"
            f" X={pos.x:.2f}, Y={pos.y:.2f}, Heading={math.degrees(yaw):.1f}° (frame: '{msg.header.frame_id}')"
        )

        # Choose responsive action client
        client = self.nav_client
        if not client.server_is_ready():
            if not client.wait_for_server(timeout_sec=1.5):
                # Try fallback action server
                if self.alt_client.wait_for_server(timeout_sec=1.0):
                    client = self.alt_client
                else:
                    self.get_logger().error(
                        f"❌ Nav2 Action Server '{self.action_topic}' is not ready! Is Nav2 stack launched?"
                    )
                    return

        # Cancel any previous executing goal
        if self.active_goal_handle is not None:
            self.get_logger().info("Cancelling previous goal to accept new RViz command...")
            try:
                self.active_goal_handle.cancel_goal_async()
            except Exception:
                pass
            self.active_goal_handle = None

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = msg
        if not goal_msg.pose.header.frame_id:
            goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()

        self.get_logger().info(f"🚀 Transmitting goal to Nav2 action server...")
        send_future = client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        send_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("❌ Goal was REJECTED by Nav2 planner/costmap!")
            return

        self.get_logger().info("✅ Goal ACCEPTED by Nav2! Robot navigating...")
        self.active_goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        now = time.time()
        if now - self.last_feedback_time >= 2.0:
            dist = feedback_msg.feedback.distance_remaining
            rec = feedback_msg.feedback.number_of_recoveries
            rec_str = f" | Recoveries: {rec}" if rec > 0 else ""
            self.get_logger().info(f"Navigating... Distance remaining: {dist:.2f}m{rec_str}")
            self.last_feedback_time = now

    def result_callback(self, future):
        self.active_goal_handle = None
        result = future.result()
        status = result.status

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info("=" * 60)
            self.get_logger().info("🏁 SUCCESS: Goal reached!")
            self.get_logger().info("=" * 60)
        elif status == GoalStatus.STATUS_CANCELED:
            self.get_logger().warn("Goal was canceled.")
        elif status == GoalStatus.STATUS_ABORTED:
            self.get_logger().error("❌ Goal was ABORTED by Nav2. Check obstacles or clearance.")
        else:
            self.get_logger().info(f"Goal completed with status code: {status}")


def main(args=None):
    rclpy.init(args=args)
    node = RvizGoalBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
