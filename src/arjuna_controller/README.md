# Arjuna Controller ROS 2 Package

An interactive, keyboard-teleoperation controller package for the **Arjuna** autonomous robot. It allows stateful, real-time control of the robot in both **differential drive** and **mecanum drive** configurations, publishing velocity commands to `/cmd_vel` and drive mode strings to `/drive_mode`.

---

## Maintainer
* **Maintainer**: Newrro Tech (Tushar S)
* **Email**: [info@newrro.in](mailto:info@newrro.in)

---

## Features
- **Dual-Mode Teleoperation**: Seamlessly switch between differential and mecanum drive control bindings on-the-fly.
- **Stateful Control**: The robot maintains the last commanded velocity until a new command or stop command is received.
- **Speed Adjustment**: Increase or decrease linear/angular velocity scaling dynamically by 10% increments.
- **Safety Emergency Stop**: Instant zero-velocity broadcast on SPACE key press.

---

## Usage

### 1. Build the Package
From the root of your workspace:
```bash
cd ~/Arjuna_ws
colcon build --packages-select arjuna_controller
source install/setup.bash
```

### 2. Run the Teleoperation Node
Ensure the motor driver and bringup stack is active, then run:
```bash
ros2 run arjuna_controller Arjuna_Controller
```

---

## Keyboard Control Bindings

### Global Commands
* **`SPACE`**: Emergency Stop (sets all linear/angular velocities to 0.0).
* **`t`**: Toggle drive mode between `differential` and `mecanum`.
* **`i` / `k`**: Increase / Decrease linear speed by 10%.
* **`j` / `l`**: Increase / Decrease angular speed by 10%.
* **`CTRL-C`**: Stop the robot and safely exit the teleoperation node.

### Differential Drive Mode Bindings
* **`↑` (Up Arrow)**: Drive straight forward.
* **`↓` (Down Arrow)**: Drive straight backward.
* **`←` (Left Arrow)**: Turn left in place.
* **`→` (Right Arrow)**: Turn right in place.
* **`u`**: Forward left arc.
* **`o`**: Forward right arc.
* **`m`**: Backward left arc.
* **`.`**: Backward right arc.

### Mecanum Drive Mode Bindings
* **`w`**: Translate forward.
* **`s`**: Translate backward.
* **`a`**: Strafe left.
* **`d`**: Strafe right.
* **`q`**: Strafe diagonally forward-left.
* **`e`**: Strafe diagonally forward-right.
* **`z`**: Strafe diagonally backward-left.
* **`c`**: Strafe diagonally backward-right.
* **`x`**: Rotate in place (angular speed determined by `j`/`l` settings).

---

## Published Topics
- **`/cmd_vel`** (`geometry_msgs/msg/Twist`)
  - Velocity commands scaled by speed/turn limits.
- **`/drive_mode`** (`std_msgs/msg/String`)
  - Publishes active drive mode (`differential` or `mecanum`) when changed.
