# Arjuna Odometry ROS 2 Package

Fuses physical wheel encoder data and converts visualization interface actions for the **Arjuna** robot.

---

## Maintainer
* **Maintainer**: Newrro Tech (Tushar S)
* **Email**: [info@newrro.in](mailto:info@newrro.in)

---

## Nodes Overview

### 1. `arjuna_ekf_odom_pub`
Fuses Left/Right motor encoder ticks to compute and publish wheel odometry (displacement and velocity). It is optimized to serve as the main wheel odometry input for the Robot Localization EKF node.

* **Subscribed Topics**:
  - `left_ticks` (`std_msgs/msg/Int64`): Cumulative encoder ticks of the Left motor wheels (ticks scaled from Front Left motor).
  - `right_ticks` (`std_msgs/msg/Int64`): Cumulative encoder ticks of the Right motor wheels (ticks scaled from Front Right motor).
  - `initial_2d` (`geometry_msgs/msg/PoseStamped`): Resets internal position tracking to a specified coordinate.
* **Published Topics**:
  - `odom` (`nav_msgs/msg/Odometry`): Estimated robot pose and velocity, equipped with default covariance matrices.
  - `odom_data_quat` (`nav_msgs/msg/Odometry`): Duplicate odometry stream with orientation encoded as quaternions.
  - `odom_data_euler` (`nav_msgs/msg/Odometry`): Duplicate odometry stream with yaw angle exported directly in the orientation structure for debugging.
* **Parameters**:
  - `publish_tf` (bool, default: `false`): Broadcasts the `odom` ➔ `base_footprint` transform. Typically set to `false` when using an EKF fusion node (`robot_localization`) to avoid transform authority conflicts.
  - `wheel_radius` (double, default: `0.04`): Wheel radius in meters (80 mm diameter).
  - `wheel_base` (double, default: `0.30`): Distance between wheels (track width) in meters.
  - `ticks_per_revolution` (double, default: `4096.0`): STS 12-bit encoder resolution.
  - `tick_scaling` (double, default: `2.5`): Motor node scaling factor.
  - `publish_rate` (double, default: `30.0`): Publishing frequency of the odometry stream (Hz).

---

### 2. `arjuna_rviz_data_pub`
Converts 3D RViz user interface clicks (goal pose and initial pose) into custom 2D formats (Euler angles / RPY) to maintain compatibility with legacy control scripts.

* **Subscribed Topics**:
  - `/move_base_simple/goal` (`geometry_msgs/msg/PoseStamped`): Triggered by the 2D Nav Goal button in standard RViz setups.
  - `/initialpose` (`geometry_msgs/msg/PoseWithCovarianceStamped`): Triggered by the 2D Pose Estimate tool in RViz.
* **Published Topics**:
  - `goal_2d` (`geometry_msgs/msg/PoseStamped`): Custom 2D pose where yaw orientation is packed into the orientation `z` field.
  - `initial_2d` (`geometry_msgs/msg/PoseStamped`): Custom 2D initial pose where yaw orientation is packed into the orientation `z` field.

---

## How to Build and Run

### 1. Build the Package
From the root of your workspace:
```bash
cd ~/Arjuna_ws
colcon build --packages-select arjuna_odometry
source install/setup.bash
```

### 2. Run the Nodes
* **Run Wheel Odometry Publisher**:
  ```bash
  ros2 run arjuna_odometry arjuna_ekf_odom_pub
  ```
  *(Typically launched automatically via `bringup_launch.py` or `mapping_launch.py`)*

* **Run RViz Conversion Helper**:
  ```bash
  ros2 run arjuna_odometry arjuna_rviz_data_pub
  ```
