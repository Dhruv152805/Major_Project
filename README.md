# Arjuna Autonomous Robot Workspace

This is the primary ROS 2 (Humble) workspace for **Arjuna**, an autonomous mobile robot. It integrates custom motor drivers, sensor fusion, SLAM mapping, and the Navigation2 (Nav2) stack. It supports both **Differential Drive** and **Mecanum Drive** configurations.

---

## 📂 Workspace Architecture

The workspace is organized into modular ROS 2 packages under `src/`:

```
Arjuna_ws/
├── requirements.txt                   # Workspace-wide Python pip dependencies
├── tf_inversion_fix.md                # Detailed analysis of LIDAR orientation fixes
├── README.md                          # Master documentation (this file)
└── src/
    ├── arjuna_main/                   # Integration, bringup launch, maps, and Nav2 config
    │   ├── arjuna_main/
    │   │   ├── config/nav2_params.yaml # Tuned Nav2 parameters (costmaps, planner, controller)
    │   │   ├── launch/                # Main integration launch files
    │   │   │   ├── bringup_launch.py  # Navigation, localization, EKF fusion & drivers
    │   │   │   └── mapping_launch.py  # SLAM mapping stack, EKF fusion & drivers
    │   │   ├── scripts/
    │   │   │   ├── Arjuna_navigation/ # Nav2 Action Clients & obstacle avoidance
    │   │   │   ├── Arjuna_opencv/     # Camera stream & QR tracking/centering
    │   │   │   └── Newrro_NavLib/     # Navigation helper library
    │   │   └── rviz/                  # RViz configurations for slam/navigation
    │   └── package.xml
    │
    ├── arjuna_controller/             # Stateful, keyboard-teleoperation node
    │   └── arjuna_controller/
    │       └── Arjuna_Controller.py   # Differential & Mecanum keybind controller
    │
    ├── arjuna_odometry/               # Encoder tick fusion & RViz conversion helpers
    │   └── src/
    │       ├── arjuna_ekf_odom_pub.cpp # Computes /wheel/odom from motor ticks
    │       └── arjuna_rviz_data_pub.cpp# Converts 3D RViz clicks to 2D formats
    │
    ├── arjuna_pub_sub/                # Core string topics & ultrasonic sensor publishers
    │   └── arjuna_pub_sub/
    │       ├── US_Pub.py              # Reads ultrasonic distances from Arduino over Serial
    │       └── US_Sub.py              # Diagnostic subscriber & obstacle warning node
    │
    ├── motor_controller/              # STServo SDK serial bridge for smart motor controls
    │   └── motor_controller/
    │       └── motor_node.py          # Differential & Mecanum kinematics mapping via SyncRead/SyncWrite
    │
    ├── arjuna_camera/                 # OAK-D 3D Spatial AI Vision, Depth & Semantic Mapping
    │   ├── arjuna_camera/
    │   │   └── teaching_node.py       # On-device MobileNet inference, depth projection & services
    │   ├── launch/teaching.launch.py  # Camera pipeline & static TF launch
    │   ├── models/                    # OpenVINO MobileNet-SSD blob models
    │   ├── rviz/teaching.rviz         # Pre-configured 3D semantic map & detection RViz profile
    │   └── srv/                       # GetObjectPose & ListObjects custom services
    │
    ├── ros-imu-bno055/                # BNO055 IMU sensor driver
    └── sllidar_ros2/                  # RPLidar A1/A2/A3 LIDAR sensor driver
```

---

## ⚙️ Core Calibrations & Configurations

The robot's physical mounting and kinematics are calibrated across all nodes in the workspace:

### 1. 180° LIDAR Orientation Correction
* **Physical Mounting:** The LIDAR is mounted facing backwards (180° rotated relative to the physical front of the chassis).
* **Launch configuration:** Corrected static transforms publish base link relations with 180° yaw rotation:
  `base_link` ➔ `laser` TF yaw offset: `3.14159265` rad.
* **Scan Processing:** The laser scan sectors in the reactive obstacle avoidance (`Arjuna_obstacle_avoidance.py`) and QR centering (`Arjuna_QR_CT.py`) are rotated by 180° to read the robot's physical front (middle indices of the LIDAR scan array).

### 2. 0.38m Chassis Reflection Filter
* To prevent false-positive front-obstacle triggers caused by chassis self-reflections, a robust **0.38m minimum range filter** is configured across the system:
  * **Nav2 Costmaps:** `obstacle_min_range` is set to `0.38`m in `nav2_params.yaml`.
  * **Obstacle Avoidance:** Readings `< 0.38`m are discarded in `Arjuna_obstacle_avoidance.py`.
  * **QR Centering:** Readings `< 0.38`m are discarded in `Arjuna_QR_CT.py`.

### 3. Nav2 Costmap Tunings
* `robot_radius`: `0.15`m (protects wheels and chassis corners).
* `inflation_radius`: `0.30`m.
* `cost_scaling_factor`: `10.0` (gentler costmap gradient, repelling the robot earlier).

### 4. Geometry and Ticks
* **Wheel Radius:** `0.04`m (80mm rubber wheels).
* **Wheel Base (Track Width):** `0.30`m.
* **STS Smart Servos:** Encoder resolution `4096.0` ticks per rev, scaled down by `2.5` to match odometry.

---

## 🛠️ Build and Compilation

### Prerequisites
Install ROS 2 Humble packages and Python dependencies:
```bash
sudo apt update
sudo apt install -y \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-slam-toolbox \
  ros-humble-robot-localization \
  ros-humble-tf2-geometry-msgs

pip install -r requirements.txt
```

### Compiling Workspace
Run the build script at the root:
```bash
cd ~/Arjuna_ws
colcon build --symlink-install
source install/setup.bash
```

---

## 🚀 Operating the Robot

### 1. Launching Bringup (Differential Mode)
Starts state transforms, LIDAR, IMU, Motor Node, EKF Fusion, Nav2 map loading, AMCL localization, and RViz:
```bash
ros2 launch arjuna_main bringup_launch.py
```
*For Mecanum Drive:*
```bash
ros2 launch arjuna_main bringup_launch.py drive_mode:=mecanum
```

### 2. Interactive Terminal Navigation
Use the terminal menu to send absolute (Map-frame) or relative (robot-frame) coordinates:
```bash
ros2 run arjuna_main arjuna_terminal_goal
```

### 3. Stateful Teleoperation Control
Drive the robot using stateful keyboard commands (SPACE for Emergency Stop):
```bash
ros2 run arjuna_controller Arjuna_Controller
```

### 4. SLAM Mapping
Build a new map using SLAM:
```bash
ros2 launch arjuna_main mapping_launch.py
```
* **Auto-Save Map:** Close the RViz window, and the mapped workspace will automatically save inside `src/arjuna_main/arjuna_main/maps/` as `my_map.yaml` and `my_map.pgm`. Incremental backup naming (`my_map1`, `my_map2`, etc.) is fully supported.

### 5. 3D Spatial AI Vision & Semantic Mapping
Launch real-time 3D object detection, depth sensing, and RViz semantic map visualization:
```bash
# Terminal 1: Camera node & static transforms
ros2 launch arjuna_camera teaching.launch.py

# Terminal 2: Pre-configured RViz visualizer
rviz2 -d src/arjuna_camera/rviz/teaching.rviz
```
* Query 3D object poses on demand:
```bash
ros2 service call /list_objects arjuna_camera/srv/ListObjects
ros2 service call /get_object_pose arjuna_camera/srv/GetObjectPose "{target_label: 'person'}"
```
