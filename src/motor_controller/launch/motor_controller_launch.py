#!/usr/bin/env python3

"""
Arjuna Motor Controller Launch File

Usage Examples:
1. Run in default mode (differential drive, /dev/ttyACM0, 1000000 baud):
   ros2 launch motor_controller motor_controller_launch.py

2. Run in mecanum drive mode:
   ros2 launch motor_controller motor_controller_launch.py drive_mode:=mecanum

3. Run on a different serial port (e.g. /dev/ttyUSB0):
   ros2 launch motor_controller motor_controller_launch.py port:=/dev/ttyUSB0

4. Run at a different baud rate (e.g. 115200):
   ros2 launch motor_controller motor_controller_launch.py baudrate:=115200

5. Full combination example:
   ros2 launch motor_controller motor_controller_launch.py drive_mode:=mecanum port:=/dev/ttyACM0 baudrate:=1000000
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Declare launch arguments
    port_arg = DeclareLaunchArgument(
        'port',
        default_value='/dev/ttyACM0',
        description='Serial port for motor communication'
    )
    
    baudrate_arg = DeclareLaunchArgument(
        'baudrate',
        default_value='1000000',
        description='Baud rate for motor communication'
    )
    
    wheel_sep_arg = DeclareLaunchArgument(
        'wheel_sep',
        default_value='0.30',
        description='Wheel separation distance (m)'
    )
    
    wheel_base_arg = DeclareLaunchArgument(
        'wheel_base',
        default_value='0.30',
        description='Wheel base axle distance (m)'
    )
    
    motor_acc_arg = DeclareLaunchArgument(
        'motor_acc',
        default_value='0',
        description='Motor acceleration'
    )
    
    drive_mode_arg = DeclareLaunchArgument(
        'drive_mode',
        default_value='differential',
        description='Drive mode (differential or mecanum)'
    )
    
    speed_scaling_arg = DeclareLaunchArgument(
        'speed_scaling',
        default_value='10000',
        description='Scaling factor from m/s to motor unit commands'
    )
    
    tick_scaling_arg = DeclareLaunchArgument(
        'tick_scaling',
        default_value='2.5',
        description='Division factor for raw ticks'
    )
    
    invert_y_arg = DeclareLaunchArgument(
        'invert_y',
        default_value='false',
        description='Invert Y velocity command'
    )

    # Motor driver node
    motor_node = Node(
        package='motor_controller',
        executable='motor_node',
        name='motor_driver',
        output='screen',
        parameters=[{
            'port': LaunchConfiguration('port'),
            'baudrate': LaunchConfiguration('baudrate'),
            'wheel_sep': LaunchConfiguration('wheel_sep'),
            'wheel_base': LaunchConfiguration('wheel_base'),
            'motor_acc': LaunchConfiguration('motor_acc'),
            'drive_mode': LaunchConfiguration('drive_mode'),
            'speed_scaling': LaunchConfiguration('speed_scaling'),
            'tick_scaling': LaunchConfiguration('tick_scaling'),
            'invert_y': LaunchConfiguration('invert_y'),
        }]
    )

    return LaunchDescription([
        port_arg,
        baudrate_arg,
        wheel_sep_arg,
        wheel_base_arg,
        motor_acc_arg,
        drive_mode_arg,
        speed_scaling_arg,
        tick_scaling_arg,
        invert_y_arg,
        motor_node
    ])
