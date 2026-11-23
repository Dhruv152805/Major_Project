#!/usr/bin/env python3
"""
TerrainFleet Home Pose Initializer
==================================
Reads fleet_config.yaml (created by record_points.py) and publishes
the initial pose for each robot to its respective AMCL initialpose topic:
  - /{robot_id}/initialpose (e.g., /arjuna_1/initialpose, /arjuna_2/initialpose)

This eliminates the need to manually click "2D Pose Estimate" in RViz
at the start of every experimental session.

Usage:
  ros2 run arjuna_auction set_home_poses
  ros2 run arjuna_auction set_home_poses --config fleet_config.yaml
  ./set_home_poses.py
"""

import os
import sys
import math
import time
import yaml
import argparse
from pathlib import Path

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped


def yaw_to_quaternion(yaw: float):
    """Converts a planar 2D yaw angle (radians) to a ROS quaternion (x, y, z, w)."""
    half = yaw * 0.5
    return 0.0, 0.0, math.sin(half), math.cos(half)


class SetHomePosesNode(Node):
    def __init__(self, config_path: str):
        super().__init__('set_home_poses')
        cfg_file = Path(config_path)
        if not cfg_file.exists():
            ws_cfg = Path(__file__).resolve().parents[3] / config_path
            if ws_cfg.exists():
                cfg_file = ws_cfg
            else:
                self.get_logger().error(f"Configuration file not found: {config_path}")
                self.get_logger().error("Please run './scripts/record_points.py --home' first!")
                sys.exit(1)

        with open(cfg_file, 'r') as f:
            self.config = yaml.safe_load(f)

        if not isinstance(self.config, dict) or not self.config:
            self.get_logger().error(f"Invalid YAML structure in {config_path}")
            sys.exit(1)

        self.publishers_dict = {}
        for robot_id in self.config.keys():
            topic_name = f'/{robot_id}/initialpose'
            pub = self.create_publisher(PoseWithCovarianceStamped, topic_name, 10)
            self.publishers_dict[robot_id] = pub

        self.get_logger().info("=" * 60)
        self.get_logger().info(f"Loaded fleet home configuration from: {config_path}")
        for robot_id, data in self.config.items():
            self.get_logger().info(
                f"  [{robot_id}] -> x: {data.get('x', 0.0):.2f}m, "
                f"y: {data.get('y', 0.0):.2f}m, "
                f"heading: {data.get('heading', 0.0):.4f} rad "
                f"({math.degrees(data.get('heading', 0.0)):.1f}°)"
            )
        self.get_logger().info("=" * 60)

    def dispatch_poses(self, repeat_count: int = 5, interval_sec: float = 0.25):
        """Dispatches initial poses multiple times to ensure AMCL receives them over Wi-Fi."""
        self.get_logger().info(f"Broadcasting initial poses to AMCL ({repeat_count} bursts)...")

        for burst in range(repeat_count):
            now_msg = self.get_clock().now().to_msg()
            for robot_id, data in self.config.items():
                x = float(data.get('x', 0.0))
                y = float(data.get('y', 0.0))
                yaw = float(data.get('heading', 0.0))
                qx, qy, qz, qw = yaw_to_quaternion(yaw)

                msg = PoseWithCovarianceStamped()
                msg.header.stamp = now_msg
                msg.header.frame_id = 'map'

                msg.pose.pose.position.x = x
                msg.pose.pose.position.y = y
                msg.pose.pose.position.z = 0.0
                msg.pose.pose.orientation.x = qx
                msg.pose.pose.orientation.y = qy
                msg.pose.pose.orientation.z = qz
                msg.pose.pose.orientation.w = qw

                # Standard 6x6 covariance matrix (flattened 36 items)
                # Position variance: 0.25 m^2 (sigma = 0.5m)
                # Yaw variance: 0.068 rad^2 (approx 15 degrees)
                cov = [0.0] * 36
                cov[0] = 0.25    # var(x)
                cov[7] = 0.25    # var(y)
                cov[35] = 0.068  # var(yaw)
                msg.pose.covariance = cov

                self.publishers_dict[robot_id].publish(msg)

            time.sleep(interval_sec)

        self.get_logger().info("=" * 60)
        self.get_logger().info("✅ Starting poses transmitted successfully!")
        self.get_logger().info("Next steps:")
        self.get_logger().info("  1. Check RViz on your laptop to verify scan alignments with map walls.")
        self.get_logger().info("  2. If scan is slightly offset, drive the robot forward/turn slightly to let AMCL settle.")
        self.get_logger().info("=" * 60)


def main(args=None):
    parser = argparse.ArgumentParser(description="Set starting poses from fleet_config.yaml")
    parser.add_argument(
        '--config', '-c', type=str, default='fleet_config.yaml',
        help="Path to fleet_config.yaml (default: fleet_config.yaml)"
    )

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
    node = SetHomePosesNode(config_path=parsed.config)
    try:
        node.dispatch_poses(repeat_count=5, interval_sec=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
