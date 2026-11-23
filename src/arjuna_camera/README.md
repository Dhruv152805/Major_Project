# arjuna_camera

ROS 2 package for OAK-D Spatial AI Stereo Camera driving real-time 3D spatial object detection, aligned stereo depth maps, distance measurements, and 3D semantic mapping in RViz.

## Maintainer
* **Maintainer**: Newrro Tech (Tushar S)
* **Email**: [info@newrro.in](mailto:info@newrro.in)

---

## Key Features & Architecture

* **DepthAI v3 & v2 Compatibility**: Seamlessly runs on modern DepthAI v3 (`dai.node.Camera`, `dai.node.NeuralNetwork`) with runtime backward compatibility for v2.
* **Pure Python ROS Image Bridge**: Direct buffer-to-message serialization (`cv_image.tobytes()`), eliminating `cv_bridge` / `NumPy 2.x` binary ABI incompatibility.
* **On-Device AI Perception**: Runs OpenVINO MobileNet-SSD directly on the Myriad X VPU with real-time tensor decoding.
* **3D Spatial Depth Projection**: Combines 2D bounding boxes with aligned stereo depth and optical intrinsics to calculate $(X, Y, Z)$ positions in meters.
* **3D Semantic Mapping**: Publishes `/semantic_map` (`visualization_msgs/MarkerArray`) with 3D bounding cubes and floating text labels for RViz.
* **Colorized Depth Map**: `camera/depth/image_colored` with Jet colormap for visualization.
* **Center Distance Stream**: `camera/depth/center_distance` (`std_msgs/Float32`) measuring distance at image center.
* **ROS 2 Query Services**: Query 3D object poses and list all detected objects on demand.

---

## Detectable Object Classes (Pascal VOC)
The onboard model detects 20 object classes:
> `person`, `bottle`, `chair`, `diningtable`, `tvmonitor`, `pottedplant`, `sofa`, `bicycle`, `bird`, `boat`, `bus`, `car`, `cat`, `cow`, `dog`, `horse`, `motorbike`, `sheep`, `train`, `aeroplane`

---

## Published Topics

| Topic | Message Type | Description |
| :--- | :--- | :--- |
| `/camera/color/image_raw` | `sensor_msgs/Image` | Raw RGB camera stream (640x360, BGR8) |
| `/camera/color/image_debug` | `sensor_msgs/Image` | RGB stream with 2D bounding boxes, labels, confidence & distances |
| `/camera/color/camera_info` | `sensor_msgs/CameraInfo` | RGB camera calibration & intrinsics |
| `/camera/depth/image_raw` | `sensor_msgs/Image` | 16-bit raw depth map (16UC1, millimeters) |
| `/camera/depth/image_colored` | `sensor_msgs/Image` | Colorized Jet depth stream for visual debugging |
| `/camera/depth/camera_info` | `sensor_msgs/CameraInfo` | Depth camera calibration & intrinsics |
| `/camera/depth/center_distance` | `std_msgs/Float32` | Distance at image center in meters |
| `/semantic_map` | `visualization_msgs/MarkerArray` | 3D bounding cubes & floating text markers in `camera_optical_frame` |
| `/tf_static` | `tf2_msgs/TFMessage` | Static transforms (`base_link` $\rightarrow$ `camera_link` $\rightarrow$ `camera_optical_frame`) |

---

## ROS 2 Services

### 1. `list_objects` (`arjuna_camera/srv/ListObjects`)
Returns all detected objects currently in the camera's field of view.
```bash
ros2 service call /list_objects arjuna_camera/srv/ListObjects
```

### 2. `get_object_pose` (`arjuna_camera/srv/GetObjectPose`)
Returns the 3D pose (`geometry_msgs/PoseStamped`) and confidence for a specific target class.
```bash
ros2 service call /get_object_pose arjuna_camera/srv/GetObjectPose "{target_label: 'person'}"
```

---

## Quick Start & Usage

### 1. Build the Package
```bash
cd ~/Arjuna_ws
colcon build --packages-select arjuna_camera
source install/setup.bash
```

### 2. Launch the Teaching Node (Terminal 1)
```bash
source install/setup.bash
ros2 launch arjuna_camera teaching.launch.py
```

### 3. Launch RViz Visualization (Terminal 2)
To view the pre-configured layout (3D Semantic Map, 2D Detections Feed, Depth Map, TF):
```bash
source install/setup.bash
rviz2 -d src/arjuna_camera/rviz/teaching.rviz
```

---

## TF Coordinate Frames
* `base_link` $\rightarrow$ `camera_link`: Translation `(0.1, 0.0, 0.2)`
* `camera_link` $\rightarrow$ `camera_optical_frame`: Standard ROS optical frame rotation (`qx=-0.5, qy=0.5, qz=-0.5, qw=0.5`)
