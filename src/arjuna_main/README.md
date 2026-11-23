# Arjuna Main Integration Package

This is the main bringup, mapping, and navigation integration package for the Arjuna autonomous robot. It coordinates all hardware drivers, sensor streams, fusion, and mapping nodes into structured launch files.

---

## Maintainer
* **Maintainer**: Newrro Tech (Tushar S)
* **Email**: [info@newrro.in](mailto:info@newrro.in)

---

## Dependencies & Prerequisites

Before building and running the workspace, ensure all system (APT) and python (PIP) dependencies are installed.

### 1. ROS 2 & System Packages (APT)
Run the following commands to install the required ROS 2 Humble packages:
```bash
sudo apt update
sudo apt install -y \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-slam-toolbox \
  ros-humble-robot-localization \
  ros-humble-tf2-geometry-msgs
```

### 2. Python Packages (PIP)
Install the required python packages for camera interface, serial comms, and QR tracking using pip:
```bash
pip install -r requirements.txt
```
*(Or install them individually)*:
```bash
pip install pyserial depthai opencv-python pyzbar numpy
```

---

## Package Architecture

```
arjuna_main/
├── README.md                          # This documentation file
├── package.xml                        # Package dependencies and executor configurations
├── setup.py                           # Console scripts and installation configurations
├── setup.cfg                          # Build configurations
└── arjuna_main/
    ├── behavior_trees/                # Nav2 behavior trees (arjuna_nav_bt.xml, arjuna_nav_through_poses_bt.xml)
    ├── config/                        # Shared parameters and config files
    │   └── nav2_params.yaml           # Detailed parameters for the Nav2 navigation stack
    ├── launch/
    │   ├── bringup_launch.py          # Main launch file for Nav2 navigation, 
    │   └── mapping_launch.py          # Main launch file for SLAM mapping and drivers
    ├── maps/                          # Saved PGM/YAML map files
    ├── rviz/
    │   ├── arjuna.rviz                # RViz setup for localization & navigation
    │   └── slam.rviz                  # RViz setup for SLAM mapping
    ├── scripts/
    │   ├── Data_code.py               # ROS 2 I2C Ultrasonic Sensor Publisher & MOSFET Light Controller
    │   ├── Arjuna_navigation/         # Active navigation nodes (Nav2 Action Clients)
    │   │   ├── Arjuna_go_to_point_terminal.py   # Send single goal to Nav2 via terminal
    │   │   ├── arjuna_terminal_goal.py         # Interactive goal sender with relative/absolute modes
    │   │   ├── Arjuna_multi_point_terminal.py  # Send waypoints to Nav2 via terminal
    │   │   └── Arjuna_obstacle_avoidance.py    # Autonomous reactive obstacle avoidance
    │   ├── Arjuna_opencv/             # Camera & computer vision nodes
    │   │   ├── Arjuna_camera_pub.py            # Stream video frames (CompressedImage)
    │   │   ├── Arjuna_camera_sub.py            # Display video stream in OpenCV window
    │   │   ├── Arjuna_QR_Rec.py                # QR recognition diagnostics node
    │   │   ├── Arjuna_QR_tracking.py           # Detect/track QR target "Arjuna"
    │   │   └── Arjuna_QR_CT.py                 # Center QR code using rotational control
    │   └── Newrro_NavLib/             # Custom path tracking & obstacle avoidance math library
    │       ├── Newrro_Navigation.py
    │       └── Newrro_obs_script.py
    └── webpage/                       # Web visualization files
```

---

## Launch Files

### 1. `bringup_launch.py`
This launch file brings up the full physical system for localization and navigation:
* **Static Transforms (TF)**:
  * `base_footprint` ➔ `base_link` (z: `0.09` offset)
  * `base_link` ➔ `laser` (z: `0.09` offset, yaw: `3.14159265` / 180° rotation correction for backward-mounted LIDAR)
  * `base_link` ➔ `imu` (roll: `-1.570796325` / 90° orientation pitch-roll offset correction)
* **Drivers & Hardware**:
  * `motor_controller/motor_node`: Dynamically maps velocity commands to hardware IDs according to the selected drive mode.
  * `arjuna_odometry/arjuna_ekf_odom_pub`: Converts wheel ticks to raw odometry velocity on `/wheel/odom` (re-mapped to prevent transform duplication).
  * `imu_bno055/bno055_i2c_node`: Reads raw IMU sensor data from I2C bus (`/dev/i2c-7`).
  * `sllidar_ros2/sllidar_node`: Drives the RPLidar / SLlidar on USB (`/dev/ttyUSB0`).
* **Fusion**:
  * `robot_localization/ekf_node`: Fuses `/wheel/odom` (velocities) and `/imu/data` (orientation/yaw rate) to publish the fused `odom` ➔ `base_footprint` TF, outputting Pose/Twist to `/robot_pose_ekf/odom_combined`.
* **Map Server & Localization**:
  * `nav2_map_server/map_server`: Loads the configured static map from file.
  * `nav2_amcl/amcl`: Runs Adaptive Monte Carlo Localization (AMCL) to dynamically publish the `map` ➔ `odom` transform to correct odometry drift.
* **Nav2 Action Servers**:
  * Runs the standard Nav2 controller, planner, behavior, bt_navigator, and lifecycle manager servers for autonomous path planning.
* **RViz & Helper**:
  * `arjuna_odometry/arjuna_rviz_data_pub`: Resolves user clicks in RViz to coordinate targets.
  * `rviz2`: Launches the visualizer preloaded with `arjuna.rviz` (which contains a persistent red arrow visualization for `Goal Pose` mapped to `/goal_pose`).

### 2. `mapping_launch.py`
Brings up the same sensor driver layer, but switches the localization topology for SLAM:
* **Fusion**: Runs the EKF pose estimator remapped to output directly to the standard `/odom` topic.
* **SLAM**: Runs `slam_toolbox/async_slam_toolbox_node` which consumes LIDAR scans and EKF odometry to map the environment and broadcast the `map ➔ odom` transform.
* **RViz**: Opens RViz loaded with `slam.rviz`.
* **Auto-Save**: Registers an event handler to automatically save the map as a PGM/YAML pair inside the maps folder upon closing RViz.

---

## Instructions to Run

First, compile and source the workspace:
```bash
cd ~/Arjuna_ws
colcon build --packages-select arjuna_main
source install/setup.bash
```

### A. Run Bringup (Navigation & Control)
To run the robot using **Differential Drive** with default ports:
```bash
ros2 launch arjuna_main bringup_launch.py
```
To run the robot using **Mecanum Drive** and specifying custom ports for hardware components (e.g. LIDAR, motor controller, and IMU):
```bash
ros2 launch arjuna_main bringup_launch.py drive_mode:=mecanum serial_port:=/dev/ttyUSB1 motor_port:=/dev/ttyACM1 imu_device:=/dev/i2c-1
```

### B. Send Goals via RViz
1. Start the bringup stack above.
2. In RViz, click the **2D Goal Pose** tool at the top toolbar (or press `g`).
3. Click and drag anywhere on the grid map to select the goal pose and orientation.
4. The standard Nav2 stack will automatically plan a path, avoid obstacles, and drive the robot to the target coordinate.

### C. Run SLAM Mapping
To generate a 2D map of a new environment:
```bash
# Differential drive
ros2 launch arjuna_main mapping_launch.py

# Mecanum drive
ros2 launch arjuna_main mapping_launch.py drive_mode:=mecanum
```
Use a teleoperation node (e.g., keyboard controller from `arjuna_controller`) to drive the robot around.

### D. Saving the Map (Automatic & Manual)

* **Automatic Map Saving (Triggered on RViz exit)**:
  Once mapping is complete, simply **close the RViz window**. An event handler inside the launch script will automatically trigger the `map_saver_cli` to save your map into `arjuna_main/arjuna_main/maps/`.
  * If `my_map` doesn't exist, it will save as `my_map`.
  * If `my_map` exists, it will save as `my_map1`, `my_map2`, etc.

* **Manual Map Saving**:
  If you wish to save it manually to a custom filename without closing RViz, open a new terminal and run:
  ```bash
  ros2 run nav2_map_server map_saver_cli -f ~/Arjuna_ws/src/arjuna_main/arjuna_main/maps/custom_map_name
  ```

---

## Running Console Scripts

All python scripts are installed as console executables in your workspace. You must build and source your workspace (`source install/setup.bash`) before running them.

### 1. Navigation Scripts

Before running these scripts, ensure the bringup stack is active:
```bash
ros2 launch arjuna_main bringup_launch.py
```

* **Single Goal via Terminal (`go_to_point_terminal`)**
  Allows entering target coordinates (X, Y) directly into the terminal window. These coordinates are sent as an Action Goal to the Nav2 action server.
  ```bash
  ros2 run arjuna_main go_to_point_terminal
  ```

* **Interactive Terminal Goals (`arjuna_terminal_goal`)**
  An interactive console menu that allows choosing between:
  1. **Relative Coordinates** (moves relative to the robot's current pose in `base_footprint` frame, e.g. 1m forward).
  2. **Absolute Map Coordinates** (moves to points in the `map` frame; queries and displays the robot's current map coordinates via TF beforehand).
  Provides live throttled feedback (distance remaining, recovery behaviors) and clean shut down handling.
  ```bash
  ros2 run arjuna_main arjuna_terminal_goal
  ```

* **Multi-Point Waypoints via Terminal (`multi_point_terminal`)**
  Collects multiple coordinates from terminal input (e.g. `1.5, 2.0`), then sends them sequentially as Action Goals to the Nav2 stack once you type `done`.
  ```bash
  ros2 run arjuna_main multi_point_terminal
  ```

* **Autonomous Obstacle Avoidance (`obstacle_avoidance`)**
  Drives the robot with autonomous reactive obstacle avoidance based on laser scan sectors (with 180° mounting orientation adjustment and minimum-range filtering to ignore reflections).
  ```bash
  ros2 run arjuna_main obstacle_avoidance
  ```

### 2. OpenCV & Vision Scripts

These scripts handle camera feed streaming, QR code recognition, tracking, and centering. They support both standard USB cameras and DepthAI OAK-D cameras with automated discovery.

* **Camera Publisher (`camera_pub`)**
  Captures video frames from the camera (auto-discovers DepthAI/OAK-D devices and falls back to standard USB cameras) and publishes them on the `/arjuna/camera/image_raw/compressed` topic.
  ```bash
  ros2 run arjuna_main camera_pub
  ```

* **Camera Subscriber (`camera_sub`)**
  Subscribes to `/arjuna/camera/image_raw/compressed` and displays the live frame in an OpenCV window.
  ```bash
  ros2 run arjuna_main camera_sub
  ```

* **QR Code Recognition (`QR_Recog`)**
  Scans camera frames for QR codes, parses their payload data, and prints diagnostics.
  ```bash
  ros2 run arjuna_main QR_Recog
  ```

* **QR Code Tracking (`QR_Tracking`)**
  Uses visual feedback from detected QR codes (case-insensitive and whitespace-stripped matching for "Arjuna") to publish tracking commands (`left`, `center`, `right`, `stop`) to `/arjuna/qr_tracking/command`.
  ```bash
  ros2 run arjuna_main QR_Tracking
  ```

* **QR Centering (`QR_CT`)**
  Subscribes to `/arjuna/qr_tracking/command` and commands robot rotation/translation to center detected QR codes in the camera frame, utilizing LIDAR distance checks for collision avoidance.
  ```bash
  ros2 run arjuna_main QR_CT
  ```

### 3. Sensor & I2C Scripts

* **I2C Ultrasonic Sensors & Light Controller (`data_code`)**
  Communicates over I2C (Bus 7, Address `0x08`) to read dual ultrasonic sensors and pin A1 analog voltage while providing terminal keypress light control.
  ```bash
  ros2 run arjuna_main data_code
  ```
  - **Topics Published**:
    - `/ultrasonic/sensor1/range` & `/ultrasonic/sensor2/range` (`sensor_msgs/msg/Range`)
    - `/ultrasonic/sensor1/distance_cm` & `/ultrasonic/sensor2/distance_cm` (`std_msgs/msg/Float32`)
    - `/analog/voltage` (`std_msgs/msg/Float32`)
    - `/light_status` (`std_msgs/msg/Bool`)
  - **Controls**:
    - Press **`t`** or **`T`** in terminal to toggle the MOSFET light ON/OFF.
    - Publish to `/toggle_light` (`std_msgs/msg/Bool`) for topic-based light control.
