#!/usr/bin/env python3
"""
Arjuna QR Tracking Node (Direct Camera Capture)
==============================================
Processes live video streams to detect a target QR code containing "Arjuna" (case-insensitive)
and publishes tracking steering commands ('left', 'center', 'right', 'stop') to center the robot.

-----------------------------------------------------------------------------------------
ARCHITECTURE & CONTROL FLOW:
1. Dynamic Camera Discovery:
   - Supports both standard USB UVC cameras (using OpenCV VideoCapture) and DepthAI OAK-D cameras.
   - Automatically probes for DepthAI hardware. If available, initializes a pipeline for
     the OAK-D RGB sensor; otherwise, falls back to a standard video device (e.g. '/dev/video0').
2. Multi-Threaded Execution (Low-Latency pipeline):
   - Capture Thread: Pulls frames continuously from the device and enqueues them.
   - Processing: Main node logic reads frames, flips horizontally (to correct mirroring),
     converts to grayscale, and runs QR detection.
   - Display Thread: Runs in parallel to show the OpenCV GUI window, rendering bounding boxes
     and active zone overlay lines without blocking the ROS executor.
3. Dual-Backend QR Detection:
   - Primary: Uses pyzbar (decodes multiple QR codes, robust orientation handling).
   - Fallback: OpenCV QRCodeDetector (if pyzbar is not installed or fails).
4. Zone Partitioning:
   - Divides the camera frame horizontal resolution into zones:
     * Left Zone (0% - 40%): Triggers 'left' command to rotate left.
     * Center Zone (40% - 60%): Triggers 'center' command to drive straight forward.
     * Right Zone (60% - 100%): Triggers 'right' command to rotate right.
     * No QR detected: Triggers 'stop'.
   - Commands are published on '/arjuna/qr_tracking/command'.

Company: NEWRRO TECH LLP
Website: www.newrro.in
-----------------------------------------------------------------------------------------
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import cv2
import numpy as np
from pyzbar import pyzbar
import threading
from queue import Queue
import time

# Check DepthAI library availability
try:
    import depthai as dai
    HAS_DEPTHAI = True
except ImportError:
    HAS_DEPTHAI = False

# Constants
WINDOW_NAME = "Arjuna QR Tracking"
TARGET_QR_TEXT = "Arjuna"  # Target payload (case insensitive)
ZONE_LEFT_PERCENT = 40     # Left boundary (0% - 40%)
ZONE_CENTER_PERCENT = 20   # Center alignment corridor (40% - 60%)
ZONE_RIGHT_PERCENT = 40    # Right boundary (60% - 100%)

# Drawing Colors (BGR format)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_BLUE = (255, 0, 0)
COLOR_YELLOW = (0, 255, 255)
COLOR_WHITE = (255, 255, 255)

class QRTracker(Node):
    def __init__(self):
        super().__init__('arjuna_qr_tracker')
        
        # Declare parameters
        self.declare_parameter('flip_horizontal', True)
        self.flip_horizontal = self.get_parameter('flip_horizontal').value
        
        self.declare_parameter('camera_type', 'auto')  # Options: 'auto', 'oak', 'usb'
        self.declare_parameter('camera_device', '/dev/video0')
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)
        self.declare_parameter('fps', 30)

        # Retrieve parameters
        camera_type = self.get_parameter('camera_type').value
        camera_device_param = self.get_parameter('camera_device').value
        try:
            camera_device = int(camera_device_param)
        except ValueError:
            camera_device = camera_device_param

        frame_width = self.get_parameter('frame_width').value
        frame_height = self.get_parameter('frame_height').value
        fps = self.get_parameter('fps').value
        
        # State variables
        self.current_frame = None
        self.qr_detected = False
        self.qr_zone = None
        self.qr_data = None
        self.qr_bbox = None
        
        # Diagnostic statistics
        self.frame_count = 0
        self.qr_count = 0
        self.start_time = time.time()
        
        # Frame queue to transfer images between capture and processing
        self.frame_queue = Queue(maxsize=2)
        
        # Fallback OpenCV detector initialization
        self.detector = cv2.QRCodeDetector()
        
        # Publisher for visual steering command
        self.qr_cmd_pub = self.create_publisher(
            String,
            '/arjuna/qr_tracking/command',
            10)

        # Device handlers
        self.cap = None
        self.dai_device = None
        self.pipeline = None
        self.dai_queue = None
        self.is_depthai = False

        # Detect OAK-D camera availability
        has_oak = False
        if HAS_DEPTHAI:
            try:
                device_infos = dai.Device.getAllAvailableDevices()
                if len(device_infos) > 0:
                    has_oak = True
            except Exception as e:
                self.get_logger().warn(f"Failed to query DepthAI devices: {e}")

        # Choose camera mode based on parameter and availability
        if camera_type == 'oak' or (camera_type == 'auto' and has_oak):
            self.get_logger().info("Initializing OAK-D / DepthAI Camera...")
            try:
                if hasattr(dai.node, 'Camera'):
                    # DepthAI v3 API
                    self.pipeline = dai.Pipeline()
                    try:
                        cam = self.pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_A)
                    except Exception:
                        cam = self.pipeline.create(dai.node.Camera).build()
                    
                    frame_type = getattr(dai.ImgFrame.Type, 'BGR888p', None)
                    if frame_type is not None:
                        video_output = cam.requestOutput(size=(frame_width, frame_height), type=frame_type, fps=fps)
                    else:
                        video_output = cam.requestOutput(size=(frame_width, frame_height), fps=fps)
                    
                    self.dai_queue = video_output.createOutputQueue(maxSize=4, blocking=False)
                    self.pipeline.start()
                    self.is_depthai = True
                    self.get_logger().info("✓ DepthAI Camera (v3 API) initialized successfully.")
                elif hasattr(dai.node, 'ColorCamera') and hasattr(dai.node, 'XLinkOut'):
                    # DepthAI v2 API
                    self.pipeline = dai.Pipeline()
                    cam_rgb = self.pipeline.create(dai.node.ColorCamera)
                    cam_rgb.setPreviewSize(frame_width, frame_height)
                    cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
                    cam_rgb.setInterleaved(False)
                    cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
                    cam_rgb.setFps(fps)

                    xout_rgb = self.pipeline.create(dai.node.XLinkOut)
                    xout_rgb.setStreamName("rgb")
                    cam_rgb.preview.link(xout_rgb.input)

                    self.dai_device = dai.Device(self.pipeline)
                    self.dai_queue = self.dai_device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
                    self.is_depthai = True
                    self.get_logger().info("✓ DepthAI Camera (v2 API) initialized successfully.")
                else:
                    raise RuntimeError("Incompatible DepthAI API: No Camera or ColorCamera/XLinkOut found")
            except Exception as e:
                self.get_logger().error(f"Failed to initialize DepthAI camera: {e}")
                if camera_type == 'oak':
                    raise RuntimeError("OAK camera initialization failed")
                else:
                    self.get_logger().info("Falling back to Standard USB Camera...")

        if not self.is_depthai:
            self.get_logger().info(f"Initializing Standard USB Camera ({camera_device})...")
            self.cap = cv2.VideoCapture(camera_device)
            if not self.cap.isOpened():
                self.get_logger().error(f"Failed to open standard camera device: {camera_device}")
                raise RuntimeError("Camera init failed")
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
            self.cap.set(cv2.CAP_PROP_FPS, fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.get_logger().info("✓ Standard USB Camera initialized successfully.")

        # Start capture thread
        self.is_capturing = True
        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.capture_thread.start()
        
        # Start display thread
        self.is_displaying = True
        self.display_thread = threading.Thread(target=self.display_loop, daemon=True)
        self.display_thread.start()
        
        # Stats logging timer (every 5 seconds)
        self.stats_timer = self.create_timer(5.0, self.print_stats)
        
        self.get_logger().info("")
        self.get_logger().info("=" * 60)
        self.get_logger().info("ARJUNA QR TRACKING - ACTIVE")
        self.get_logger().info("=" * 60)
        self.get_logger().info(f"Target QR: '{TARGET_QR_TEXT}' (case insensitive)")
        self.get_logger().info(f"Zones: LEFT {ZONE_LEFT_PERCENT}% | CENTER {ZONE_CENTER_PERCENT}% | RIGHT {ZONE_RIGHT_PERCENT}%")
        self.get_logger().info(f"Mode: {'DepthAI (OAK)' if self.is_depthai else 'Standard USB (UVC)'}")
        self.get_logger().info("Publishes: /arjuna/qr_tracking/command")
        self.get_logger().info("=" * 60)
        self.get_logger().info("Window: Green box = centered | Red box = need alignment")
        self.get_logger().info("Press Q or ESC to quit")
        self.get_logger().info("=" * 60)
        self.get_logger().info("")

    def capture_loop(self):
        """Continuous background capture thread."""
        if self.is_depthai:
            while self.is_capturing:
                try:
                    in_rgb = self.dai_queue.get()
                    if in_rgb is not None:
                        frame = in_rgb.getCvFrame()
                        self.process_incoming_frame(frame)
                except Exception as e:
                    self.get_logger().warn(f"DepthAI capture error: {e}")
                    time.sleep(0.01)
        else:
            while self.is_capturing:
                ret, frame = self.cap.read()
                if not ret:
                    self.get_logger().warn("Failed to capture standard camera frame")
                    time.sleep(0.01)
                    continue
                self.process_incoming_frame(frame)

    def process_incoming_frame(self, frame):
        """Applies pre-processing flips and passes frame to tracking."""
        try:
            if frame is None:
                return
            
            # Flip horizontally to fix mirroring
            if self.flip_horizontal:
                frame = cv2.flip(frame, 1)
            
            self.frame_count += 1
            self.process_frame(frame)
            
        except Exception as e:
            self.get_logger().error(f"Frame processing error: {e}")
    
    def process_frame(self, frame):
        """
        Grayscales the frame, runs pyzbar / OpenCV detection, evaluates
        the center coordinates against zone boundaries, and publishes commands.
        """
        height, width = frame.shape[:2]
        
        # Calculate zone boundaries based on percentages
        left_boundary = int(width * ZONE_LEFT_PERCENT / 100)
        right_boundary = int(width * (ZONE_LEFT_PERCENT + ZONE_CENTER_PERCENT) / 100)
        
        # Draw visual zone partition lines on HUD
        cv2.line(frame, (left_boundary, 0), (left_boundary, height), COLOR_YELLOW, 2)
        cv2.line(frame, (right_boundary, 0), (right_boundary, height), COLOR_YELLOW, 2)
        
        # Zone labels
        cv2.putText(frame, "LEFT", (int(left_boundary/2) - 30, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_YELLOW, 2)
        cv2.putText(frame, "CENTER", (left_boundary + int((right_boundary - left_boundary)/2) - 40, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_YELLOW, 2)
        cv2.putText(frame, "RIGHT", (right_boundary + int((width - right_boundary)/2) - 35, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_YELLOW, 2)
        
        # Grayscale conversion for robust decoding
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 1. Primary Decode Attempt using pyzbar
        qr_codes = pyzbar.decode(gray)
        
        self.qr_detected = False
        self.qr_zone = None
        command = "stop"
        found_target = False
        
        for qr in qr_codes:
            qr_data = qr.data.decode('utf-8').strip()
            
            # Match target text
            if TARGET_QR_TEXT.lower() in qr_data.lower():
                self.qr_detected = True
                self.qr_data = qr_data
                self.qr_count += 1
                found_target = True
                
                points = qr.polygon
                if len(points) == 4:
                    # Calculate center coordinates of the QR bounding box
                    qr_center_x = int(sum([p.x for p in points]) / 4)
                    qr_center_y = int(sum([p.y for p in points]) / 4)
                    
                    # Evaluate steering zone
                    if qr_center_x < left_boundary:
                        self.qr_zone = "left"
                        box_color = COLOR_RED
                        command = "left"
                    elif qr_center_x < right_boundary:
                        self.qr_zone = "center"
                        box_color = COLOR_GREEN
                        command = "center"
                    else:
                        self.qr_zone = "right"
                        box_color = COLOR_RED
                        command = "right"
                    
                    # Draw visual target boundaries
                    pts = np.array([[p.x, p.y] for p in points], np.int32)
                    pts = pts.reshape((-1, 1, 2))
                    cv2.polylines(frame, [pts], True, box_color, 3)
                    cv2.circle(frame, (qr_center_x, qr_center_y), 5, box_color, -1)
                    
                    # Text overlays
                    text_y = qr_center_y - 20
                    cv2.putText(frame, f"QR: {qr_data}", 
                               (qr_center_x - 50, text_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
                    cv2.putText(frame, f"Zone: {self.qr_zone.upper()}", 
                               (qr_center_x - 50, text_y + 25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
                    break
        
        # 2. Fallback Decode Attempt using OpenCV QRCodeDetector
        if not found_target:
            try:
                text, pts, _ = self.detector.detectAndDecode(gray)
                if text:
                    qr_data = text.strip()
                    if TARGET_QR_TEXT.lower() in qr_data.lower():
                        self.qr_detected = True
                        self.qr_data = qr_data
                        self.qr_count += 1
                        found_target = True
                        
                        if pts is not None and len(pts) > 0:
                            pts = pts.astype(int).reshape((-1, 2))
                            qr_center_x = int(sum([p[0] for p in pts]) / 4)
                            qr_center_y = int(sum([p[1] for p in pts]) / 4)
                            
                            if qr_center_x < left_boundary:
                                self.qr_zone = "left"
                                box_color = COLOR_RED
                                command = "left"
                            elif qr_center_x < right_boundary:
                                self.qr_zone = "center"
                                box_color = COLOR_GREEN
                                command = "center"
                            else:
                                self.qr_zone = "right"
                                box_color = COLOR_RED
                                command = "right"
                            
                            pts_draw = pts.reshape((-1, 1, 2))
                            cv2.polylines(frame, [pts_draw], True, box_color, 3)
                            cv2.circle(frame, (qr_center_x, qr_center_y), 5, box_color, -1)
                            
                            text_y = qr_center_y - 20
                            cv2.putText(frame, f"QR: {qr_data} (CV2)", 
                                       (qr_center_x - 50, text_y),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
                            cv2.putText(frame, f"Zone: {self.qr_zone.upper()}", 
                                       (qr_center_x - 50, text_y + 25),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
            except Exception as e:
                self.get_logger().warn(f"OpenCV detectAndDecode exception: {e}")
        
        # Publish command topic
        cmd_msg = String()
        cmd_msg.data = command
        self.qr_cmd_pub.publish(cmd_msg)
        
        # HUD Status bar
        status_text = f"Status: {'QR DETECTED' if self.qr_detected else 'NO QR'} | Command: {command.upper()}"
        status_color = COLOR_GREEN if self.qr_detected else COLOR_RED
        cv2.putText(frame, status_text, (10, height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # HUD FPS info
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, height - 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_WHITE, 2)
        
        # Enqueue frame for display thread
        if self.frame_queue.full():
            try:
                self.frame_queue.get_nowait()
            except:
                pass
        
        try:
            self.frame_queue.put_nowait(frame)
        except:
            pass
    
    def display_loop(self):
        """OpenCV GUI display loop thread."""
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        
        while self.is_displaying:
            if not self.frame_queue.empty():
                try:
                    frame = self.frame_queue.get_nowait()
                    cv2.imshow(WINDOW_NAME, frame)
                except:
                    pass
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q') or key == 27:
                self.get_logger().info("Quit key pressed.")
                self.is_displaying = False
                break
        
        cv2.destroyAllWindows()
    
    def print_stats(self):
        """Diagnostic telemetry output."""
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        self.get_logger().info(
            f"Stats | Frames: {self.frame_count} | QR Detections: {self.qr_count} | "
            f"FPS: {fps:.1f} | Current: {'QR=' + self.qr_zone.upper() if self.qr_detected else 'NO QR'}"
        )
    
    def cleanup(self):
        """Terminates capture threads and releases camera devices."""
        self.is_capturing = False
        self.is_displaying = False
        if hasattr(self, 'capture_thread') and self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        if hasattr(self, 'display_thread') and self.display_thread:
            self.display_thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
        if hasattr(self, 'pipeline') and self.pipeline is not None:
            try:
                self.pipeline.stop()
            except Exception:
                pass
        if hasattr(self, 'dai_device') and self.dai_device is not None:
            try:
                self.dai_device.close()
            except Exception:
                pass
        cv2.destroyAllWindows()
        self.get_logger().info("QR Tracker cleaned up.")

def main(args=None):
    rclpy.init(args=args)
    
    try:
        tracker = QRTracker()
        
        # Spin once inside a sleep loop to keep GUI responsive
        while tracker.is_displaying and rclpy.ok():
            rclpy.spin_once(tracker, timeout_sec=0.1)
            
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'tracker' in locals():
            tracker.cleanup()
            tracker.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()