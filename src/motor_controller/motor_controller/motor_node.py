#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Int64, String
from rcl_interfaces.msg import SetParametersResult
import time
import sys
import os
import serial

# Add the current directory to sys.path so we can import the SDK
sys.path.insert(0, os.path.dirname(__file__))
from STservo_sdk import PortHandler, sts, COMM_SUCCESS, GroupSyncRead

class MotorDriverNode(Node):

    def __init__(self):
        super().__init__('motor_driver')
        
        # Publishers for ticks
        self.left_ticks_pub = self.create_publisher(Int64, 'left_ticks', 10)
        self.right_ticks_pub = self.create_publisher(Int64, 'right_ticks', 10)
        
        # Subscriber for cmd_vel
        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.listener_callback,
            10)
            
        # Subscriber for drive_mode
        self.mode_subscription = self.create_subscription(
            String,
            'drive_mode',
            self.drive_mode_callback,
            10)
        
        # Parameters configured for Arjuna robot defaults
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 1000000)
        self.declare_parameter('wheel_sep', 0.30)
        self.declare_parameter('wheel_base', 0.30)
        self.declare_parameter('motor_acc', 0)
        self.declare_parameter('drive_mode', 'differential') # 'differential' or 'mecanum'
        self.declare_parameter('speed_scaling', 10000)
        self.declare_parameter('tick_scaling', 2.5) # Division factor for ticks (2.5 matches Arjuna odom)
        self.declare_parameter('invert_y', False)
        
        self.port = self.get_parameter('port').get_parameter_value().string_value
        self.baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        self.wheel_sep = self.get_parameter('wheel_sep').get_parameter_value().double_value
        self.wheel_base = self.get_parameter('wheel_base').get_parameter_value().double_value
        self.motor_acc = self.get_parameter('motor_acc').get_parameter_value().integer_value
        self.drive_mode = self.get_parameter('drive_mode').get_parameter_value().string_value
        self.speed_scaling = self.get_parameter('speed_scaling').get_parameter_value().integer_value
        self.tick_scaling = self.get_parameter('tick_scaling').get_parameter_value().double_value
        self.invert_y = self.get_parameter('invert_y').get_parameter_value().bool_value
        
        # Command Heartbeat Tracking
        self.last_cmd_time = self.get_clock().now()
        self.cmd_warning_logged = False

        # Encoder Tracking Variables
        self.total_left_ticks = 0
        self.total_right_ticks = 0
        
        self.prev_left_ticks = 0
        self.prev_right_ticks = 0

        self.fl_speed_cmd = 0.0
        self.fr_speed_cmd = 0.0
        self.rl_speed_cmd = 0.0
        self.rr_speed_cmd = 0.0

        self.fl_speed = 0
        self.fr_speed = 0
        self.rl_speed = 0
        self.rr_speed = 0

        # Log parameters
        self.get_logger().info(f"Initializing motor_driver node in '{self.drive_mode}' mode.")
        self.get_logger().info(f"Port: {self.port}, Baudrate: {self.baudrate}")
        self.get_logger().info(f"Wheel Separation: {self.wheel_sep} m, Wheel Base: {self.wheel_base} m")
        self.get_logger().info(f"Speed Scaling: {self.speed_scaling}, Tick Scaling: {self.tick_scaling}, Invert Y: {self.invert_y}")

        self.portHandler = PortHandler(self.port)
        self.packetHandler = sts(self.portHandler)

        if self.portHandler.openPort():
            self.get_logger().info(f"Succeeded to open the port {self.port}")
        else:
            self.get_logger().error(f"Failed to open the port {self.port}")
            raise RuntimeError(f"Failed to open port {self.port}")

        if self.portHandler.setBaudRate(self.baudrate):
            self.get_logger().info(f"Succeeded to change the baudrate to {self.baudrate}")
        else:
            self.get_logger().error(f"Failed to change the baudrate to {self.baudrate}")
            raise RuntimeError(f"Failed to set baudrate {self.baudrate}")

        # Initialize Sync Communication objects
        # SyncRead for positions (Register 56, length 4 bytes: Position and Speed)
        # On Arjuna, we read ticks from ID 1 (Left / FL) and ID 2 (Right / FR)
        self.groupSyncRead = GroupSyncRead(self.packetHandler, 56, 4)
        self.groupSyncRead.addParam(1) # Left / FL (ID 1)
        self.groupSyncRead.addParam(2) # Right / FR (ID 2)
        
        # Initialize all 4 motors in Wheel Mode and Enable Torque
        for motor_id in [1, 2, 3, 4]:
            self.packetHandler.WheelMode(motor_id)
            # Register 40 is Torque Enable (1)
            self.packetHandler.write1ByteTxRx(motor_id, 40, 1)
        self.get_logger().info("Motors (1,2,3,4) initialized in Wheel Mode and Torque Enabled")

        # Timer for tick publishing and main loop (30Hz for low latency)
        self.timer = self.create_timer(0.033, self.main_loop)

        # Register parameter callback to support dynamic drive mode switching at runtime
        self.add_on_set_parameters_callback(self.parameters_callback)

    def listener_callback(self, msg):
        linear_x = msg.linear.x
        linear_y = msg.linear.y
        angular_z = msg.angular.z

        # Log received velocity (throttled to 1.0s to avoid flooding)
        self.get_logger().info(
            f"Subscribed cmd_vel: linear_x={linear_x:.3f}, linear_y={linear_y:.3f}, angular_z={angular_z:.3f}",
            throttle_duration_sec=1.0
        )

        # Update Heartbeat
        self.last_cmd_time = self.get_clock().now()
        if self.cmd_warning_logged:
            self.get_logger().info("Control commands resumed.")
            self.cmd_warning_logged = False

        if self.invert_y:
            linear_y = -linear_y

        if self.drive_mode == 'mecanum':
            # Mecanum drive kinematics with geometry-based angular velocity scaling
            # L = (wheel_base + wheel_sep) / 2.0
            l_sum = (self.wheel_base + self.wheel_sep) / 2.0
            self.fl_speed_cmd = linear_x - linear_y - (angular_z * l_sum)
            self.fr_speed_cmd = linear_x + linear_y + (angular_z * l_sum)
            self.rl_speed_cmd = linear_x + linear_y - (angular_z * l_sum)
            self.rr_speed_cmd = linear_x - linear_y + (angular_z * l_sum)
        else:
            # Differential drive kinematics - matches motorops (Arjuna_cmd_vel_sub.py)
            # Left_velocity = ((linear_vel * 2) - (angular_vel * wheel_sep)) / 2.0
            # Right_velocity = ((linear_vel * 2) + (angular_vel * wheel_sep)) / 2.0
            v_l = ((linear_x * 2.0) - (angular_z * self.wheel_sep)) / 2.0
            v_r = ((linear_x * 2.0) + (angular_z * self.wheel_sep)) / 2.0
            
            self.fl_speed_cmd = v_l
            self.rl_speed_cmd = v_l
            self.fr_speed_cmd = v_r
            self.rr_speed_cmd = v_r

        # Scale velocities to motor speed units
        self.fl_speed = int(self.fl_speed_cmd * self.speed_scaling)
        self.fr_speed = int(self.fr_speed_cmd * self.speed_scaling)
        self.rl_speed = int(self.rl_speed_cmd * self.speed_scaling)
        self.rr_speed = int(self.rr_speed_cmd * self.speed_scaling)

    def parameters_callback(self, params):
        for param in params:
            if param.name == 'drive_mode':
                value = param.value
                if value in ['differential', 'mecanum']:
                    self.drive_mode = value
                    self.get_logger().info(f"Drive mode dynamically changed to: {self.drive_mode}")
                else:
                    return SetParametersResult(successful=False, reason="Invalid drive_mode. Must be 'differential' or 'mecanum'")
        return SetParametersResult(successful=True)

    def drive_mode_callback(self, msg):
        mode = msg.data.lower()
        if mode in ['differential', 'mecanum']:
            if self.drive_mode != mode:
                self.drive_mode = mode
                self.get_logger().info(f"Drive mode dynamically changed via topic to: {self.drive_mode}")

    def present_pos(self, motor_id):
        """Read current motor position"""
        position, speed, result, error = self.packetHandler.ReadPosSpeed(motor_id)
        if result != COMM_SUCCESS:
            return None
        return position

    def update_ticks(self):
        """Optimized tick counting using SyncRead for Left (ID 1) and Right (ID 2) wheels"""
        comm_result = self.groupSyncRead.txRxPacket()
        if comm_result != COMM_SUCCESS:
            return

        # Left / FL (ID 1): Negated rotation direction
        pos_l = self.groupSyncRead.getData(1, 56, 2)
        if pos_l is not None:
            raw_ticks = pos_l
            if self.prev_left_ticks != 0 or self.total_left_ticks != 0:
                diff = raw_ticks - self.prev_left_ticks
                if diff > 2048: diff -= 4096
                elif diff < -2048: diff += 4096
                self.total_left_ticks -= diff
            self.prev_left_ticks = raw_ticks

        # Right / FR (ID 2): Positive rotation direction
        pos_r = self.groupSyncRead.getData(2, 56, 2)
        if pos_r is not None:
            raw_ticks = pos_r
            if self.prev_right_ticks != 0 or self.total_right_ticks != 0:
                diff = raw_ticks - self.prev_right_ticks
                if diff > 2048: diff -= 4096
                elif diff < -2048: diff += 4096
                self.total_right_ticks += diff
            self.prev_right_ticks = raw_ticks

        # Scale ticks if requested
        pub_l = int(self.total_left_ticks / self.tick_scaling)
        pub_r = int(self.total_right_ticks / self.tick_scaling)

        # Publish ticks
        self.left_ticks_pub.publish(Int64(data=pub_l))
        self.right_ticks_pub.publish(Int64(data=pub_r))

        # Log published ticks (throttled to 1.0s)
        self.get_logger().info(
            f"Published Ticks - Left: {pub_l} | Right: {pub_r}",
            throttle_duration_sec=1.0
        )

    def main_loop(self):
        try:
            self.update_ticks()
        except serial.SerialException as e:
            self.get_logger().warn(f"Serial read glitch (will retry): {e}")
            return  # Skip this cycle, don't crash
        except Exception as e:
            self.get_logger().warn(f"Tick update error: {e}")
            return
            
        # Check command heartbeat: if > 2.0s without cmd_vel, stop motors for safety
        now = self.get_clock().now()
        time_diff = (now - self.last_cmd_time).nanoseconds / 1e9
        if time_diff > 2.0 and not self.cmd_warning_logged:
            if self.last_cmd_time.nanoseconds > 0:
                self.get_logger().warn(f"Control heartbeat idle for {time_diff:.1f}s. Stopping motors...")
            self.cmd_warning_logged = True
            self.fl_speed = 0
            self.fr_speed = 0
            self.rl_speed = 0
            self.rr_speed = 0

        # Write speeds to motors using SyncWrite
        try:
            # Left (IDs 1, 4) - Negated due to mirroring adjustment on Arjuna
            fl_val = self.packetHandler.sts_toscs(-self.fl_speed, 15)
            rl_val = self.packetHandler.sts_toscs(-self.rl_speed, 15)
            fl_packet = [self.motor_acc, 0, 0, 0, 0, self.packetHandler.sts_lobyte(fl_val), self.packetHandler.sts_hibyte(fl_val)]
            rl_packet = [self.motor_acc, 0, 0, 0, 0, self.packetHandler.sts_lobyte(rl_val), self.packetHandler.sts_hibyte(rl_val)]
            
            # Right (IDs 2, 3) - Positive due to mirroring adjustment on Arjuna
            fr_val = self.packetHandler.sts_toscs(self.fr_speed, 15)
            rr_val = self.packetHandler.sts_toscs(self.rr_speed, 15)
            fr_packet = [self.motor_acc, 0, 0, 0, 0, self.packetHandler.sts_lobyte(fr_val), self.packetHandler.sts_hibyte(fr_val)]
            rr_packet = [self.motor_acc, 0, 0, 0, 0, self.packetHandler.sts_lobyte(rr_val), self.packetHandler.sts_hibyte(rr_val)]
            
            # Add to SyncWrite
            self.packetHandler.groupSyncWrite.clearParam()
            self.packetHandler.groupSyncWrite.addParam(1, fl_packet) # FL (ID 1)
            self.packetHandler.groupSyncWrite.addParam(2, fr_packet) # FR (ID 2)
            self.packetHandler.groupSyncWrite.addParam(4, rl_packet) # RL (ID 4)
            self.packetHandler.groupSyncWrite.addParam(3, rr_packet) # RR (ID 3)
            
            # Transmit (one packet for all)
            self.packetHandler.groupSyncWrite.txPacket()
            
        except Exception as e:
            self.get_logger().error(f"Motor SyncWrite Error: {e}")

    def stop_motors(self):
        """Force motors to zero speed using Broadcast ID for instant stop"""
        self.get_logger().info("Safety Shutdown: Broadcasting STOP to all motors.")
        try:
            # ID 254 is Broadcast ID for STServo
            self.packetHandler.WriteSpec(254, 0, self.motor_acc)
            time.sleep(0.05)
        except Exception as e:
            self.get_logger().error(f"Failed to broadcast stop: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = MotorDriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_motors()
        if hasattr(node, 'portHandler') and node.portHandler:
            node.portHandler.closePort()
        node.destroy_node()
        try:
            rclpy.shutdown()
        except:
            pass

if __name__ == '__main__':
    main()
