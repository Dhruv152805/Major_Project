#!/usr/bin/env python3
"""
Arjuna Camera Publisher Node (Pure Python / No cv_bridge)
==========================================================
Captures camera frames from either an OAK-D camera or standard USB camera,
encodes them directly to JPEG format, and publishes them as CompressedImage 
messages to '/arjuna/camera/image_raw/compressed'.

-----------------------------------------------------------------------------------------
ARCHITECTURE & CONTROL FLOW:
1. Dynamic Camera Discovery:
   - Probes the system using DepthAI (getAllAvailableDevices()) to discover OAK-D cameras.
   - If found, sets up a color camera preview node in DepthAI pipeline.
   - If not found, falls back to OpenCV's VideoCapture backend to capture from a USB camera (e.g. '/dev/video0').
2. Multi-Threaded Capture:
   - The capture loop runs inside a dedicated background thread ('capture_thread').
   - Incoming raw BGR frames are pushed to a FIFO thread-safe frame Queue.
   - To keep latency minimal, if the queue fills up, older frames are discarded (dropped).
3. Direct JPEG Encoding (No cv_bridge):
   - A timer-driven publisher callback runs at the target FPS.
   - It pulls frames from the queue, encodes them into JPEG format via cv2.imencode, 
     populates a std_msgs/Header with current ROS time, and publishes to the compressed topic.
   - Eliminating cv_bridge removes dependencies, making this node extremely portable and lightweight.

Company: NEWRRO TECH LLP
Website: www.newrro.in
-----------------------------------------------------------------------------------------
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
import cv2
import threading
from queue import Queue
import time
import depthai as dai

# Encoding parameters
JPEG_QUALITY = 80
QUEUE_SIZE = 10

class CameraPublisher(Node):
    def __init__(self):
        super().__init__('arjuna_camera_publisher')
        
        # Declare ROS 2 parameters
        self.declare_parameter('camera_type', 'auto')  # 'auto', 'oak', 'usb'
        self.declare_parameter('camera_device', '/dev/video0')
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)
        self.declare_parameter('fps', 30)

        # Retrieve parameters
        camera_type = self.get_parameter('camera_type').value
        camera_device_param = self.get_parameter('camera_device').value
        try:
            # Convert string index to integer if needed (e.g. "/dev/video0" vs "0")
            camera_device = int(camera_device_param)
        except ValueError:
            camera_device = camera_device_param

        frame_width = self.get_parameter('frame_width').value
        frame_height = self.get_parameter('frame_height').value
        fps = self.get_parameter('fps').value

        # Publisher for compressed image stream
        self.image_pub = self.create_publisher(
            CompressedImage, 
            '/arjuna/camera/image_raw/compressed', 
            10)
        
        # Diagnostics
        self.frame_count = 0
        self.dropped_frames = 0
        self.start_time = time.time()
        
        # Frame queue to hand over captured frames to publisher timer thread safely
        self.frame_queue = Queue(maxsize=QUEUE_SIZE)
        
        # Device handlers
        self.cap = None
        self.dai_device = None
        self.pipeline = None
        self.dai_queue = None
        self.is_depthai = False

        # Detect OAK camera / DepthAI availability
        has_oak = False
        try:
            device_infos = dai.Device.getAllAvailableDevices()
            if len(device_infos) > 0:
                has_oak = True
        except Exception as e:
            self.get_logger().warn(f"Failed to query DepthAI devices: {e}")

        # Initialize OAK-D / USB camera based on parameters and discovery
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
        
        # Publishing timer callback to control frame rate
        timer_period = 1.0 / fps
        self.timer = self.create_timer(timer_period, self.publish_frame)
        
        # Diagnostics output timer (every 5 seconds)
        self.stats_timer = self.create_timer(5.0, self.print_stats)
        
        self.get_logger().info("=" * 60)
        self.get_logger().info("ARJUNA CAMERA PUBLISHER - ACTIVE")
        self.get_logger().info(f"Mode: {'DepthAI (OAK)' if self.is_depthai else 'Standard USB (UVC)'}")
        self.get_logger().info(f"Resolution: {frame_width}x{frame_height} @ {fps} FPS")
        self.get_logger().info(f"Topic: /arjuna/camera/image_raw/compressed")
        self.get_logger().info("=" * 60)
    
    def capture_loop(self):
        """Continuous background capture thread."""
        if self.is_depthai:
            while self.is_capturing:
                try:
                    in_rgb = self.dai_queue.get()  # Blocks until frame is ready from OAK-D
                    if in_rgb is not None:
                        frame = in_rgb.getCvFrame()
                        self._enqueue_frame(frame)
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
                self._enqueue_frame(frame)
                
    def _enqueue_frame(self, frame):
        """Thread-safe method to add raw frame to queue. Discards oldest on overflow."""
        if self.frame_queue.full():
            try:
                # Remove oldest frame to avoid latency buildup
                self.frame_queue.get_nowait()
                self.dropped_frames += 1
            except:
                pass
        
        try:
            self.frame_queue.put_nowait(frame)
        except:
            self.dropped_frames += 1
    
    def publish_frame(self):
        """Pulls frame from queue, encodes to JPEG, and publishes."""
        if self.frame_queue.empty():
            return
        
        try:
            frame = self.frame_queue.get_nowait()
        except:
            return
        
        # Construct ROS 2 CompressedImage message
        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_frame'
        msg.format = 'jpeg'
        
        # Encode to JPEG
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
        success, encoded = cv2.imencode('.jpg', frame, encode_param)
        
        if success:
            msg.data = encoded.tobytes()
            self.image_pub.publish(msg)
            self.frame_count += 1
    
    def print_stats(self):
        """Calculates and logs frame drop percentages and average FPS."""
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        total_frames = self.frame_count + self.dropped_frames
        drop_pct = (self.dropped_frames / total_frames * 100) if total_frames > 0 else 0
        
        self.get_logger().info(
            f"Frames: {self.frame_count} | Dropped: {self.dropped_frames} ({drop_pct:.1f}%) | "
            f"FPS: {fps:.1f} | Queue: {self.frame_queue.qsize()}/{QUEUE_SIZE}"
        )
    
    def cleanup(self):
        """Releases all camera devices and stops background threads on exit."""
        self.is_capturing = False
        if hasattr(self, 'capture_thread') and self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
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
        try:
            self.get_logger().info("Camera publisher shut down.")
        except Exception:
            pass

def main(args=None):
    rclpy.init(args=args)
    pub = None
    try:
        pub = CameraPublisher()
        rclpy.spin(pub)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        if pub is not None:
            pub.cleanup()
            pub.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()