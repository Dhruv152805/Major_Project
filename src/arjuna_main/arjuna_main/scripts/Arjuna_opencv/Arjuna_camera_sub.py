#!/usr/bin/env python3
"""
Arjuna Camera Subscriber Node (Pure Python / No cv_bridge)
==========================================================
Subscribes to the compressed video stream, decodes the images directly from bytes 
to BGR matrix format, overlays live performance statistics (FPS), and displays
the output in an interactive window.

-----------------------------------------------------------------------------------------
ARCHITECTURE & CONTROL FLOW:
1. Subscription:
   - Subscribes to '/arjuna/camera/image_raw/compressed' (sensor_msgs/CompressedImage).
2. Direct JPEG Decoding:
   - Converts the incoming message byte array into a numpy array.
   - Decodes the array using cv2.imdecode to obtain a BGR image (avoiding cv_bridge dependency).
3. Threaded GUI (OpenCV HighGUI):
   - Decoded frames are placed inside a FIFO thread-safe frame Queue.
   - An independent GUI thread ('display_loop') runs in parallel, reading frames from the queue
     and displaying them via cv2.imshow.
   - This prevents window refresh stalls and keeps the ROS executor spinning efficiently.
4. User Interaction:
   - The user can press 'Q' or 'ESC' on the visual window to safely stop the node.

Company: NEWRRO TECH LLP
Website: www.newrro.in
-----------------------------------------------------------------------------------------
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
import cv2
import numpy as np
import threading
from queue import Queue
import time

WINDOW_NAME = "Arjuna Camera"
QUEUE_SIZE = 5
SHOW_FPS = True

class CameraSubscriber(Node):
    def __init__(self):
        super().__init__('arjuna_camera_subscriber')
        
        # Diagnostics
        self.frame_count = 0
        self.dropped_frames = 0
        self.start_time = time.time()
        self.last_frame_time = time.time()
        self.current_fps = 0.0
        
        # Frame queue to hand over decoded frames to display thread safely
        self.frame_queue = Queue(maxsize=QUEUE_SIZE)
        
        # Subscriber for incoming compressed images
        self.image_sub = self.create_subscription(
            CompressedImage,
            '/arjuna/camera/image_raw/compressed',
            self.image_callback,
            10)
        
        # Start display thread for GUI window updates
        self.is_displaying = True
        self.display_thread = threading.Thread(target=self.display_loop, daemon=True)
        self.display_thread.start()
        
        # Diagnostics stats log timer (every 5 seconds)
        self.stats_timer = self.create_timer(5.0, self.print_stats)
        
        self.get_logger().info("=" * 60)
        self.get_logger().info("ARJUNA CAMERA SUBSCRIBER - ACTIVE")
        self.get_logger().info("Subscribed: /arjuna/camera/image_raw/compressed")
        self.get_logger().info("Window: 'Arjuna Camera'")
        self.get_logger().info("Press Q or ESC on visual window to quit")
        self.get_logger().info("=" * 60)
    
    def image_callback(self, msg):
        """Callback to receive and decode compressed image messages."""
        try:
            # Decode JPEG byte stream (no cv_bridge)
            np_arr = np.frombuffer(msg.data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if frame is None:
                self.get_logger().warn("Failed to decode compressed image buffer.")
                return
            
            # Calculate stream FPS
            current_time = time.time()
            time_diff = current_time - self.last_frame_time
            if time_diff > 0:
                self.current_fps = 1.0 / time_diff
            self.last_frame_time = current_time
            
            # Overlay active FPS on the image frame
            if SHOW_FPS:
                cv2.putText(frame, f"Stream FPS: {self.current_fps:.1f}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Drop older frames if the display thread is lagging behind
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                    self.dropped_frames += 1
                except:
                    pass
            
            try:
                self.frame_queue.put_nowait(frame)
                self.frame_count += 1
            except:
                self.dropped_frames += 1
                
        except Exception as e:
            self.get_logger().error(f"JPEG Decode error: {e}")
    
    def display_loop(self):
        """OpenCV visualization display loop."""
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        
        while self.is_displaying:
            if not self.frame_queue.empty():
                try:
                    frame = self.frame_queue.get_nowait()
                    cv2.imshow(WINDOW_NAME, frame)
                except:
                    pass
            
            # Listen for key press events inside the window (wait 1ms)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q') or key == 27:
                self.get_logger().info("Quit key detected.")
                self.is_displaying = False
                break
        
        cv2.destroyAllWindows()
    
    def print_stats(self):
        """Logs subscriber performance telemetry."""
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        total_frames = self.frame_count + self.dropped_frames
        drop_pct = (self.dropped_frames / total_frames * 100) if total_frames > 0 else 0
        
        self.get_logger().info(
            f"Frames processed: {self.frame_count} | Dropped: {self.dropped_frames} ({drop_pct:.1f}%) | "
            f"Display FPS: {fps:.1f} | Queue size: {self.frame_queue.qsize()}/{QUEUE_SIZE}"
        )
    
    def cleanup(self):
        """Stops display threads and cleans up resources on shutdown."""
        self.is_displaying = False
        if hasattr(self, 'display_thread') and self.display_thread:
            self.display_thread.join(timeout=2.0)
        cv2.destroyAllWindows()
        self.get_logger().info("Camera subscriber shut down.")

def main(args=None):
    rclpy.init(args=args)
    
    try:
        sub = CameraSubscriber()
        
        # Spin executor loop
        while sub.is_displaying and rclpy.ok():
            rclpy.spin_once(sub, timeout_sec=0.1)
            
    except KeyboardInterrupt:
        pass
    finally:
        if 'sub' in locals():
            sub.cleanup()
            sub.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()