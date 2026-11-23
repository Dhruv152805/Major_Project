#!/usr/bin/env python3
"""
TerrainFleet Task Marker RViz Visualizer Node
=============================================
Runs on the control laptop. Listens to fleet task announcements, claims,
and completions, and publishes interactive 3D RViz markers on:
  /fleet/task_markers (visualization_msgs/msg/MarkerArray)

Color Legend:
  - Gray / Amber : Announced / Auction in Progress
  - Red          : Won & Executing by arjuna_1 (matches red scan)
  - Cyan         : Won & Executing by arjuna_2 (matches cyan scan)
  - Green        : Succeeded / Finished
  - Orange       : Re-auction in progress (peer failure detected)

Usage:
  ros2 run arjuna_auction task_marker_node
"""

import json
import time
from typing import Dict, Any

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point


# Color definitions (RGBA normalized 0.0 - 1.0)
COLORS = {
    'announced': (0.8, 0.8, 0.2, 0.7),     # Yellow / Gold
    'arjuna_1':  (0.95, 0.15, 0.15, 0.9),  # Bright Red
    'arjuna_2':  (0.0, 0.85, 0.95, 0.9),   # Bright Cyan
    'completed': (0.15, 0.85, 0.25, 0.9),  # Bright Green
    'reauction': (1.0, 0.5, 0.0, 0.95),    # Vibrant Orange
    'default':   (0.6, 0.6, 0.6, 0.6),     # Neutral Gray
}


class TaskMarkerNode(Node):
    def __init__(self):
        super().__init__('task_marker_node')

        self.tasks: Dict[str, Dict[str, Any]] = {}
        # task_id -> {
        #   'x': float, 'y': float, 'heading': float,
        #   'status': 'announced'|'claimed'|'completed'|'reauction',
        #   'winner': str|None, 'id_int': int
        # }
        self.next_id_counter = 0

        # Subscriptions
        self.create_subscription(
            String, '/fleet/task_announcement', self.task_announcement_cb, 10
        )
        self.create_subscription(
            String, '/fleet/task_claims', self.task_claim_cb, 10
        )
        self.create_subscription(
            String, '/fleet/robot_failure', self.robot_failure_cb, 10
        )

        # Publisher for RViz MarkerArray
        self.marker_pub = self.create_publisher(MarkerArray, '/fleet/task_markers', 10)

        # Timer to regularly publish markers for RViz late-joiners
        self.create_timer(1.0, self.publish_markers)

        self.get_logger().info("=" * 60)
        self.get_logger().info("🎨 TASK MARKER NODE INITIALIZED")
        self.get_logger().info("Publishing RViz visualization markers on: /fleet/task_markers")
        self.get_logger().info("  • Red: arjuna_1 | Cyan: arjuna_2 | Yellow: Announced | Green: Done")
        self.get_logger().info("=" * 60)

    def task_announcement_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            tid = data['task_id']
            x = float(data['x'])
            y = float(data['y'])
            heading = float(data.get('heading', 0.0))
            is_reauction = bool(data.get('is_reauction', False))

            if tid not in self.tasks:
                self.tasks[tid] = {
                    'x': x, 'y': y, 'heading': heading,
                    'status': 'reauction' if is_reauction else 'announced',
                    'winner': None,
                    'id_int': self.next_id_counter
                }
                self.next_id_counter += 1
            else:
                self.tasks[tid]['status'] = 'reauction' if is_reauction else 'announced'
                self.tasks[tid]['winner'] = None

            self.get_logger().info(f"📍 Marker updated for [{tid}]: status={self.tasks[tid]['status']}")
            self.publish_markers()
        except Exception as e:
            self.get_logger().warn(f"Error parsing task announcement: {e}")

    def task_claim_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            tid = data.get('task_id')
            rid = data.get('robot_id')

            if tid in self.tasks:
                self.tasks[tid]['winner'] = rid
                self.tasks[tid]['status'] = 'claimed'
                self.get_logger().info(f"🎯 Marker [{tid}] colored for winner [{rid}]")
                self.publish_markers()
        except Exception as e:
            self.get_logger().warn(f"Error parsing task claim: {e}")

    def robot_failure_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            failed_id = data.get('failed_robot_id')
            # Mark any active task by failed robot as reauction
            for tid, tinfo in self.tasks.items():
                if tinfo.get('winner') == failed_id and tinfo.get('status') == 'claimed':
                    tinfo['status'] = 'reauction'
                    tinfo['winner'] = None
                    self.get_logger().warn(f"⚠️ Task [{tid}] marked for re-auction due to failure of [{failed_id}]")
            self.publish_markers()
        except Exception as e:
            self.get_logger().warn(f"Error handling failure in markers: {e}")

    def publish_markers(self):
        if not self.tasks:
            return

        marker_array = MarkerArray()
        now = self.get_clock().now().to_msg()

        for tid, info in self.tasks.items():
            base_id = info['id_int'] * 2

            # Determine color
            winner = info.get('winner')
            status = info.get('status')

            if status == 'reauction':
                rgba = COLORS['reauction']
                status_text = "RE-AUCTION"
            elif status == 'claimed' and winner in COLORS:
                rgba = COLORS[winner]
                status_text = f"Won by {winner}"
            elif status == 'completed':
                rgba = COLORS['completed']
                status_text = "Completed"
            else:
                rgba = COLORS['announced']
                status_text = "Pending"

            # 1. Floor Cylinder / Disc Marker
            disc = Marker()
            disc.header.frame_id = 'map'
            disc.header.stamp = now
            disc.ns = 'task_points'
            disc.id = base_id
            disc.type = Marker.CYLINDER
            disc.action = Marker.ADD
            disc.pose.position.x = info['x']
            disc.pose.position.y = info['y']
            disc.pose.position.z = 0.02
            disc.pose.orientation.w = 1.0
            disc.scale.x = 0.35  # diameter 35cm
            disc.scale.y = 0.35
            disc.scale.z = 0.04  # thickness 4cm
            disc.color.r = rgba[0]
            disc.color.g = rgba[1]
            disc.color.b = rgba[2]
            disc.color.a = rgba[3]
            marker_array.markers.append(disc)

            # 2. 3D Floating Text Label above disc
            text_marker = Marker()
            text_marker.header.frame_id = 'map'
            text_marker.header.stamp = now
            text_marker.ns = 'task_labels'
            text_marker.id = base_id + 1
            text_marker.type = Marker.TEXT_VIEW_FACING
            text_marker.action = Marker.ADD
            text_marker.pose.position.x = info['x']
            text_marker.pose.position.y = info['y']
            text_marker.pose.position.z = 0.30  # floating 30cm up
            text_marker.pose.orientation.w = 1.0
            text_marker.scale.z = 0.16  # text height
            text_marker.color.r = 1.0
            text_marker.color.g = 1.0
            text_marker.color.b = 1.0
            text_marker.color.a = 1.0
            text_marker.text = f"{tid}\n({status_text})"
            marker_array.markers.append(text_marker)

        self.marker_pub.publish(marker_array)


def main(args=None):
    rclpy.init(args=args)
    node = TaskMarkerNode()
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
