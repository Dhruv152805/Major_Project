#!/usr/bin/env python3
"""
Arjuna QR Control & Centering Node
==================================
Subscribes to QR tracking commands and fuses them with raw LIDAR scans to execute
rotational and linear alignment to center on a detected QR code while ensuring safety.

-----------------------------------------------------------------------------------------
ARCHITECTURE & CONTROL FLOW:
1. Command Input:
   - Subscribes to '/arjuna/qr_tracking/command' (std_msgs/String), which receives steering
     directions ('left', 'center', 'right', 'stop') from the QR tracking computer vision node.
2. Safety Override (LIDAR Integration):
   - Subscribes to '/scan' (sensor_msgs/LaserScan) to detect close obstacles.
   - The RPLidar is physically mounted rotated 180° (backward-facing) on the chassis.
   - The scan angles are remapped by 180° to read front-facing sectors:
     * 'front_left':  180° to 240° relative to the physical front
     * 'front_right': 120° to 180° relative to the physical front
     * 'f_left':      240° to 300° relative to the physical front
     * 'f_right':     60° to 120° relative to the physical front
   - Filters out scans < 0.38m to prevent false triggers from chassis self-reflections.
   - Priority 1 Safety: If any obstacle is found within OBSTACLE_THRESHOLD (0.35m),
     all motion commands are overridden and velocity is forced to zero immediately.
3. Hysteresis & Loop Timer:
   - Evaluates commands in a 20Hz timer callback (every 0.05 seconds) for low latency.
   - Publishes final Twist commands directly to '/cmd_vel'.

Company: NEWRRO TECH LLP
Website: www.newrro.in
-----------------------------------------------------------------------------------------
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
import time

# Controller Parameters
LINEAR_VELOCITY = 0.5       # Forward speed (m/s) when centering
ANGULAR_VELOCITY = 0.7      # Rotational speed (rad/s) when turning to align
OBSTACLE_THRESHOLD = 0.35   # Safety stop threshold in meters (35cm)

class QRController(Node):
    def __init__(self):
        super().__init__('arjuna_qr_controller')
        
        # State tracking variables
        self.current_command = "stop"
        self.obstacle_detected = False
        self.regions = {}
        
        # Diagnostics
        self.command_count = 0
        self.obstacle_count = 0
        self.start_time = time.time()
        
        # Subscribe to vision commands
        self.qr_cmd_sub = self.create_subscription(
            String,
            '/arjuna/qr_tracking/command',
            self.qr_command_callback,
            10)
        
        # Subscribe to LIDAR scan
        self.laser_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.laser_callback,
            10)
        
        # Publisher for motor control
        self.cmd_vel_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10)
        
        # Main control loop timer (20Hz)
        self.timer = self.create_timer(0.05, self.control_loop)
        
        # Diagnostic statistics timer (every 5 seconds)
        self.stats_timer = self.create_timer(5.0, self.print_stats)
        
        self.get_logger().info("")
        self.get_logger().info("=" * 60)
        self.get_logger().info("ARJUNA QR CONTROLLER - ACTIVE")
        self.get_logger().info("=" * 60)
        self.get_logger().info(f"Linear velocity: {LINEAR_VELOCITY} m/s")
        self.get_logger().info(f"Angular velocity: {ANGULAR_VELOCITY} rad/s")
        self.get_logger().info(f"Obstacle threshold: {OBSTACLE_THRESHOLD} m")
        self.get_logger().info("Subscribes: /arjuna/qr_tracking/command, /scan")
        self.get_logger().info("Publishes: /cmd_vel")
        self.get_logger().info("=" * 60)
        self.get_logger().info("Waiting for QR tracking commands...")
        self.get_logger().info("=" * 60)
        self.get_logger().info("")
    
    def qr_command_callback(self, msg):
        """Receives visual tracking commands from the camera processing node."""
        new_command = msg.data
        
        if new_command != self.current_command:
            self.current_command = new_command
            self.command_count += 1
            
            if new_command != "stop":
                self.get_logger().info(f"QR Command: {new_command.upper()}")
    
    def laser_callback(self, msg):
        """
        Processes LIDAR data to detect obstacles in critical sectors,
        remapping indexes for the 180° rotation offset.
        """
        num_ranges = len(msg.ranges)
        
        if num_ranges == 0:
            return
        
        def get_region_min(start_fraction, end_fraction):
            """Computes minimum range, applying reflection filters (< 0.38m)."""
            start_idx = int(num_ranges * start_fraction)
            end_idx = int(num_ranges * end_fraction)
            if start_idx >= end_idx or end_idx > num_ranges:
                return 10.0
            region_ranges = msg.ranges[start_idx:end_idx]
            if len(region_ranges) == 0:
                return 10.0
            
            # Apply 0.38m chassis self-reflection filter
            valid_ranges = [r for r in region_ranges if 0.38 < r < 10.0]
            return min(valid_ranges) if valid_ranges else 10.0
         
        # Remap scan indices by 180 degrees to align with physical robot front
        self.regions = {
            'front_left':  get_region_min(0.5, 0.667),     # 180-240° (Robot Front-Left)
            'front_right': get_region_min(0.333, 0.5),     # 120-180° (Robot Front-Right)
            'f_left':      get_region_min(0.667, 0.833),   # 240-300° (Robot Left)
            'f_right':     get_region_min(0.167, 0.333)    # 60-120° (Robot Right)
        }
        
        # Check if an obstacle is within threshold in any front-facing sector
        self.obstacle_detected = (
            self.regions['front_left'] < OBSTACLE_THRESHOLD or
            self.regions['front_right'] < OBSTACLE_THRESHOLD or
            self.regions['f_left'] < OBSTACLE_THRESHOLD or
            self.regions['f_right'] < OBSTACLE_THRESHOLD
        )
        
        if self.obstacle_detected:
            self.obstacle_count += 1
    
    def control_loop(self):
        """
        Main execution loop (20Hz).
        Applies safety overrides first, then visual centering commands.
        """
        cmd = Twist()
        
        # PRIORITY 1: Obstacle Safety Override
        if self.obstacle_detected:
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
            
            if not hasattr(self, '_obstacle_warned'):
                self.get_logger().warn("⚠ OBSTACLE DETECTED - Stopping centering action.")
                self._obstacle_warned = True
        
        # PRIORITY 2: Centering Control commands
        else:
            if hasattr(self, '_obstacle_warned'):
                delattr(self, '_obstacle_warned')
            
            if self.current_command == "left":
                # Rotate left to align target QR
                cmd.linear.x = 0.0
                cmd.angular.z = ANGULAR_VELOCITY
            
            elif self.current_command == "center":
                # Target centered - drive forward
                cmd.linear.x = LINEAR_VELOCITY
                cmd.angular.z = 0.0
            
            elif self.current_command == "right":
                # Rotate right to align target QR
                cmd.linear.x = 0.0
                cmd.angular.z = -ANGULAR_VELOCITY
            
            elif self.current_command == "stop":
                # Target lost or stop requested
                cmd.linear.x = 0.0
                cmd.angular.z = 0.0
        
        # Publish Twist message
        self.cmd_vel_pub.publish(cmd)
    
    def print_stats(self):
        """Outputs statistical diagnostics to console."""
        elapsed = time.time() - self.start_time
        
        self.get_logger().info(
            f"Stats | Commands received: {self.command_count} | "
            f"Obstacles detected: {self.obstacle_count} | "
            f"Current cmd: {self.current_command.upper()} | "
            f"Obstacle active: {'YES' if self.obstacle_detected else 'NO'}"
        )
    
    def cleanup(self):
        """Stops the robot on shutdown."""
        stop_cmd = Twist()
        stop_cmd.linear.x = 0.0
        stop_cmd.angular.z = 0.0
        self.cmd_vel_pub.publish(stop_cmd)
        self.get_logger().info("Robot stopped - QR Controller shutdown.")

def main(args=None):
    rclpy.init(args=args)
    
    try:
        controller = QRController()
        rclpy.spin(controller)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'controller' in locals():
            controller.cleanup()
            controller.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()