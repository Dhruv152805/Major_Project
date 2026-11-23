#!/usr/bin/env python3
import depthai as dai
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from std_msgs.msg import Float32
from ament_index_python.packages import get_package_share_directory
import os
import cv2
import numpy as np
import math
from geometry_msgs.msg import PoseStamped, Point
from visualization_msgs.msg import Marker, MarkerArray
from arjuna_camera.srv import GetObjectPose, ListObjects

class TeachingNode(Node):
    def __init__(self):
        super().__init__('teaching_node')
        
        # 1. Configuration
        self.target_width = 640
        self.target_height = 360
        self.labels = [
            "background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair",
            "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"
        ]
        
        # Simple list to hold detections from the current frame
        self.current_detections = [] 

        # 2. Publishers
        self.pub_color = self.create_publisher(Image, 'camera/color/image_raw', 10)
        self.pub_depth = self.create_publisher(Image, 'camera/depth/image_raw', 10)
        self.pub_depth_colored = self.create_publisher(Image, 'camera/depth/image_colored', 10)
        self.pub_center_dist = self.create_publisher(Float32, 'camera/depth/center_distance', 10)
        self.pub_debug = self.create_publisher(Image, 'camera/color/image_debug', 10)
        self.pub_info = self.create_publisher(CameraInfo, 'camera/color/camera_info', 10)
        self.pub_depth_info = self.create_publisher(CameraInfo, 'camera/depth/camera_info', 10)
        self.pub_markers = self.create_publisher(MarkerArray, '/semantic_map', 10)

        # 3. Services
        self.srv_get = self.create_service(GetObjectPose, 'get_object_pose', self.get_object_pose_callback)
        self.srv_list = self.create_service(ListObjects, 'list_objects', self.list_objects_callback)

        # 4. DepthAI Pipeline Initialization
        self.pipeline = dai.Pipeline()
        self.device = None
        self.rgb_queue = None
        self.depth_queue = None
        self.det_queue = None
        
        try:
            if hasattr(dai.node, 'XLinkOut'):
                # DepthAI v2 API
                self.setup_pipeline_v2()
                self.device = dai.Device(self.pipeline)
                self.rgb_queue = self.device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
                self.depth_queue = self.device.getOutputQueue(name="depth", maxSize=4, blocking=False)
                self.det_queue = self.device.getOutputQueue(name="det", maxSize=4, blocking=False)
                
                calibData = self.device.readCalibration()
                intrinsics = calibData.getCameraIntrinsics(dai.CameraBoardSocket.CAM_A, self.target_width, self.target_height)
                self.camera_info_msg = self.build_camera_info(self.target_width, self.target_height, intrinsics)
                self.get_logger().info("OAK-D Teacher Mode (v2 API): Initialized.")
            else:
                # DepthAI v3 API
                self.setup_pipeline_v3()
                self.pipeline.start()
                try:
                    calibData = self.pipeline.getCalibrationData()
                    intrinsics = calibData.getCameraIntrinsics(dai.CameraBoardSocket.CAM_A, self.target_width, self.target_height)
                    self.camera_info_msg = self.build_camera_info(self.target_width, self.target_height, intrinsics)
                except Exception:
                    self.camera_info_msg = self.build_camera_info(self.target_width, self.target_height, [[500,0,self.target_width/2],[0,500,self.target_height/2],[0,0,1]])
                self.get_logger().info("OAK-D Teacher Mode (v3 API): Initialized.")
        except Exception as e:
            self.get_logger().error(f"Failed to start camera: {e}")
            return

        self.timer = self.create_timer(0.1, self.timer_callback)

    def cv2_to_imgmsg(self, cv_image, encoding="bgr8", frame_id="camera_optical_frame", stamp=None):
        """Pure-Python converter from OpenCV numpy image to sensor_msgs/Image (avoids cv_bridge numpy C-extension mismatch)."""
        msg = Image()
        if stamp is not None:
            msg.header.stamp = stamp
        msg.header.frame_id = frame_id
        msg.height, msg.width = cv_image.shape[:2]
        msg.encoding = encoding
        msg.is_bigendian = 0
        if encoding in ("bgr8", "rgb8"):
            msg.step = msg.width * 3
        elif encoding == "16UC1":
            msg.step = msg.width * 2
        elif encoding in ("mono8", "8UC1"):
            msg.step = msg.width
        else:
            channels = cv_image.shape[2] if len(cv_image.shape) > 2 else 1
            msg.step = msg.width * (cv_image.dtype.itemsize * channels)
        msg.data = cv_image.tobytes()
        return msg

    def setup_pipeline_v3(self):
        # RGB & Mono cameras
        cam_rgb = self.pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_A)
        cam_left = self.pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_B)
        cam_right = self.pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_C)

        # Stereo Depth
        stereo = self.pipeline.create(dai.node.StereoDepth)
        if hasattr(dai.node.StereoDepth, 'PresetMode'):
            if hasattr(dai.node.StereoDepth.PresetMode, 'DENSITY'):
                stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.DENSITY)
            elif hasattr(dai.node.StereoDepth.PresetMode, 'HIGH_DENSITY'):
                stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
            elif hasattr(dai.node.StereoDepth.PresetMode, 'DEFAULT'):
                stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.DEFAULT)
        stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A)
        stereo.setOutputSize(self.target_width, self.target_height)
        
        cam_left.requestOutput((640, 400), dai.ImgFrame.Type.RAW8).link(stereo.left)
        cam_right.requestOutput((640, 400), dai.ImgFrame.Type.RAW8).link(stereo.right)

        # Outputs
        rgb_out = cam_rgb.requestOutput((self.target_width, self.target_height), dai.ImgFrame.Type.BGR888p, fps=10)
        self.rgb_queue = rgb_out.createOutputQueue(maxSize=4, blocking=False)
        self.depth_queue = stereo.depth.createOutputQueue(maxSize=4, blocking=False)

        # NN: NeuralNetwork
        nn = self.pipeline.create(dai.node.NeuralNetwork)
        pkg_share = get_package_share_directory('arjuna_camera')
        model_path = os.path.join(pkg_share, 'models', 'mobilenet-ssd_openvino_2021.4_6shave.blob')
        if os.path.exists(model_path):
            nn.setBlobPath(model_path)
            nn.input.setBlocking(False)

            nn_rgb_out = cam_rgb.requestOutput((300, 300), dai.ImgFrame.Type.BGR888p)
            nn_rgb_out.link(nn.input)
            self.det_queue = nn.out.createOutputQueue(maxSize=4, blocking=False)
            self.get_logger().info(f"Loaded neural network model: {model_path}")
        else:
            self.get_logger().warn(f"Model file not found at {model_path}")
            self.det_queue = None

    def setup_pipeline_v2(self):
        # RGB
        cam_rgb = self.pipeline.create(dai.node.ColorCamera)
        cam_rgb.setBoardSocket(dai.CameraBoardSocket.CAM_A)
        cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        cam_rgb.setIspScale(1, 3) # 640x360
        cam_rgb.setFps(10)
        cam_rgb.setInterleaved(False)

        # Depth
        mono_left = self.pipeline.create(dai.node.MonoCamera)
        mono_right = self.pipeline.create(dai.node.MonoCamera)
        stereo = self.pipeline.create(dai.node.StereoDepth)
        
        mono_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        mono_left.setBoardSocket(dai.CameraBoardSocket.CAM_B)
        mono_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        mono_right.setBoardSocket(dai.CameraBoardSocket.CAM_C)
        
        stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
        stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A) # Align to RGB
        mono_left.out.link(stereo.left)
        mono_right.out.link(stereo.right)

        # NN 
        spatial_nn = self.pipeline.create(dai.node.MobileNetSpatialDetectionNetwork)
        pkg_share = get_package_share_directory('arjuna_camera')
        model_path = os.path.join(pkg_share, 'models', 'mobilenet-ssd_openvino_2021.4_6shave.blob')
        spatial_nn.setBlobPath(model_path)
        spatial_nn.setConfidenceThreshold(0.3)
        spatial_nn.input.setBlocking(False)
        spatial_nn.setBoundingBoxScaleFactor(0.5)
        
        # Links
        cam_rgb.preview.link(spatial_nn.input)
        stereo.depth.link(spatial_nn.inputDepth)

        # XOut
        xout_rgb = self.pipeline.create(dai.node.XLinkOut)
        xout_rgb.setStreamName("rgb")
        cam_rgb.isp.link(xout_rgb.input)

        xout_depth = self.pipeline.create(dai.node.XLinkOut)
        xout_depth.setStreamName("depth")
        stereo.depth.link(xout_depth.input)

        xout_nn = self.pipeline.create(dai.node.XLinkOut)
        xout_nn.setStreamName("det")
        spatial_nn.out.link(xout_nn.input)

    def parse_detections(self, in_det):
        detections = []
        if in_det is None:
            return detections
        try:
            # Case 1: ImgDetections (DepthAI v2 or parser node)
            if hasattr(in_det, 'detections'):
                for d in in_det.detections:
                    if d.confidence >= 0.25:
                        detections.append({
                            'label_id': int(d.label),
                            'conf': float(d.confidence),
                            'xmin': float(d.xmin),
                            'ymin': float(d.ymin),
                            'xmax': float(d.xmax),
                            'ymax': float(d.ymax)
                        })
                return detections
            
            # Case 2: NNData raw tensor from NeuralNetwork [1, 1, 100, 7]
            raw = np.array(in_det.getFirstLayerFp16()).reshape(-1, 7)
            for row in raw:
                conf = float(row[2])
                label_id = int(row[1])
                if 0.25 <= conf <= 1.0 and 0 < label_id < len(self.labels):
                    xmin = max(0.0, min(1.0, float(row[3])))
                    ymin = max(0.0, min(1.0, float(row[4])))
                    xmax = max(0.0, min(1.0, float(row[5])))
                    ymax = max(0.0, min(1.0, float(row[6])))
                    if (xmax - xmin) > 0.02 and (ymax - ymin) > 0.02:
                        detections.append({
                            'label_id': label_id,
                            'conf': conf,
                            'xmin': xmin,
                            'ymin': ymin,
                            'xmax': xmax,
                            'ymax': ymax
                        })
        except Exception:
            pass
        return detections

    def build_camera_info(self, width, height, intrinsics):
        info = CameraInfo()
        info.width = width
        info.height = height
        info.distortion_model = "plumb_bob"
        info.k = [intrinsics[0][0], intrinsics[0][1], intrinsics[0][2],
                  intrinsics[1][0], intrinsics[1][1], intrinsics[1][2],
                  intrinsics[2][0], intrinsics[2][1], intrinsics[2][2]]
        info.p = [intrinsics[0][0], intrinsics[0][1], intrinsics[0][2], 0.0,
                  intrinsics[1][0], intrinsics[1][1], intrinsics[1][2], 0.0,
                  intrinsics[2][0], intrinsics[2][1], intrinsics[2][2], 0.0]
        info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        return info

    def timer_callback(self):
        in_rgb = self.rgb_queue.tryGet() if self.rgb_queue else None
        in_depth = self.depth_queue.tryGet() if self.depth_queue else None
        in_det = self.det_queue.tryGet() if self.det_queue else None
        
        now = self.get_clock().now().to_msg()
        
        # Clear detections for the new frame
        self.current_detections = []

        depth_frame = None
        if in_depth is not None:
            depth_frame = in_depth.getFrame()
            if depth_frame.shape[1] != self.target_width or depth_frame.shape[0] != self.target_height:
                depth_frame = cv2.resize(depth_frame, (self.target_width, self.target_height), interpolation=cv2.INTER_NEAREST)

        if in_rgb is not None:
            cv_frame = in_rgb.getCvFrame()
            debug_frame = cv_frame.copy()
            h, w = debug_frame.shape[:2]

            # Process Detections
            raw_dets = self.parse_detections(in_det)
            if len(raw_dets) > 0:
                for det in raw_dets:
                    label_id = det['label_id']
                    label = self.labels[label_id] if label_id < len(self.labels) else f"obj_{label_id}"
                    conf = det['conf']
                    
                    x1, y1 = max(0, int(det['xmin'] * w)), max(0, int(det['ymin'] * h))
                    x2, y2 = min(w - 1, int(det['xmax'] * w)), min(h - 1, int(det['ymax'] * h))
                    cx_box = (x1 + x2) // 2
                    cy_box = (y1 + y2) // 2

                    # Compute 3D Coordinates
                    x_m, y_m, z_m = 0.0, 0.0, 0.0
                    if depth_frame is not None:
                        # Direct depth projection from aligned depth frame
                        patch = depth_frame[max(0, cy_box-3):min(h, cy_box+4), max(0, cx_box-3):min(w, cx_box+4)]
                        valid_d = patch[patch > 0]
                        if len(valid_d) > 0:
                            z_m = float(np.median(valid_d)) / 1000.0

                    # Fallback estimated depth if depth sensor returned 0
                    if z_m <= 0.05:
                        z_m = 1.0
                    
                    fx = self.camera_info_msg.k[0] if (self.camera_info_msg and self.camera_info_msg.k[0] > 0) else 500.0
                    fy = self.camera_info_msg.k[4] if (self.camera_info_msg and self.camera_info_msg.k[4] > 0) else 500.0
                    cx_cal = self.camera_info_msg.k[2] if (self.camera_info_msg and self.camera_info_msg.k[2] > 0) else (w / 2.0)
                    cy_cal = self.camera_info_msg.k[5] if (self.camera_info_msg and self.camera_info_msg.k[5] > 0) else (h / 2.0)
                    x_m = (cx_box - cx_cal) * z_m / fx
                    y_m = (cy_box - cy_cal) * z_m / fy

                    # Draw on debug frame
                    cv2.rectangle(debug_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    text = f"{label} {z_m:.2f}m ({conf:.2f})"
                    cv2.putText(debug_frame, text, (x1, max(18, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    # Store as real-time detection
                    self.current_detections.append({
                        'label': label,
                        'conf': conf,
                        'x': x_m,
                        'y': y_m,
                        'z': z_m
                    })

                if len(self.current_detections) > 0:
                    summary = ", ".join([f"{d['label']}({d['conf']:.2f}, {d['z']:.2f}m)" for d in self.current_detections])
                    self.get_logger().info(f"Detections: {summary}", throttle_duration_sec=1.0)

            # Publish Color / Debug
            raw_msg = self.cv2_to_imgmsg(cv_frame, encoding="bgr8")
            raw_msg.header.stamp = now
            raw_msg.header.frame_id = "camera_optical_frame"
            self.pub_color.publish(raw_msg)
            
            debug_msg = self.cv2_to_imgmsg(debug_frame, encoding="bgr8")
            debug_msg.header.stamp = now
            debug_msg.header.frame_id = "camera_optical_frame"
            self.pub_debug.publish(debug_msg)

            self.camera_info_msg.header = raw_msg.header
            self.pub_info.publish(self.camera_info_msg)

        if in_depth is not None and depth_frame is not None:
            msg = self.cv2_to_imgmsg(depth_frame, encoding="16UC1")
            msg.header.stamp = now
            msg.header.frame_id = "camera_optical_frame"
            self.pub_depth.publish(msg)
            
            self.camera_info_msg.header = msg.header
            self.pub_depth_info.publish(self.camera_info_msg)

            # 1. Calculate center point distance (3x3 average)
            h_d, w_d = depth_frame.shape
            cx, cy = w_d // 2, h_d // 2
            center_region = depth_frame[cy-1:cy+2, cx-1:cx+2]
            valid = center_region[center_region > 0]
            if len(valid) > 0:
                dist_m = float(np.mean(valid)) / 1000.0
                dist_msg = Float32()
                dist_msg.data = dist_m
                self.pub_center_dist.publish(dist_msg)

            # 2. Colored depth map for RViz / Debugging
            depth_vis = cv2.normalize(depth_frame, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            depth_colored = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)
            
            # Mask out invalid depths (0) so they appear pure black
            depth_colored[depth_frame == 0] = [0, 0, 0]
            
            colored_msg = self.cv2_to_imgmsg(depth_colored, encoding="bgr8")
            colored_msg.header = msg.header
            self.pub_depth_colored.publish(colored_msg)

        # Publish 3D Markers to RViz (/semantic_map)
        self.publish_semantic_map(now)

    def publish_semantic_map(self, stamp):
        """Publishes 3D bounding cubes and floating text labels for all current detections."""
        marker_array = MarkerArray()
        
        # Always send a delete-all marker first so lost objects disappear immediately
        del_marker = Marker()
        del_marker.action = Marker.DELETEALL
        marker_array.markers.append(del_marker)

        for i, det in enumerate(self.current_detections):
            # 1. Cube Marker
            box_marker = Marker()
            box_marker.header.frame_id = "camera_optical_frame"
            box_marker.header.stamp = stamp
            box_marker.ns = "detections_3d"
            box_marker.id = i * 2
            box_marker.type = Marker.CUBE
            box_marker.action = Marker.ADD
            box_marker.pose.position.x = det['x']
            box_marker.pose.position.y = det['y']
            box_marker.pose.position.z = det['z']
            box_marker.pose.orientation.w = 1.0
            
            # Approximate object volume (0.15m x 0.15m x 0.15m)
            box_marker.scale.x = 0.15
            box_marker.scale.y = 0.15
            box_marker.scale.z = 0.15
            
            # Translucent Cyan
            box_marker.color.r = 0.0
            box_marker.color.g = 1.0
            box_marker.color.b = 1.0
            box_marker.color.a = 0.5
            marker_array.markers.append(box_marker)

            # 2. Text Label Marker
            text_marker = Marker()
            text_marker.header.frame_id = "camera_optical_frame"
            text_marker.header.stamp = stamp
            text_marker.ns = "detections_text"
            text_marker.id = i * 2 + 1
            text_marker.type = Marker.TEXT_VIEW_FACING
            text_marker.action = Marker.ADD
            text_marker.pose.position.x = det['x']
            text_marker.pose.position.y = det['y'] - 0.12 # Float slightly above the cube
            text_marker.pose.position.z = det['z']
            text_marker.pose.orientation.w = 1.0
            text_marker.scale.z = 0.08 # Text height in meters
            text_marker.text = f"{det['label']} ({det['z']:.2f}m)"
            
            # Solid White Text
            text_marker.color.r = 1.0
            text_marker.color.g = 1.0
            text_marker.color.b = 1.0
            text_marker.color.a = 1.0
            marker_array.markers.append(text_marker)

        self.pub_markers.publish(marker_array)

    def get_object_pose_callback(self, request, response):
        """Find the most confident visible object matching the requested label."""
        target = request.label.lower()
        candidates = [d for d in self.current_detections if d['label'].lower() == target]
        
        if candidates:
            # Pick highest confidence
            best = max(candidates, key=lambda x: x['conf'])
            response.success = True
            response.message = f"Found {best['label']} at depth {best['z']:.2f}m (Confidence: {best['conf']:.2f})"
            response.pose.header.frame_id = "camera_optical_frame"
            response.pose.header.stamp = self.get_clock().now().to_msg()
            response.pose.pose.position.x = best['x']
            response.pose.pose.position.y = best['y']
            response.pose.pose.position.z = best['z']
            response.pose.pose.orientation.w = 1.0
            return response
        
        response.success = False
        response.message = f"Object '{request.label}' not currently visible."
        return response

    def list_objects_callback(self, request, response):
        """List everything the camera has detected in the CURRENT frame."""
        response.labels = []
        response.poses = []
        for det in self.current_detections:
            response.labels.append(det['label'])
            p = PoseStamped()
            p.header.frame_id = "camera_optical_frame"
            p.header.stamp = self.get_clock().now().to_msg()
            p.pose.position.x = det['x']
            p.pose.position.y = det['y']
            p.pose.position.z = det['z']
            p.pose.orientation.w = 1.0
            response.poses.append(p)
        response.success = True
        return response

def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = TeachingNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        if node is not None:
            if hasattr(node, 'pipeline') and node.pipeline is not None:
                try:
                    node.pipeline.stop()
                except Exception:
                    pass
            if hasattr(node, 'device') and node.device is not None:
                try:
                    node.device.close()
                except Exception:
                    pass
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
