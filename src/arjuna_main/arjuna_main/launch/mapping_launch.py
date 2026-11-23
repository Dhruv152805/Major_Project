#!/usr/bin/env python3
"""
Arjuna Main SLAM Mapping Launch File
=====================================
Brings up:
1. Static TF transforms (base_footprint -> base_link -> laser, imu)
2. Motor driver node (motor_controller/motor_node)
3. Wheel odometry node (arjuna_odometry/arjuna_ekf_odom_pub remapped to /wheel/odom)
4. IMU driver node (imu_bno055/bno055_i2c_node)
5. LIDAR driver node (sllidar_ros2/sllidar_node)
6. Sensor Fusion node (robot_localization/ekf_node publishing odom -> base_footprint TF, remapped to /odom)
7. SLAM node (slam_toolbox/async_slam_toolbox_node publishing map -> odom TF and /map)
8. Autonomous Nav2 Navigation Stack (controller, planner, behaviors, bt_navigator, lifecycle)
   allows the robot to autonomously navigate to goals even while mapping in real time!
9. RViz Goal Bridge (bridges RViz 2D Goal Pose clicks directly to Nav2 action goals)
10. RViz visualization with default slam.rviz config
11. Auto-save map on RViz exit
"""

import os
import copy
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, TimerAction
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.conditions import IfCondition


def get_default_imu_device():
    import fcntl
    def probe_bno055(dev_path):
        if not os.path.exists(dev_path):
            return False
        try:
            fd = os.open(dev_path, os.O_RDWR)
            fcntl.ioctl(fd, 0x0703, 0x28)
            os.write(fd, b'\x00')
            chip_id = os.read(fd, 1)
            os.close(fd)
            return chip_id == b'\xa0'
        except Exception:
            return False

    for bus in ['/dev/i2c-7', '/dev/i2c-1', '/dev/i2c-0']:
        if probe_bno055(bus):
            return bus
    return '/dev/i2c-1'


def generate_launch_description():
    pkg_share = get_package_share_directory('arjuna_main')

    # Launch Configurations
    serial_port_arg = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyUSB0',
        description='LIDAR serial port'
    )

    drive_mode_arg = DeclareLaunchArgument(
        'drive_mode',
        default_value='differential',
        description='Drive mode: differential or mecanum'
    )

    motor_port_arg = DeclareLaunchArgument(
        'motor_port',
        default_value='/dev/ttyACM0',
        description='Motor controller serial port'
    )

    imu_device_arg = DeclareLaunchArgument(
        'imu_device',
        default_value=get_default_imu_device(),
        description='IMU I2C device path'
    )

    nav_arg = DeclareLaunchArgument(
        'nav',
        default_value='True',
        description='Whether to run Nav2 autonomous goal execution during SLAM mapping'
    )

    gui_arg = DeclareLaunchArgument(
        'gui',
        default_value='True',
        description='Whether to start RViz visualization'
    )

    # ========== TRANSFORM LAYER (Static TFs) ==========

    base_link_broadcaster = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_link_broadcaster',
        arguments=['0', '0', '0.09', '0', '0', '0', 'base_footprint', 'base_link']
    )

    base_link_to_laser = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_link_to_laser',
        arguments=['0', '0', '0.09', '3.14159265', '0', '0', 'base_link', 'laser']
    )

    imu_broadcaster = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='imu_broadcaster',
        arguments=['0', '0', '0', '-1.570796325', '0', '0', 'base_link', 'imu']
    )

    # ========== SENSOR & DRIVER LAYER ==========

    motor_driver = Node(
        package='motor_controller',
        executable='motor_node',
        name='motor_driver',
        output='screen',
        parameters=[{
            'port': LaunchConfiguration('motor_port'),
            'baudrate': 1000000,
            'drive_mode': LaunchConfiguration('drive_mode'),
            'speed_scaling': 10000,
            'tick_scaling': 2.5,
            'invert_y': False
        }],
        remappings=[
            ('cmd_vel', '/cmd_vel'),
            ('/cmd_vel', '/cmd_vel'),
            ('odom', '/wheel/odom'),
            ('/odom', '/wheel/odom'),
        ]
    )

    wheel_odom = Node(
        package='arjuna_odometry',
        executable='arjuna_ekf_odom_pub',
        name='arjuna_ekf_odom_pub',
        parameters=[{
            'publish_tf': False,  # EKF publishes TF
            'wheel_radius': 0.04,
            'wheel_base': 0.30,
            'ticks_per_revolution': 4096.0,
            'tick_scaling': 2.5,
            'odom_frame': 'odom',
            'base_frame': 'base_footprint'
        }],
        remappings=[
            ('/odom', '/wheel/odom'),
            ('/odom_data_quat', '/wheel/odom_data_quat'),
            ('/odom_data_euler', '/wheel/odom_data_euler')
        ]
    )

    imu_node = Node(
        package='imu_bno055',
        executable='bno055_i2c_node',
        name='imu_node',
        namespace='imu',
        parameters=[{
            'device': LaunchConfiguration('imu_device'),
            'address': 40,
            'frame_id': 'imu'
        }],
        remappings=[
            ('/data', '/imu/data'),
            ('/raw', '/imu/raw'),
            ('/mag', '/imu/mag'),
            ('/status', '/imu/status'),
            ('/temp', 'imu/temp'),
        ],
        output='screen'
    )

    lidar_node = Node(
        package='sllidar_ros2',
        executable='sllidar_node',
        name='sllidar_node',
        parameters=[{
            'channel_type': 'serial',
            'serial_port': LaunchConfiguration('serial_port'),
            'serial_baudrate': 460800,
            'frame_id': 'laser',
            'inverted': False,
            'angle_compensate': True,
            'scan_mode': 'Standard'
        }],
        remappings=[
            ('scan', '/scan'),
            ('/scan', '/scan'),
        ],
        output='screen'
    )

    # ========== FUSION LAYER ==========

    robot_localization_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_fusion',
        output='screen',
        parameters=[{
            'frequency': 30.0,
            'sensor_timeout': 1.0,
            'two_d_mode': True,
            'publish_tf': True,

            'odom_frame': 'odom',
            'base_link_frame': 'base_footprint',
            'world_frame': 'odom',

            # Wheel odometry velocities
            'odom0': '/wheel/odom',
            'odom0_config': [False, False, False,
                            False, False, False,
                            True,  False, False,
                            False, False, True,
                            False, False, False],
            'odom0_differential': False,

            # IMU yaw and yaw rate
            'imu0': '/imu/data',
            'imu0_config': [False, False, False,
                          False, False, True,
                          False, False, False,
                          False, False, True,
                          False, False, False],
            'imu0_differential': False,
            'imu0_relative': True,
            'imu0_remove_gravitational_acceleration': True,

            'debug': False
        }],
        remappings=[
            ('/odometry/filtered', '/odom')
        ]
    )

    # ========== SLAM LAYER ==========

    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[{
            'use_sim_time': False,
            'base_frame': 'base_footprint',
            'odom_frame': 'odom',
            'map_frame': 'map',
            'scan_topic': '/scan',
            'mode': 'mapping',

            'minimum_travel_distance': 0.01,
            'minimum_travel_heading': 0.01,
            'minimum_time_interval': 0.1,

            'transform_publish_period': 0.02,
            'transform_timeout': 0.2,
            'tf_buffer_duration': 30.0,

            'resolution': 0.05,
            'max_laser_range': 12.0,
            'map_update_interval': 1.0,

            'throttle_scans': 1,
            'stack_size_to_use': 40000000,
            'enable_interactive_mode': True,

            'do_loop_closing': True,
            'loop_search_maximum_distance': 3.0,
            'loop_match_minimum_chain_size': 10,

            'scan_buffer_size': 10,
            'scan_buffer_maximum_scan_distance': 10.0,
            'link_match_minimum_response_fine': 0.1,
            'link_scan_maximum_distance': 1.5,
            'correlation_search_space_dimension': 0.5,
            'correlation_search_space_resolution': 0.01
        }]
    )

    # ========== NAV2 NAVIGATION LAYER (Online SLAM Goal Navigation) ==========

    nav2_params_file = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    default_bt_xml = os.path.join(pkg_share, 'behavior_trees', 'arjuna_nav_bt.xml')

    with open(nav2_params_file, 'r') as f:
        nav2_cfg = yaml.safe_load(f)

    controller_params = nav2_cfg.get('controller_server', {}).get('ros__parameters', {})
    planner_params = nav2_cfg.get('planner_server', {}).get('ros__parameters', {})
    behavior_params = nav2_cfg.get('behavior_server', {}).get('ros__parameters', {})
    bt_params = nav2_cfg.get('bt_navigator', {}).get('ros__parameters', {})

    local_costmap_raw = nav2_cfg.get('local_costmap', {}).get('local_costmap', {}).get('ros__parameters', {})
    global_costmap_raw = nav2_cfg.get('global_costmap', {}).get('global_costmap', {}).get('ros__parameters', {})

    local_costmap_slam = copy.deepcopy(local_costmap_raw)
    local_costmap_slam['global_frame'] = 'odom'
    local_costmap_slam['robot_base_frame'] = 'base_footprint'
    if 'obstacle_layer' in local_costmap_slam and isinstance(local_costmap_slam['obstacle_layer'], dict):
        if 'scan' in local_costmap_slam['obstacle_layer'] and isinstance(local_costmap_slam['obstacle_layer']['scan'], dict):
            local_costmap_slam['obstacle_layer']['scan']['topic'] = '/scan'

    global_costmap_slam = copy.deepcopy(global_costmap_raw)
    global_costmap_slam['global_frame'] = 'map'
    global_costmap_slam['robot_base_frame'] = 'base_footprint'
    global_costmap_slam.setdefault('static_layer', {})
    global_costmap_slam['static_layer']['map_topic'] = '/map'
    if 'obstacle_layer' in global_costmap_slam and isinstance(global_costmap_slam['obstacle_layer'], dict):
        if 'scan' in global_costmap_slam['obstacle_layer'] and isinstance(global_costmap_slam['obstacle_layer']['scan'], dict):
            global_costmap_slam['obstacle_layer']['scan']['topic'] = '/scan'

    slam_costmap_file = '/tmp/slam_nav_costmaps.yaml'
    with open(slam_costmap_file, 'w') as f:
        yaml.safe_dump({
            'local_costmap': {
                'local_costmap': {
                    'ros__parameters': local_costmap_slam
                }
            },
            'global_costmap': {
                'global_costmap': {
                    'ros__parameters': global_costmap_slam
                }
            },
            '/**': {
                'local_costmap': {
                    'local_costmap': {
                        'ros__parameters': local_costmap_slam
                    }
                },
                'global_costmap': {
                    'global_costmap': {
                        'ros__parameters': global_costmap_slam
                    }
                }
            }
        }, f)

    controller_server_node = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[controller_params, slam_costmap_file],
        remappings=[
            ('cmd_vel', '/cmd_vel'),
            ('odom', '/odom'),
        ],
        condition=IfCondition(LaunchConfiguration('nav'))
    )

    planner_server_node = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[planner_params, slam_costmap_file],
        remappings=[
            ('map', '/map'),
        ],
        condition=IfCondition(LaunchConfiguration('nav'))
    )

    behavior_server_node = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[behavior_params, {
            'global_frame': 'odom',
            'robot_base_frame': 'base_footprint',
        }],
        remappings=[
            ('cmd_vel', '/cmd_vel'),
        ],
        condition=IfCondition(LaunchConfiguration('nav'))
    )

    bt_navigator_node = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[bt_params, {
            'default_nav_to_pose_bt_xml': default_bt_xml,
            'global_frame': 'map',
            'robot_base_frame': 'base_footprint',
            'odom_topic': '/odom',
        }],
        condition=IfCondition(LaunchConfiguration('nav'))
    )

    nav_lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{
            'use_sim_time': False,
            'autostart': True,
            'node_names': [
                'controller_server',
                'planner_server',
                'behavior_server',
                'bt_navigator'
            ],
            'bond_timeout': 10.0,
            'attempt_respawn_reconnection': True,
        }],
        condition=IfCondition(LaunchConfiguration('nav'))
    )

    delayed_nav_lifecycle = TimerAction(
        period=4.0,
        actions=[nav_lifecycle_manager]
    )

    # Bridge RViz 2D Goal Pose (/goal_pose) directly to Nav2 action client
    rviz_goal_bridge = Node(
        package='arjuna_main',
        executable='rviz_goal_bridge',
        name='rviz_goal_bridge',
        output='screen',
        parameters=[{'robot_id': ''}],
        condition=IfCondition(LaunchConfiguration('nav'))
    )

    # ========== VISUALIZATION ==========

    rviz_config_path = os.path.join(pkg_share, 'rviz', 'slam.rviz')

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path] if os.path.exists(rviz_config_path) else [],
        output='screen',
        condition=IfCondition(LaunchConfiguration('gui'))
    )

    # ========== AUTOMATIC MAP SAVER ==========
    maps_dir = os.path.join(pkg_share, 'maps')
    if not os.path.exists(maps_dir):
        maps_dir = '/home/arjuna/Arjuna_ws_team3/src/arjuna_main/arjuna_main/maps'
    os.makedirs(maps_dir, exist_ok=True)

    if not os.path.exists(os.path.join(maps_dir, 'my_map.yaml')):
        map_name = 'my_map'
    else:
        i = 1
        while os.path.exists(os.path.join(maps_dir, f'my_map{i}.yaml')):
            i += 1
        map_name = f'my_map{i}'

    map_path = os.path.join(maps_dir, map_name)

    save_map_on_exit = RegisterEventHandler(
        OnProcessExit(
            target_action=rviz_node,
            on_exit=[
                Node(
                    package='nav2_map_server',
                    executable='map_saver_cli',
                    name='map_saver',
                    output='screen',
                    arguments=['-f', map_path],
                    parameters=[{'use_sim_time': False}]
                )
            ]
        )
    )

    return LaunchDescription([
        # Arguments
        serial_port_arg,
        drive_mode_arg,
        motor_port_arg,
        imu_device_arg,
        nav_arg,
        gui_arg,

        # Static TFs
        base_link_broadcaster,
        base_link_to_laser,
        imu_broadcaster,

        # Sensor & Driver layer
        motor_driver,
        wheel_odom,
        imu_node,
        lidar_node,

        # Fusion layer
        robot_localization_node,

        # SLAM layer
        slam_toolbox_node,

        # Online SLAM Nav2 Navigation
        controller_server_node,
        planner_server_node,
        behavior_server_node,
        bt_navigator_node,
        delayed_nav_lifecycle,
        rviz_goal_bridge,

        # RViz & Map auto-save
        rviz_node,
        save_map_on_exit
    ])
