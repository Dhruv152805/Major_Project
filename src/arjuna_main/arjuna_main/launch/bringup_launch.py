
#!/usr/bin/env python3
"""
Arjuna Main Bringup Launch File — multi-robot namespaced version

CHANGES FROM ORIGINAL (single-robot) VERSION:
- New required-ish arg 'robot_id' (default 'arjuna_1') prefixes every
  robot-specific topic and TF frame with the robot's id, so two robots
  on the same ROS_DOMAIN_ID no longer collide/mirror each other.
- 'map' frame and the '/map' topic stay UNPREFIXED and shared - both
  robots localize against the same map.
- New arg 'run_map_server' (default True). Only ONE robot should launch
  the map server.
- Every robot-specific node name is suffixed with robot_id.
- lifecycle_manager_node is wrapped in a 5s TimerAction.
- Nav2 YAML sections are loaded explicitly as Python dictionaries because
  the actual Nav2 node names are suffixed with robot_id.

USAGE:
  Robot 1:
    ros2 launch arjuna_main bringup_launch.py \
      robot_id:=arjuna_1 run_map_server:=True

  Robot 2:
    ros2 launch arjuna_main bringup_launch.py \
      robot_id:=arjuna_2 run_map_server:=False
"""

import os
import copy
import yaml

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.conditions import IfCondition


def get_imu_device(configured_device):
    """
    Check if BNO055 is reachable on configured_device; if not, check common
    alternative I2C buses (e.g. /dev/i2c-7 on Robot 2 vs /dev/i2c-1 on Robot 1).
    """
    import fcntl
    def probe_bno055(dev_path):
        if not os.path.exists(dev_path):
            return False
        try:
            fd = os.open(dev_path, os.O_RDWR)
            # 0x0703 is I2C_SLAVE, address 40 (0x28) is BNO055 default
            fcntl.ioctl(fd, 0x0703, 0x28)
            os.write(fd, b'\x00')
            chip_id = os.read(fd, 1)
            os.close(fd)
            return chip_id == b'\xa0'
        except Exception:
            return False

    if probe_bno055(configured_device):
        return configured_device

    for alt in ['/dev/i2c-7', '/dev/i2c-1', '/dev/i2c-0']:
        if alt != configured_device and probe_bno055(alt):
            print(f"[bringup_launch] Auto-detected BNO055 on '{alt}' (configured '{configured_device}' was not responsive)")
            return alt

    return configured_device


def launch_setup(context, *args, **kwargs):
    pkg_share = get_package_share_directory('arjuna_main')

    robot_id = LaunchConfiguration('robot_id').perform(context)
    run_map_server = (
        LaunchConfiguration('run_map_server').perform(context) == 'True'
    )
    imu_device_configured = LaunchConfiguration('imu_device').perform(context)
    actual_imu_device = get_imu_device(imu_device_configured)

    nav2_params_file = os.path.join(
        pkg_share,
        'config',
        'nav2_params.yaml'
    )

    default_bt_xml_file = os.path.join(
        pkg_share,
        'behavior_trees',
        'arjuna_nav_bt.xml'
    )

    # ================================================================
    # LOAD NAV2 PARAMETERS
    # ================================================================
    #
    # The YAML contains sections such as:
    #
    #   controller_server:
    #     ros__parameters:
    #
    # But our actual node is:
    #
    #   controller_server_arjuna_1
    #
    # ROS 2 therefore does not automatically apply the
    # controller_server section to controller_server_arjuna_1.
    #
    # We explicitly load each section and pass it as a dictionary.
    # We also load local_costmap and global_costmap and inject them
    # directly into controller_server and planner_server.
    # ================================================================

    with open(nav2_params_file, 'r') as f:
        nav2_config = yaml.safe_load(f)

    amcl_params = nav2_config.get('amcl', {}).get('ros__parameters', {})

    controller_params = nav2_config.get('controller_server', {}).get('ros__parameters', {})

    planner_params = nav2_config.get('planner_server', {}).get('ros__parameters', {})

    behavior_params = nav2_config.get('behavior_server', {}).get('ros__parameters', {})

    bt_navigator_params = nav2_config.get('bt_navigator', {}).get('ros__parameters', {})

    map_server_params = nav2_config.get('map_server', {}).get('ros__parameters', {})

    # Costmaps
    local_costmap_raw = nav2_config.get('local_costmap', {}).get('local_costmap', {}).get('ros__parameters', {})
    global_costmap_raw = nav2_config.get('global_costmap', {}).get('global_costmap', {}).get('ros__parameters', {})

    # ================================================================
    # ROBOT-SPECIFIC FRAME NAMES
    # ================================================================

    base_footprint_frame = f'{robot_id}/base_footprint'
    base_link_frame = f'{robot_id}/base_link'
    laser_frame = f'{robot_id}/laser'
    imu_frame = f'{robot_id}/imu'
    odom_frame = f'{robot_id}/odom'

    # map stays shared between robots
    map_frame = 'map'

    # ================================================================
    # ROBOT-SPECIFIC TOPIC NAMES
    # ================================================================

    t_scan = f'/{robot_id}/scan'

    t_odom = f'/{robot_id}/odom'

    t_wheel_odom = f'/{robot_id}/wheel/odom'

    t_wheel_odom_quat = (
        f'/{robot_id}/wheel/odom_data_quat'
    )

    t_wheel_odom_euler = (
        f'/{robot_id}/wheel/odom_data_euler'
    )

    t_imu_data = f'/{robot_id}/imu/data'

    t_imu_raw = f'/{robot_id}/imu/raw'

    t_imu_mag = f'/{robot_id}/imu/mag'

    t_imu_status = f'/{robot_id}/imu/status'

    t_imu_temp = f'/{robot_id}/imu/temp'

    t_ekf_output = (
        f'/{robot_id}/robot_pose_ekf/odom_combined'
    )

    t_cmd_vel = f'/{robot_id}/cmd_vel'

    t_initialpose = f'/{robot_id}/initialpose'

    # Prepare robot-specific costmaps
    local_costmap_params = copy.deepcopy(local_costmap_raw)
    local_costmap_params['global_frame'] = odom_frame
    local_costmap_params['robot_base_frame'] = base_footprint_frame
    if 'obstacle_layer' in local_costmap_params and isinstance(local_costmap_params['obstacle_layer'], dict):
        if 'scan' in local_costmap_params['obstacle_layer'] and isinstance(local_costmap_params['obstacle_layer']['scan'], dict):
            local_costmap_params['obstacle_layer']['scan']['topic'] = t_scan

    global_costmap_params = copy.deepcopy(global_costmap_raw)
    global_costmap_params['global_frame'] = map_frame
    global_costmap_params['robot_base_frame'] = base_footprint_frame
    if 'obstacle_layer' in global_costmap_params and isinstance(global_costmap_params['obstacle_layer'], dict):
        if 'scan' in global_costmap_params['obstacle_layer'] and isinstance(global_costmap_params['obstacle_layer']['scan'], dict):
            global_costmap_params['obstacle_layer']['scan']['topic'] = t_scan

    # The costmap sub-node does not inherit the ('map', '/map') remap from
    # planner_server, so its static layer would subscribe to the relative
    # topic /<robot_id>/map, which nobody publishes. Point it at the shared
    # absolute /map topic published by the single map_server.
    global_costmap_params.setdefault('static_layer', {})
    global_costmap_params['static_layer']['map_topic'] = '/map'

    # The costmaps are sub-nodes:
    #   /{robot_id}/local_costmap/local_costmap
    #   /{robot_id}/global_costmap/global_costmap
    # In ROS 2, parameters must follow the namespace hierarchy in YAML.
    # We provide nested, wildcard, and direct formats to guarantee all parameters load.
    costmap_param_file = f'/tmp/{robot_id}_costmaps.yaml'

    class NoAliasDumper(yaml.SafeDumper):
        def ignore_aliases(self, data):
            return True

    with open(costmap_param_file, 'w') as f:
        yaml.dump({
            robot_id: {
                'local_costmap': {
                    'local_costmap': {
                        'ros__parameters': copy.deepcopy(local_costmap_params)
                    }
                },
                'global_costmap': {
                    'global_costmap': {
                        'ros__parameters': copy.deepcopy(global_costmap_params)
                    }
                },
            },
            f'/{robot_id}/local_costmap/local_costmap': {
                'ros__parameters': copy.deepcopy(local_costmap_params)
            },
            f'/{robot_id}/global_costmap/global_costmap': {
                'ros__parameters': copy.deepcopy(global_costmap_params)
            },
            'local_costmap': {
                'local_costmap': {
                    'ros__parameters': copy.deepcopy(local_costmap_params)
                }
            },
            'global_costmap': {
                'global_costmap': {
                    'ros__parameters': copy.deepcopy(global_costmap_params)
                }
            },
            '/**': {
                'local_costmap': {
                    'local_costmap': {
                        'ros__parameters': copy.deepcopy(local_costmap_params)
                    }
                },
                'global_costmap': {
                    'global_costmap': {
                        'ros__parameters': copy.deepcopy(global_costmap_params)
                    }
                }
            }
        }, f, Dumper=NoAliasDumper)

    # ================================================================
    # MAP FILE
    # ================================================================

    maps_dir = os.path.join(
        pkg_share,
        'maps'
    )

    installed_map_path = os.path.join(
        maps_dir,
        'my_map.yaml'
    )

    default_map_path = installed_map_path

    if os.path.exists(maps_dir):
        try:
            yaml_files = [
                f
                for f in os.listdir(maps_dir)
                if f.endswith('.yaml')
            ]

            if yaml_files:
                yaml_files.sort(
                    key=lambda x: os.path.getmtime(
                        os.path.join(maps_dir, x)
                    ),
                    reverse=True
                )

                default_map_path = os.path.join(
                    maps_dir,
                    yaml_files[0]
                )

        except Exception:
            pass

    map_path = (
        LaunchConfiguration('map').perform(context)
        or default_map_path
    )

    # ================================================================
    # TRANSFORM LAYER
    # ================================================================

    base_link_broadcaster = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name=f'base_link_broadcaster_{robot_id}',
        arguments=[
            '0',
            '0',
            '0.09',
            '0',
            '0',
            '0',
            base_footprint_frame,
            base_link_frame
        ]
    )

    base_link_to_laser = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name=f'base_link_to_laser_{robot_id}',
        arguments=[
            '0',
            '0',
            '0.09',
            '3.14159265',
            '0',
            '0',
            base_link_frame,
            laser_frame
        ]
    )

    imu_broadcaster = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name=f'imu_broadcaster_{robot_id}',
        arguments=[
            '0',
            '0',
            '0',
            '-1.570796325',
            '0',
            '0',
            base_link_frame,
            imu_frame
        ]
    )

    # ================================================================
    # SENSOR & DRIVER LAYER
    # ================================================================

    motor_driver = Node(
        package='motor_controller',
        executable='motor_node',
        name=f'motor_driver_{robot_id}',
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
            ('/odom', t_odom),
            ('/cmd_vel', t_cmd_vel),
            ('odom', t_odom),
            ('cmd_vel', t_cmd_vel),
            ('left_ticks', f'/{robot_id}/left_ticks'),
            ('/left_ticks', f'/{robot_id}/left_ticks'),
            ('right_ticks', f'/{robot_id}/right_ticks'),
            ('/right_ticks', f'/{robot_id}/right_ticks'),
        ]
    )

    wheel_odom = Node(
        package='arjuna_odometry',
        executable='arjuna_ekf_odom_pub',
        name=f'arjuna_ekf_odom_pub_{robot_id}',

        parameters=[{
            'publish_tf': False,
            'wheel_radius': 0.04,
            'wheel_base': 0.30,
            'ticks_per_revolution': 4096.0,
            'tick_scaling': 2.5,
            'odom_frame': odom_frame,
            'base_frame': base_footprint_frame
        }],

        remappings=[
            ('/odom', t_wheel_odom),
            ('/odom_data_quat', t_wheel_odom_quat),
            ('/odom_data_euler', t_wheel_odom_euler),
            ('left_ticks', f'/{robot_id}/left_ticks'),
            ('/left_ticks', f'/{robot_id}/left_ticks'),
            ('right_ticks', f'/{robot_id}/right_ticks'),
            ('/right_ticks', f'/{robot_id}/right_ticks'),
        ]
    )

    imu_node = Node(
        package='imu_bno055',
        executable='bno055_i2c_node',
        name=f'imu_node_{robot_id}',
        output='screen',

        parameters=[{
            'device': actual_imu_device,
            'address': 40,
            'frame_id': imu_frame
        }],

        remappings=[
            ('/data', t_imu_data),
            ('/raw', t_imu_raw),
            ('/mag', t_imu_mag),
            ('/status', t_imu_status),
            ('/temp', t_imu_temp),
        ]
    )

    lidar_node = Node(
        package='sllidar_ros2',
        executable='sllidar_node',
        name=f'sllidar_node_{robot_id}',
        output='screen',

        parameters=[{
            'channel_type': 'serial',
            'serial_port': LaunchConfiguration('serial_port'),
            'serial_baudrate': 460800,
            'frame_id': laser_frame,
            'inverted': False,
            'angle_compensate': True,
            'scan_mode': 'Standard'
        }],

        remappings=[
            ('scan', t_scan),
            ('/scan', t_scan),
        ]
    )

    # ================================================================
    # FUSION LAYER
    # ================================================================

    robot_localization_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name=f'robot_pose_ekf_{robot_id}',
        output='screen',

        parameters=[{
            'frequency': 30.0,
            'sensor_timeout': 1.0,
            'two_d_mode': True,
            'publish_tf': True,

            'map_frame': map_frame,
            'odom_frame': odom_frame,
            'base_link_frame': base_footprint_frame,
            'world_frame': odom_frame,

            'odom0': t_wheel_odom,

            'odom0_config': [
                False,
                False,
                False,
                False,
                False,
                False,
                True,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False
            ],

            'odom0_differential': False,

            'imu0': t_imu_data,

            'imu0_config': [
                False,
                False,
                False,
                False,
                False,
                True,
                False,
                False,
                False,
                False,
                False,
                True,
                False,
                False,
                False
            ],

            'imu0_differential': False,
            'imu0_relative': True,
            'imu0_remove_gravitational_acceleration': True,

            'debug': False
        }],

        remappings=[
            ('odometry/filtered', t_ekf_output)
        ]
    )

    rviz_data_pub = Node(
        package='arjuna_odometry',
        executable='arjuna_rviz_data_pub',
        name=f'rviz_data_pub_{robot_id}',
        output='screen',
        remappings=[
            ('/initialpose', t_initialpose),
            ('initialpose', t_initialpose),
            ('/move_base_simple/goal', f'/{robot_id}/move_base_simple/goal'),
            ('move_base_simple/goal', f'/{robot_id}/move_base_simple/goal'),
        ]
    )

    # ================================================================
    # MAP SERVER
    # ================================================================

    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',

        parameters=[map_server_params, {
            'yaml_filename': map_path,
            'topic_name': 'map',
            'frame_id': map_frame
        }],

        condition=(
            IfCondition('True')
            if run_map_server
            else IfCondition('False')
        )
    )

    # ================================================================
    # AMCL
    # ================================================================

    amcl_node = Node(
        namespace=robot_id,
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',

        parameters=[amcl_params, {
            'base_frame_id': base_footprint_frame,
            'odom_frame_id': odom_frame,
            'global_frame_id': map_frame,
            'scan_topic': t_scan,
        }],

        remappings=[
            ('map', '/map'),
        ]
    )

    # ================================================================
    # CONTROLLER SERVER
    # ================================================================

    controller_server_node = Node(
        namespace=robot_id,
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',

        parameters=[
            controller_params,
            costmap_param_file,
        ],

        remappings=[
            ('cmd_vel', t_cmd_vel),
            ('odom', t_ekf_output),
        ]
    )

    # ================================================================
    # PLANNER SERVER
    # ================================================================

    planner_server_node = Node(
        namespace=robot_id,
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',

        parameters=[
            planner_params,
            costmap_param_file,
        ],

        remappings=[
            ('map', '/map'),
            ('/map', '/map'),
            (f'/{robot_id}/map', '/map'),
            (f'/{robot_id}/global_costmap/map', '/map'),
        ]
    )

    # Bridge RViz 2D Goal Pose to Nav2 Action Server
    rviz_goal_bridge = Node(
        package='arjuna_main',
        executable='rviz_goal_bridge',
        name=f'rviz_goal_bridge_{robot_id}',
        output='screen',
        parameters=[{'robot_id': robot_id}]
    )

    # ================================================================
    # BEHAVIOR SERVER
    # ================================================================

    behavior_server_node = Node(
        namespace=robot_id,
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',

        parameters=[behavior_params, {
            'global_frame': odom_frame,
            'robot_base_frame': base_footprint_frame,
        }],

        remappings=[
            ('cmd_vel', t_cmd_vel),
        ]
    )

    # ================================================================
    # BT NAVIGATOR
    # ================================================================

    bt_navigator_node = Node(
        namespace=robot_id,
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',

        parameters=[bt_navigator_params, {
            'default_nav_to_pose_bt_xml': default_bt_xml_file,
            'global_frame': map_frame,
            'robot_base_frame': base_footprint_frame,
            'odom_topic': t_ekf_output,
        }]
    )

    # ================================================================
    # LIFECYCLE MANAGERS
    # ================================================================

    lifecycle_manager_node = Node(
        namespace=robot_id,
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',

        parameters=[{
            'use_sim_time': False,
            'autostart': True,
            'node_names': [
                'amcl',
                'controller_server',
                'planner_server',
                'behavior_server',
                'bt_navigator'
            ],
            'bond_timeout': 10.0,
            'attempt_respawn_reconnection': True,
        }]
    )

    delayed_lifecycle_manager = TimerAction(
        period=5.0,
        actions=[lifecycle_manager_node]
    )

    map_server_lifecycle_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map_server',
        output='screen',

        parameters=[{
            'use_sim_time': False,
            'autostart': True,
            'node_names': ['map_server'],
            'bond_timeout': 10.0,
            'attempt_respawn_reconnection': True,
        }],

        condition=(
            IfCondition('True')
            if run_map_server
            else IfCondition('False')
        )
    )

    delayed_map_server_lifecycle = TimerAction(
        period=2.0,
        actions=[map_server_lifecycle_node]
    )

    # ================================================================
    # RVIZ
    # ================================================================

    rviz_config_path = os.path.join(
        pkg_share,
        'rviz',
        'arjuna.rviz'
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name=f'rviz2_{robot_id}',

        arguments=(
            ['-d', rviz_config_path]
            if os.path.exists(rviz_config_path)
            else []
        ),

        condition=IfCondition(
            LaunchConfiguration('gui')
        ),

        output='screen'
    )

    # ================================================================
    # NODE LIST
    # ================================================================

    nodes = [
        base_link_broadcaster,
        base_link_to_laser,
        imu_broadcaster,

        amcl_node,
        controller_server_node,
        planner_server_node,
        behavior_server_node,
        bt_navigator_node,

        delayed_lifecycle_manager,

        motor_driver,
        wheel_odom,
        imu_node,
        lidar_node,
        robot_localization_node,
        rviz_data_pub,
        rviz_goal_bridge,
        rviz_node,
    ]

    if run_map_server:
        nodes.insert(3, map_server_node)
        nodes.insert(4, delayed_map_server_lifecycle)

    return nodes


def generate_launch_description():
    return LaunchDescription([

        DeclareLaunchArgument(
            'robot_id',
            default_value='arjuna_1',
            description=(
                'Unique robot identifier - used to prefix '
                'all topics and TF frames'
            )
        ),

        DeclareLaunchArgument(
            'run_map_server',
            default_value='True',
            description=(
                'Only ONE robot should run this - '
                'True for one robot, False for the other'
            )
        ),

        DeclareLaunchArgument(
            'gui',
            default_value='True',
            description='Whether to start RViz'
        ),

        DeclareLaunchArgument(
            'serial_port',
            default_value='/dev/ttyUSB0',
            description='LIDAR serial port'
        ),

        DeclareLaunchArgument(
            'drive_mode',
            default_value='differential',
            description='Drive mode: differential or mecanum'
        ),

        DeclareLaunchArgument(
            'motor_port',
            default_value='/dev/ttyACM0',
            description='Motor controller serial port'
        ),

        DeclareLaunchArgument(
            'imu_device',
            default_value='/dev/i2c-1',
            description='IMU I2C device path'
        ),

        DeclareLaunchArgument(
            'map',
            default_value='',
            description='Full path to map yaml file to load'
        ),

        OpaqueFunction(
            function=launch_setup
        ),
    ])
