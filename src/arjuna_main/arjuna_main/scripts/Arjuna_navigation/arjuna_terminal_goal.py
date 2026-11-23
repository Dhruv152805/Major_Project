#!/usr/bin/env python3
"""
Arjuna Interactive Autonomous Navigation Terminal Node
=====================================================
This node provides an interactive terminal CLI to command the Arjuna robot to goals 
via the ROS 2 Navigation2 (Nav2) stack. It communicates directly with the Nav2 Action Server.

-----------------------------------------------------------------------------------------
ARCHITECTURE & CONTROL FLOW:
1. Nav2 Action Client Integration:
   - Uses an ActionClient for 'NavigateToPose' (nav2_msgs/action/NavigateToPose) to send goals.
   - Leverages action feedback callbacks to monitor distance remaining and recovery counts in real-time.
2. Dual Navigation Modes:
   - Relative Mode (Frame: 'base_footprint'):
     * User inputs distances (X, Y) relative to the robot's current local position and heading.
     * The target yaw is computed as math.atan2(y, x).
   - Absolute Mode (Frame: 'map'):
     * User inputs fixed absolute coordinates on the map.
     * The node uses the TF tree ('base_footprint' -> 'map') to find the robot's current coordinates.
     * The target yaw is calculated pointing from the current position to the goal coordinate.
3. Threaded Executor:
   - Runs a background SingleThreadedExecutor spin loop to process ROS 2 callbacks (e.g., EKF odometry,
     TF transform updates, Action client feedback) without blocking the interactive user input loop on stdin.
4. Odometry & Localization Feedback:
   - Subscribes to '/robot_pose_ekf/odom_combined' to verify odometry stream availability before allowing goals.
   - Monitors GoalStatus for SUCCEEDED, ABORTED, or CANCELED states and provides detailed user messages.

Company: NEWRRO TECH LLP
Website: www.newrro.in
-----------------------------------------------------------------------------------------
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.signals import SignalHandlerOptions
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import Point
from nav_msgs.msg import Odometry
from tf2_ros import Buffer, TransformListener, TransformException
from action_msgs.msg import GoalStatus
import math
import time
import threading

class ArjunaTerminalGoalNode(Node):
    def __init__(self):
        super().__init__('arjuna_terminal_goal')
        
        # Current robot state tracking
        self.current_position = Point()
        self.current_yaw = 0.0
        self.odom_received = False
        
        # Parameter for multi-robot namespace
        self.declare_parameter('robot_id', 'arjuna_1')
        self.robot_id = self.get_parameter('robot_id').value
        self.base_frame = f'{self.robot_id}/base_footprint'
        
        # Subscribe to odometry with multi-topic fallback
        self.odom_subs = []
        for o_top in [
            f'/{self.robot_id}/robot_pose_ekf/odom_combined',
            f'/{self.robot_id}/odom',
            f'/{self.robot_id}/wheel/odom',
            '/odom',
            '/robot_pose_ekf/odom_combined',
        ]:
            sub = self.create_subscription(Odometry, o_top, self.odom_callback, 10)
            self.odom_subs.append(sub)

        # Nav2 Action Clients: primary (namespaced) and fallback (unnamespaced)
        action_topic = f'/{self.robot_id}/navigate_to_pose'
        self.action_client = ActionClient(self, NavigateToPose, action_topic)
        self.alt_client = ActionClient(self, NavigateToPose, '/navigate_to_pose')
        
        # TF Buffer and Listener to dynamically query base_footprint relation to the map
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Action goal handles and tracking flags
        self.goal_handle = None
        self.goal_done = False
        self.goal_status = None
        self.last_feedback_time = 0.0
        
        self.get_logger().info(f"Arjuna Terminal Goal Node Started for [{self.robot_id}] (action: {action_topic})")

    def odom_callback(self, msg):
        """
        Receives fused odometry data and extracts the 2D position and heading (yaw).
        Converts the orientation quaternion to yaw using standard Euler formula.
        """
        self.current_position.x = msg.pose.pose.position.x
        self.current_position.y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        
        # Quaternion to Yaw conversion
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)
        self.odom_received = True

    def get_current_pose_in_map(self):
        """
        Queries the TF tree to retrieve the robot's current coordinates inside the 'map' frame.
        Required for absolute navigation goal calculations and user feedback.
        """
        for target_frame in [self.base_frame, 'base_footprint']:
            try:
                now = rclpy.time.Time()
                trans = self.tf_buffer.lookup_transform(
                    'map', 
                    target_frame, 
                    now, 
                    timeout=rclpy.duration.Duration(seconds=0.5)
                )
                pos = trans.transform.translation
                rot = trans.transform.rotation
                
                # Quaternion to Yaw conversion
                siny_cosp = 2.0 * (rot.w * rot.z + rot.x * rot.y)
                cosy_cosp = 1.0 - 2.0 * (rot.y * rot.y + rot.z * rot.z)
                yaw = math.atan2(siny_cosp, cosy_cosp)
                return pos.x, pos.y, yaw
            except TransformException:
                continue
        return None

    def send_goal(self, x, y, frame_id='map'):
        """
        Assembles a NavigateToPose Goal message and transmits it to the Nav2 action server.
        """
        self.goal_done = False
        self.goal_status = None
        self.last_feedback_time = 0.0
        
        self.get_logger().info(f"Checking Nav2 Action Server for '{self.robot_id}'...")
        active_client = self.action_client
        if not active_client.wait_for_server(timeout_sec=3.0):
            if self.alt_client.wait_for_server(timeout_sec=2.0):
                self.get_logger().info("Using fallback unnamespaced '/navigate_to_pose' Action Server.")
                active_client = self.alt_client
            else:
                self.get_logger().error(f"Nav2 Action Server not available! Make sure bringup or mapping is launched.")
                return False
            
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = frame_id
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        
        # Calculate target yaw pointing directly towards the goal from the start location
        if frame_id in ['base_footprint', self.base_frame]:
            # In local frame, start is (0,0)
            yaw = math.atan2(y, x)
            goal_msg.pose.header.frame_id = self.base_frame
        else:
            # In global map frame, calculate displacement vector
            map_pose = self.get_current_pose_in_map()
            if map_pose is not None:
                curr_x, curr_y, _ = map_pose
                dx = x - curr_x
                dy = y - curr_y
                yaw = math.atan2(dy, dx)
            else:
                # Fallback to raw odometry coordinates if TF fails
                dx = x - self.current_position.x
                dy = y - self.current_position.y
                yaw = math.atan2(dy, dx)
        
        # Convert Euler yaw to quaternion representation
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2.0)
        
        self.get_logger().info(f"Sending goal ({x:.2f}, {y:.2f}) in '{frame_id}' frame to Nav2...")
        
        self.send_goal_future = active_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        self.send_goal_future.add_done_callback(self.goal_response_callback)
        return True

    def goal_response_callback(self, future):
        """
        Receives server acknowledgement for the sent goal.
        Registers the result callback if the goal was successfully accepted.
        """
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Goal rejected by Nav2 server!")
            self.goal_done = True
            return
            
        self.get_logger().info("Goal accepted by Nav2. Navigating...")
        self.goal_handle = goal_handle
        self.get_result_future = goal_handle.get_result_async()
        self.get_result_future.add_done_callback(self.get_result_callback)

    def feedback_callback(self, feedback_msg):
        """
        Monitors navigation progress (throttled to 1.5s intervals).
        Prints remaining distance and active recovery behavior counts.
        """
        feedback = feedback_msg.feedback
        current_time = time.time()
        if current_time - self.last_feedback_time >= 1.5:
            rec_str = f" | Recoveries: {feedback.number_of_recoveries}" if feedback.number_of_recoveries > 0 else ""
            self.get_logger().info(
                f"Progress: Remaining Distance = {feedback.distance_remaining:.2f}m{rec_str}"
            )
            self.last_feedback_time = current_time

    def get_result_callback(self, future):
        """Called when navigation terminates (goal reached, aborted, or canceled)."""
        result = future.result()
        self.goal_status = result.status
        self.goal_done = True
        self.goal_handle = None

    def cancel_goal(self):
        """Sends a cancellation request to the Action Server if navigation is interrupted."""
        if self.goal_handle is not None:
            self.get_logger().info("Canceling current goal...")
            self.goal_handle.cancel_goal_async()

def main(args=None):
    # Initialize rclpy without default keyboard interrupt signal handler to prevent conflict with CLI
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    client = ArjunaTerminalGoalNode()
    
    # Spin ROS node in a separate thread so input() doesn't block processing of callbacks
    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(client)
    
    def spin_executor():
        try:
            executor.spin()
        except Exception:
            pass
            
    executor_thread = threading.Thread(target=spin_executor, daemon=True)
    executor_thread.start()
    
    # Wait for initial odometry with 3.0s timeout instead of blocking forever
    client.get_logger().info("Checking for live odometry...")
    t_wait_start = time.time()
    while rclpy.ok() and not client.odom_received and (time.time() - t_wait_start < 3.0):
        time.sleep(0.1)
    if client.odom_received:
        client.get_logger().info("✓ Live odometry verified.")
    else:
        client.get_logger().warn("Odometry not yet received (will update in background when streaming).")
    
    # GoalStatus mapping
    status_map = {
        GoalStatus.STATUS_UNKNOWN: "UNKNOWN",
        GoalStatus.STATUS_ACCEPTED: "ACCEPTED",
        GoalStatus.STATUS_EXECUTING: "EXECUTING",
        GoalStatus.STATUS_CANCELING: "CANCELING",
        GoalStatus.STATUS_SUCCEEDED: "SUCCEEDED",
        GoalStatus.STATUS_CANCELED: "CANCELED",
        GoalStatus.STATUS_ABORTED: "ABORTED"
    }
    
    try:
        # CLI Menu Loop
        while rclpy.ok():
            try:
                print("\n===========================================")
                print(" Arjuna Nav2 Interactive Terminal Menu     ")
                print("===========================================")
                print("1. Relative Coordinates (moves relative to Robot pose)")
                print("2. Absolute Map Coordinates (fixed point on Map)")
                print("3. Exit Program")
                print("===========================================")
                choice = input("Enter choice (1, 2, or 3, default 1): ").strip()
                
                if choice == '3':
                    break
                
                if choice == '2':
                    frame_id = 'map'
                    map_pose = client.get_current_pose_in_map()
                    if map_pose is not None:
                        x_curr, y_curr, yaw_curr = map_pose
                        print(f"\n[MAP INFO] Robot Current Position: X = {x_curr:.2f}, Y = {y_curr:.2f}, Yaw = {yaw_curr:.2f}")
                    else:
                        print("\n[WARN] Robot current map pose is not available yet. Make sure AMCL is localized.")
                    
                    x = float(input("Enter absolute X goal coordinate: "))
                    y = float(input("Enter absolute Y goal coordinate: "))
                else:
                    frame_id = 'base_footprint'
                    x = float(input("Enter relative X (forward/backward distance in meters): "))
                    y = float(input("Enter relative Y (left/right distance in meters): "))
                    
            except ValueError:
                print("Invalid input. Please enter numeric values.")
                continue
            except (KeyboardInterrupt, EOFError):
                break
                
            # Send goal to the Action Server
            if not client.send_goal(x, y, frame_id):
                continue
                
            # Block this thread until action completes, supporting keyboard cancel (Ctrl-C)
            try:
                while rclpy.ok() and not client.goal_done:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                client.cancel_goal()
                while not client.goal_done:
                    time.sleep(0.1)
                print("Navigation canceled.")
                continue
                
            status_str = status_map.get(client.goal_status, f"CODE {client.goal_status}")
            
            if client.goal_status == GoalStatus.STATUS_SUCCEEDED:
                print("\n===========================================")
                print("✓ GOAL REACHED!")
                print("===========================================")
            elif client.goal_status == GoalStatus.STATUS_ABORTED:
                print("\n===========================================")
                print(f"✗ GOAL FAILED: The planner or controller aborted. (Status: {status_str})")
                print("Note: If using absolute map coords, the point might be inside a wall/obstacle.")
                print("===========================================")
            else:
                print(f"Navigation finished with status: {status_str}")
                
            try:
                cont = input("\nNavigate to another point? (y/n): ")
            except (KeyboardInterrupt, EOFError):
                break
            if cont.lower() != 'y':
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            client.cancel_goal()
            executor.shutdown()
            client.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()
