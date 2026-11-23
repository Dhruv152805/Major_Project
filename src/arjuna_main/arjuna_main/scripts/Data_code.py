#!/usr/bin/env python3

"""
ROS 2 Node: I2C Ultrasonic Sensor Publisher and MOSFET Light Controller
Supports direct ON, OFF, Toggle, and Auto-Blink controls via Keyboard, Topic, and ROS 2 Service.

Features:
1. Reads 6 bytes over I2C (Bus 1, Addr 0x08) from Arduino:
   - Byte 0-1: Ultrasonic 1 distance (cm)
   - Byte 2-3: Ultrasonic 2 distance (cm)
   - Byte 4-5: Analog pin A1 raw value -> converted to Pin Voltage (0 - 5.0 V)
2. Controls MOSFET Light on Arduino:
   - Key '1', 'o', 'O': Turn Light ON
   - Key '0', 'f', 'F': Turn Light OFF
   - Key 't', 'T': Toggle Light ON/OFF
   - Key 'b', 'B': Toggle Auto-Blink Mode (500ms cycle)
   - Key 'q', 'Q': Safe Quit
3. ROS 2 Services & Topics:
   - Service `/set_light` (`std_srvs/srv/SetBool`)
   - Topic `/toggle_light` (`std_msgs/msg/Bool`)
   - Topic `/light/set_state` (`std_msgs/msg/Bool`)
   - Topic `/light_status` (`std_msgs/msg/Bool`)
"""

import sys
import select
import termios
import tty
import threading
import time
import smbus2

import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from std_msgs.msg import Float32, Bool
from std_srvs.srv import SetBool
from sensor_msgs.msg import Range

class I2CSensorLightNode(Node):
    def __init__(self):
        super().__init__('data_code_node')

        # Parameters
        self.declare_parameter('i2c_bus', 1)
        self.declare_parameter('i2c_addr', 0x08)
        self.declare_parameter('timer_period', 0.1)  # 10 Hz
        self.declare_parameter('frame_id_1', 'ultrasonic_1_link')
        self.declare_parameter('frame_id_2', 'ultrasonic_2_link')

        self.i2c_bus_num = self.get_parameter('i2c_bus').value
        self.i2c_addr = self.get_parameter('i2c_addr').value
        timer_period = self.get_parameter('timer_period').value
        self.frame_id_1 = self.get_parameter('frame_id_1').value
        self.frame_id_2 = self.get_parameter('frame_id_2').value

        # Light / MOSFET State (0 = OFF, 1 = ON)
        self.light_state = 0
        self.blink_mode = False
        self.last_blink_time = time.time()
        self.bus = None
        self.i2c_lock = threading.Lock()
        self.running = True

        # Initialize I2C Bus
        self.init_i2c()

        # Publishers
        self.pub_us1_range = self.create_publisher(Range, '/ultrasonic/sensor1/range', 10)
        self.pub_us2_range = self.create_publisher(Range, '/ultrasonic/sensor2/range', 10)
        self.pub_us1_cm = self.create_publisher(Float32, '/ultrasonic/sensor1/distance_cm', 10)
        self.pub_us2_cm = self.create_publisher(Float32, '/ultrasonic/sensor2/distance_cm', 10)
        self.pub_voltage = self.create_publisher(Float32, '/analog/voltage', 10)
        self.pub_light_status = self.create_publisher(Bool, '/light_status', 10)

        # Subscriber for ROS-based light commands
        self.sub_light = self.create_subscription(
            Bool,
            '/toggle_light',
            self.light_command_callback,
            10
        )
        self.sub_set_state = self.create_subscription(
            Bool,
            '/light/set_state',
            self.light_command_callback,
            10
        )

        # Service for ROS-based set light ON/OFF
        self.srv_set_light = self.create_service(
            SetBool,
            '/set_light',
            self.set_light_service_callback
        )

        # Timer for reading I2C sensor data
        self.timer = self.create_timer(timer_period, self.read_and_publish_sensors)

        # Print banner & start keyboard listener
        self.print_controls_banner()
        if sys.stdin.isatty():
            self.keyboard_thread = threading.Thread(target=self.keyboard_listener_loop, daemon=True)
            self.keyboard_thread.start()

    def print_controls_banner(self):
        """Displays interactive keyboard controls guide."""
        print("=" * 60)
        print("  Arjuna I2C Sensor & MOSFET Light Controller")
        print(f"  I2C Bus: {self.i2c_bus_num} | Device Address: 0x{self.i2c_addr:02X}")
        print("=" * 60)
        print("  KEYBOARD CONTROLS:")
        print("    [1] or [o] / [O] -> Turn Light ON")
        print("    [0] or [f] / [F] -> Turn Light OFF")
        print("    [t] or [T]       -> Toggle Light ON / OFF")
        print("    [b] or [B]       -> Toggle Auto-Blink (0.5s cycle)")
        print("    [q] or [Q]       -> Safe Quit")
        print("-" * 60)
        print("  ROS 2 INTERFACES:")
        print("    Topic:   /light/set_state  (std_msgs/msg/Bool: true=ON, false=OFF)")
        print("    Service: /set_light        (std_srvs/srv/SetBool)")
        print("    Status:  /light_status     (std_msgs/msg/Bool)")
        print("=" * 60)

    def init_i2c(self):
        """Initializes the I2C bus connection."""
        try:
            self.bus = smbus2.SMBus(self.i2c_bus_num)
            self.get_logger().info(f"Successfully opened I2C Bus {self.i2c_bus_num}")
        except PermissionError:
            self.get_logger().error(f"Permission denied accessing I2C Bus {self.i2c_bus_num}. Run with sudo or add user to 'i2c' group.")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize I2C Bus {self.i2c_bus_num}: {e}")

    def control_mosfet(self, state: int):
        """Sends a 1 (ON) or 0 (OFF) to the Arduino to control the MOSFET on Pin 3."""
        self.light_state = 1 if state else 0
        if self.bus is None:
            self.get_logger().warn(f"Cannot set light state: I2C bus not open.", throttle_duration_sec=2.0)
            return False

        with self.i2c_lock:
            try:
                self.bus.write_byte(self.i2c_addr, self.light_state)
                status_str = "ON" if self.light_state == 1 else "OFF"
                self.get_logger().info(f"MOSFET Light -> {status_str}")
                return True
            except Exception as e:
                self.get_logger().error(f"Error writing to I2C: {e}", throttle_duration_sec=2.0)
                return False

    def toggle_mosfet(self):
        """Toggles the current MOSFET state."""
        self.blink_mode = False
        new_state = 0 if self.light_state == 1 else 1
        self.control_mosfet(new_state)

    def set_light_on(self):
        """Explicitly turns light ON."""
        self.blink_mode = False
        self.control_mosfet(1)

    def set_light_off(self):
        """Explicitly turns light OFF."""
        self.blink_mode = False
        self.control_mosfet(0)

    def toggle_blink_mode(self):
        """Toggles auto-blink mode."""
        self.blink_mode = not self.blink_mode
        mode_str = "ENABLED (500ms cycle)" if self.blink_mode else "DISABLED"
        self.get_logger().info(f"Auto-Blink Mode -> {mode_str}")

    def light_command_callback(self, msg: Bool):
        """Callback for /toggle_light or /light/set_state topic command."""
        self.blink_mode = False
        self.control_mosfet(1 if msg.data else 0)

    def set_light_service_callback(self, request, response):
        """Service callback for /set_light (std_srvs/srv/SetBool)."""
        self.blink_mode = False
        success = self.control_mosfet(1 if request.data else 0)
        response.success = success
        response.message = f"Light turned {'ON' if request.data else 'OFF'}"
        return response

    def read_and_publish_sensors(self):
        """Reads 6-byte data block from Arduino over I2C and publishes to ROS 2 topics."""
        if not self.running:
            return

        # Handle Auto-Blink cycle
        if self.blink_mode:
            now_sec = time.time()
            if now_sec - self.last_blink_time >= 0.5:
                self.last_blink_time = now_sec
                new_state = 0 if self.light_state == 1 else 1
                self.control_mosfet(new_state)

        if self.bus is None:
            return

        try:
            with self.i2c_lock:
                # Read 6 bytes starting from offset 0
                data = self.bus.read_i2c_block_data(self.i2c_addr, 0, 6)

            # Unpack bytes
            dist1_cm = float((data[0] << 8) | data[1])
            dist2_cm = float((data[2] << 8) | data[3])
            raw_analog = (data[4] << 8) | data[5]

            # Calculate voltage (5V ref, 10-bit ADC 0-1023)
            arduino_vref = 5.0
            pin_voltage = float((raw_analog / 1023.0) * arduino_vref)

            now = self.get_clock().now().to_msg()

            # Publish Ultrasonic 1
            msg_us1_range = Range()
            msg_us1_range.header.stamp = now
            msg_us1_range.header.frame_id = self.frame_id_1
            msg_us1_range.radiation_type = getattr(Range, 'ULTRASOUND', 1)
            msg_us1_range.field_of_view = 0.26  # ~15 degrees
            msg_us1_range.min_range = 0.02      # 2 cm
            msg_us1_range.max_range = 4.00      # 400 cm
            msg_us1_range.range = dist1_cm / 100.0
            self.pub_us1_range.publish(msg_us1_range)

            msg_us1_cm = Float32()
            msg_us1_cm.data = dist1_cm
            self.pub_us1_cm.publish(msg_us1_cm)

            # Publish Ultrasonic 2
            msg_us2_range = Range()
            msg_us2_range.header.stamp = now
            msg_us2_range.header.frame_id = self.frame_id_2
            msg_us2_range.radiation_type = getattr(Range, 'ULTRASOUND', 1)
            msg_us2_range.field_of_view = 0.26
            msg_us2_range.min_range = 0.02
            msg_us2_range.max_range = 4.00
            msg_us2_range.range = dist2_cm / 100.0
            self.pub_us2_range.publish(msg_us2_range)

            msg_us2_cm = Float32()
            msg_us2_cm.data = dist2_cm
            self.pub_us2_cm.publish(msg_us2_cm)

            # Publish Voltage
            msg_voltage = Float32()
            msg_voltage.data = pin_voltage
            self.pub_voltage.publish(msg_voltage)

            # Publish Light Status
            msg_light = Bool()
            msg_light.data = bool(self.light_state == 1)
            self.pub_light_status.publish(msg_light)

        except Exception as e:
            self.get_logger().warn(f"Error reading I2C sensor data: {e}", throttle_duration_sec=2.0)

    def keyboard_listener_loop(self):
        """Thread loop to capture keypresses in terminal without requiring Enter."""
        settings = termios.tcgetattr(sys.stdin)
        try:
            while self.running and rclpy.ok():
                tty.setraw(sys.stdin.fileno())
                rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                if rlist:
                    key = sys.stdin.read(1)
                    if key in ['1', 'o', 'O', 'h', 'H']:
                        self.set_light_on()
                    elif key in ['0', 'f', 'F', 'l', 'L']:
                        self.set_light_off()
                    elif key in ['t', 'T']:
                        self.toggle_mosfet()
                    elif key in ['b', 'B']:
                        self.toggle_blink_mode()
                    elif key in ['q', 'Q', '\x03']:  # 'q' or Ctrl+C
                        self.get_logger().info("Quit key pressed. Exiting safely...")
                        self.running = False
                        break
        except Exception as e:
            self.get_logger().debug(f"Keyboard listener exception: {e}")
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
            if rclpy.ok():
                rclpy.shutdown()

    def destroy_node(self):
        """Clean node shutdown."""
        self.running = False
        if self.bus is not None:
            # Turn OFF MOSFET safely before closing
            try:
                with self.i2c_lock:
                    self.bus.write_byte(self.i2c_addr, 0)
                    self.bus.close()
            except Exception:
                pass
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = I2CSensorLightNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
