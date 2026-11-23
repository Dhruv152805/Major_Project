# Arjuna Motor Controller ROS 2 Package

A unified, high-performance, and safety-critical ROS 2 motor control package for the **Arjuna** robot. This package uses the `stservo_sdk` library to communicate over serial with SCS-series smart servo motors, supporting both **differential drive (rubber wheels)** and **mecanum drive** configurations.

---

## Maintainer
* **Maintainer**: Newrro Tech (Tushar S)
* **Email**: [info@newrro.in](mailto:info@newrro.in)

---

## Features
- **Kinematic Versatility**: Toggle dynamically or via parameters between differential and mecanum drive kinematics.
- **Robust Communication**: Uses `GroupSyncWrite` for simultaneous velocity updates and `GroupSyncRead` for synchronized encoder feedback.
- **Safety Heartbeat**: Automatically stops the motors if no `cmd_vel` command is received for over 2.0 seconds.
- **Emergency Broadcast Stop**: Transmits a broadcast speed stop (ID 254) to all motors immediately upon node shutdown.
- **Live Parameter Updates**: Supports runtime dynamic updates of parameters (e.g. toggling drive mode on-the-fly).

---

## Topics and Message Types

### Subscribed Topics
- **`/cmd_vel`** (`geometry_msgs/msg/Twist`)
  - Subscribes to linear and angular velocity commands to drive the robot.
  - Logs incoming velocities (throttled to 1.0 Hz) to confirm connection.
- **`/drive_mode`** (`std_msgs/msg/String`)
  - Subscribes to runtime drive mode toggles (`differential` or `mecanum`).

### Published Topics
- **`/left_ticks`** (`std_msgs/msg/Int64`)
  - Cumulative encoder ticks for the left side of the robot (derived from Front Left Motor ID 1).
- **`/right_ticks`** (`std_msgs/msg/Int64`)
  - Cumulative encoder ticks for the right side of the robot (derived from Front Right Motor ID 2).

---

## Configurable Launch Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `port` | String | `/dev/ttyACM0` | Serial port connected to the motor driver board. |
| `baudrate` | Integer | `1000000` | Communication baudrate (1 Mbps). |
| `wheel_sep` | Double | `0.30` | Distance between left and right wheels (m). |
| `wheel_base` | Double | `0.30` | Axle separation distance for mecanum drive (m). |
| `drive_mode` | String | `differential` | Robot kinematics configuration (`differential` or `mecanum`). |
| `speed_scaling`| Integer | `10000` | Speed command multiplier mapping m/s to motor units. |
| `tick_scaling` | Double | `2.5` | Divisor scaling factor for raw encoder tick outputs. |
| `invert_y` | Boolean| `false` | Inverts lateral (strafe) velocity in mecanum mode. |

---

## Kinematics Reference
### 1. Differential Drive Mode (`FL = RL = Left`, `FR = RR = Right`)
- **Formula**:
  - $\text{Right Velocity} = \frac{2 \cdot v_x + \omega_z \cdot L}{2}$
  - $\text{Left Velocity} = \frac{2 \cdot v_x - \omega_z \cdot L}{2}$
- **Motor Directions**:
  - Left motors (ID 1, ID 4) are inverted/negated (`-Left_velocity`).
  - Right motors (ID 2, ID 3) are positive (`Right_velocity`).

### 2. Mecanum Drive Mode
- **Formula**:
  - $\text{Front Left (FL)} = v_x - v_y - \omega_z \cdot L_{sum}$
  - $\text{Front Right (FR)} = v_x + v_y + \omega_z \cdot L_{sum}$
  - $\text{Rear Left (RL)} = v_x + v_y - \omega_z \cdot L_{sum}$
  - $\text{Rear Right (RR)} = v_x - v_y + \omega_z \cdot L_{sum}$
- **Motor Directions**:
  - Left side motors (ID 1, ID 4) are negated.
  - Right side motors (ID 2, ID 3) are positive.

---

## How to Build and Run

### 1. Build the Package
Navigate to your ROS 2 workspace and compile the package:
```bash
cd ~/Arjuna_ws
colcon build --packages-select motor_controller
source install/setup.bash
```

### 2. Run with Launch File (Examples)

* **Run in default configuration (differential mode, 1M baud, `/dev/ttyACM0`):**
  ```bash
  ros2 launch motor_controller motor_controller_launch.py
  ```

* **Run in mecanum drive mode:**
  ```bash
  ros2 launch motor_controller motor_controller_launch.py drive_mode:=mecanum
  ```

* **Run on a different serial port (e.g. `/dev/ttyUSB0`):**
  ```bash
  ros2 launch motor_controller motor_controller_launch.py port:=/dev/ttyUSB0
  ```

* **Run at a different baudrate (e.g. 115200):**
  ```bash
  ros2 launch motor_controller motor_controller_launch.py baudrate:=115200
  ```

* **Combined customized launch:**
  ```bash
  ros2 launch motor_controller motor_controller_launch.py drive_mode:=mecanum port:=/dev/ttyACM0 baudrate:=1000000
  ```

---

## Dynamic Toggling (At Runtime)

You can toggle the drive mode or configure parameters **on-the-fly** while the node is running:

- **Switch to Mecanum Mode:**
  ```bash
  ros2 param set /motor_driver drive_mode mecanum
  ```
- **Switch to Differential Mode:**
  ```bash
  ros2 param set /motor_driver drive_mode differential
  ```
