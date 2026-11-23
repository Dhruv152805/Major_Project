#!/usr/bin/env python3

"""
Arjuna Odometry and EKF Fusion Launch File

This launch file brings up:
1. The optimized C++ wheel odometry publisher (arjuna_ekf_odom_pub)
2. The RViz interface click converter (arjuna_rviz_data_pub)
3. Optionally, the robot_localization EKF node fusing odometry + IMU (ekf_node)

Usage Examples:
1. Launch everything (Odom + RViz Helper + EKF Fusion):
   ros2 launch arjuna_odometry arjuna_odometry_launch.py

2. Launch wheel odometry only (without EKF, wheel odom will publish TF odom->base_footprint):
   ros2 launch arjuna_odometry arjuna_odometry_launch.py use_ekf:=false
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    pkg_share = FindPackageShare('arjuna_odometry')

    # Paths to config files
    default_odom_config = PathJoinSubstitution([pkg_share, 'config', 'arjuna_odometry_params.yaml'])
    default_ekf_config = PathJoinSubstitution([pkg_share, 'config', 'ekf.yaml'])

    # Declare launch arguments
    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value=default_odom_config,
        description='Path to arjuna_odometry config file'
    )

    ekf_config_file_arg = DeclareLaunchArgument(
        'ekf_config_file',
        default_value=default_ekf_config,
        description='Path to EKF configuration file'
    )

    use_ekf_arg = DeclareLaunchArgument(
        'use_ekf',
        default_value='true',
        description='Whether to launch EKF fusion node (robot_localization)'
    )

    # Dynamic TF configuration:
    # If EKF is used, the wheel odometry publisher should NOT publish TF (publish_tf:=false).
    # If EKF is disabled, the wheel odometry publisher MUST publish TF (publish_tf:=true).
    publish_tf_expr = PythonExpression([
        "'false' if '", LaunchConfiguration('use_ekf'), "' == 'true' else 'true'"
    ])

    # 1. C++ Wheel Odometry Publisher Node
    arjuna_odom_node = Node(
        package='arjuna_odometry',
        executable='arjuna_ekf_odom_pub',
        name='arjuna_ekf_odom_pub',
        output='screen',
        parameters=[
            LaunchConfiguration('config_file'),
            {'publish_tf': publish_tf_expr}
        ]
    )

    # 2. C++ RViz Data Click Converter Node
    arjuna_rviz_node = Node(
        package='arjuna_odometry',
        executable='arjuna_rviz_data_pub',
        name='arjuna_rviz_data_pub',
        output='screen'
    )

    # 3. EKF Fusion Node (robot_localization)
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[LaunchConfiguration('ekf_config_file')],
        condition=IfCondition(LaunchConfiguration('use_ekf'))
    )

    return LaunchDescription([
        config_file_arg,
        ekf_config_file_arg,
        use_ekf_arg,
        arjuna_odom_node,
        arjuna_rviz_node,
        ekf_node
    ])
