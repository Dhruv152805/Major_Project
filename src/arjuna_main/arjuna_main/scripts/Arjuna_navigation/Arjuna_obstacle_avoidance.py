#!/usr/bin/env python3
"""
Arjuna Autonomous Obstacle Avoidance Node
=========================================
Implements real-time, sector-based reactive obstacle avoidance for the Arjuna robot.
This node acts as a local safety override by subscribing to raw LIDAR scan data, 
identifying close-range obstacles, and publishing Twist velocity commands to '/cmd_vel'.

-----------------------------------------------------------------------------------------
ARCHITECTURE & CONTROL FLOW:
1. Data Input:
   - Subscribes to '/scan' (sensor_msgs/LaserScan) published by RPLidar/SLlidar.
2. Sector Processing & 180° Yaw Correction:
   - The LIDAR sensor is physically mounted rotated 180° (backward-facing) on the robot chassis.
   - The global TF handles this via static transforms (yaw = 3.14159265 in bringup_launch.py).
   - In this local python script, raw scan data indices must be remapped to find the physical front.
   - On a typical RPLidar, index 0 is the back of the sensor (which points forward physically).
   - We divide the scan array into 4 forward-facing sectors:
     * 'fright':   90° to 135° relative to the physical front
     * 'front_R':  135° to 180° relative to the physical front
     * 'front_L':  180° to 225° relative to the physical front
     * 'fleft':    225° to 270° relative to the physical front
3. Noise & Chassis Reflection Filter:
   - Readings < 0.38 meters are discarded to prevent the robot's own metal/acrylic chassis 
     frame from causing false-positive obstacle detection.
4. Stateful Reactive Avoidance (State Machine):
   - If obstacles are detected within OBSTACLE_DIST_THRESHOLD (0.5m), the node enters 
     stateful avoidance mode (avoiding=True) and executes a specific maneuver (backup, turn_left, etc.).
   - To prevent erratic oscillation, a hysteresis minimum duration (min_avoidance_time) is enforced.
   - Once the path is verified clear beyond SAFE_DISTANCE (0.7m), normal navigation resumes.

Company: NEWRRO TECH LLP
Website: www.newrro.in
-----------------------------------------------------------------------------------------
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
import time

# Control Tuning Constants
OBSTACLE_DIST_THRESHOLD = 0.5  # Distance threshold to trigger obstacle avoidance maneuver (meters)
SAFE_DISTANCE = 0.7            # Distance considered safe to resume forward motion (meters)
LINEAR_SPEED = 0.1             # Forward moving speed (m/s)
TURN_SPEED = 0.07              # Turning speed (rad/s)
ADJUST_TURN_SPEED = 0.035       # Mild turning speed (rad/s)

class ObstacleAvoidance(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance')
        
        # Dictionary to store minimum distances for each of the 4 front sectors
        self.regions = {}
        
        # State machine variables
        self.avoiding = False
        self.avoidance_type = None
        self.start_time = 0.0
        self.min_avoidance_time = 2.0
        
        # Publisher to control robot velocity
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Subscriber to receive scan data from the LIDAR driver
        self.sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.laser_callback,
            10
        )
        
        self.get_logger().info("Obstacle Avoidance Node Started")
        self.get_logger().info(f"Trigger Threshold: {OBSTACLE_DIST_THRESHOLD}m | Safe Threshold: {SAFE_DISTANCE}m")
        
    def laser_callback(self, msg):
        """
        Callback triggered whenever new LIDAR scans arrive.
        Filters data, calculates sector minimums, and calls the action selector.
        """
        total_points = len(msg.ranges)
        max_range = 10.0  # Fallback range when no obstacles are detected
        
        def safe_min(start, end):
            """
            Computes the minimum range value within a sector slice,
            filtering out zeros, inf, nan, and chassis self-reflections.
            """
            if start >= total_points:
                return max_range
            end = min(end, total_points)
            subset = msg.ranges[start:end]
            
            # Apply 0.38m chassis self-reflection filter
            valid_ranges = [r for r in subset if 0.38 < r < max_range]
            return min(valid_ranges) if valid_ranges else max_range
            
        # Remap scan indices by 180 degrees to align with physical robot front
        # Standard RPLidar indexes counter-clockwise.
        # Given the 180° rotation, the physical front corresponds to the middle of the range array.
        self.regions = {
            'fright':  safe_min(int(total_points * 0.25), int(total_points * 0.375)),  # 90-135° (Physical Robot Right)
            'front_R': safe_min(int(total_points * 0.375), int(total_points * 0.5)),   # 135-180° (Physical Robot Front-Right)
            'front_L': safe_min(int(total_points * 0.5), int(total_points * 0.625)),   # 180-225° (Physical Robot Front-Left)
            'fleft':   safe_min(int(total_points * 0.625), int(total_points * 0.75))   # 225-270° (Physical Robot Left)
        }
        
        # Log parsed regions to console for telemetry
        self.get_logger().info(
            f"Regions: fL={self.regions['front_L']:.2f}m, "
            f"fleft={self.regions['fleft']:.2f}m, "
            f"fright={self.regions['fright']:.2f}m, "
            f"fR={self.regions['front_R']:.2f}m",
            throttle_duration_sec=1.0  # Avoid terminal flooding
        )
        self.take_action()

    def is_path_clear(self):
        """
        Evaluates whether the path is sufficiently clear to exit the active avoidance maneuver.
        Enforces a wider/safer corridor (SAFE_DISTANCE = 0.7m) compared to the trigger threshold.
        """
        front_clear = (self.regions['front_L'] > SAFE_DISTANCE and 
                       self.regions['front_R'] > SAFE_DISTANCE)
        
        if self.avoidance_type in ['adjust_right', 'turn_right']:
            # Currently avoiding an obstacle on the left, make sure front and left are clear
            return front_clear and self.regions['fleft'] > SAFE_DISTANCE
        elif self.avoidance_type in ['adjust_left', 'turn_left']:
            # Currently avoiding an obstacle on the right, make sure front and right are clear
            return front_clear and self.regions['fright'] > SAFE_DISTANCE
        else:
            # Backing up or general recovery: ensure all front/side sectors are clear
            return (front_clear and 
                    self.regions['fleft'] > SAFE_DISTANCE and 
                    self.regions['fright'] > SAFE_DISTANCE)
    
    def take_action(self):
        """
        State Machine & Control Action Selector:
        Determines the appropriate Twist linear/angular speed based on sector values.
        Ensures persistent maneuvers are not interrupted prematurely.
        """
        msg = Twist()
        current_time = time.time()
        
        # Evaluate obstacle presence based on threshold
        front_obstacle = (self.regions['front_L'] < OBSTACLE_DIST_THRESHOLD or 
                          self.regions['front_R'] < OBSTACLE_DIST_THRESHOLD)
        left_obstacle = (self.regions['fleft'] < OBSTACLE_DIST_THRESHOLD)
        right_obstacle = (self.regions['fright'] < OBSTACLE_DIST_THRESHOLD)
        
        # CASE 1: Continue active avoidance maneuver if the minimum duration has not elapsed,
        # or if the path is still not fully clear.
        if self.avoiding:
            elapsed = current_time - self.start_time
            
            if elapsed < self.min_avoidance_time or not self.is_path_clear():
                if self.avoidance_type == 'back_up':
                    state = 'CONTINUING: Backing up'
                    msg.linear.x = -LINEAR_SPEED
                    msg.angular.z = 0.0
                elif self.avoidance_type == 'turn_right':
                    state = 'CONTINUING: Turning right'
                    msg.linear.x = 0.0
                    msg.angular.z = -TURN_SPEED
                elif self.avoidance_type == 'turn_left':
                    state = 'CONTINUING: Turning left'
                    msg.linear.x = 0.0
                    msg.angular.z = TURN_SPEED
                elif self.avoidance_type == 'adjust_right':
                    state = 'CONTINUING: Adjusting right'
                    msg.linear.x = LINEAR_SPEED
                    msg.angular.z = -ADJUST_TURN_SPEED
                elif self.avoidance_type == 'adjust_left':
                    state = 'CONTINUING: Adjusting left'
                    msg.linear.x = LINEAR_SPEED
                    msg.angular.z = ADJUST_TURN_SPEED
                
                self.get_logger().info(state, throttle_duration_sec=1.0)
                self.pub.publish(msg)
                return
            else:
                # Minimum duration elapsed and path is clear -> Exit avoidance state
                self.get_logger().info("AVOIDANCE COMPLETE - Path clear. Resuming normal navigation.")
                self.avoiding = False
                self.avoidance_type = None
        
        # CASE 2: No active avoidance, or previous maneuver completed. Check for new obstacles.
        if front_obstacle and left_obstacle and right_obstacle:
            state = 'NEW AVOIDANCE: Surrounded'
            msg.linear.x = -LINEAR_SPEED
            msg.angular.z = 0.0
            self.avoiding = True
            self.avoidance_type = 'back_up'
            self.start_time = current_time
            self.min_avoidance_time = 3.0
            
        elif front_obstacle and left_obstacle:
            state = 'NEW AVOIDANCE: Front and left blocked - turning right'
            msg.linear.x = 0.0
            msg.angular.z = -TURN_SPEED
            self.avoiding = True
            self.avoidance_type = 'turn_right'
            self.start_time = current_time
            self.min_avoidance_time = 2.0
            
        elif front_obstacle and right_obstacle:
            state = 'NEW AVOIDANCE: Front and right blocked - turning left'
            msg.linear.x = 0.0
            msg.angular.z = TURN_SPEED
            self.avoiding = True
            self.avoidance_type = 'turn_left'
            self.start_time = current_time
            self.min_avoidance_time = 2.0
            
        elif front_obstacle:
            # Front only blocked: steer towards whichever side has more clearance
            if self.regions['fleft'] > self.regions['fright']:
                state = 'NEW AVOIDANCE: Front blocked - turning left'
                msg.angular.z = TURN_SPEED
                self.avoidance_type = 'turn_left'
            else:
                state = 'NEW AVOIDANCE: Front blocked - turning right'
                msg.angular.z = -TURN_SPEED
                self.avoidance_type = 'turn_right'
            msg.linear.x = 0.0
            self.avoiding = True
            self.start_time = current_time
            self.min_avoidance_time = 2.0
            
        elif left_obstacle:
            state = 'NEW AVOIDANCE: Left side obstacle - adjusting right'
            msg.linear.x = LINEAR_SPEED
            msg.angular.z = -ADJUST_TURN_SPEED
            self.avoiding = True
            self.avoidance_type = 'adjust_right'
            self.start_time = current_time
            self.min_avoidance_time = 1.5
            
        elif right_obstacle:
            state = 'NEW AVOIDANCE: Right side obstacle - adjusting left'
            msg.linear.x = LINEAR_SPEED
            msg.angular.z = ADJUST_TURN_SPEED
            self.avoiding = True
            self.avoidance_type = 'adjust_left'
            self.start_time = current_time
            self.min_avoidance_time = 1.5
            
        else:
            # Normal State: No obstacles detected in any monitored sector
            state = 'Clear path - moving forward'
            msg.linear.x = LINEAR_SPEED
            msg.angular.z = 0.0
        
        self.get_logger().info(state, throttle_duration_sec=1.0)
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidance()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
