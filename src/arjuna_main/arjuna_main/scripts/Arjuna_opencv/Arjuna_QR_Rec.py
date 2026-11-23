#!/usr/bin/env python3
"""
Arjuna QR Recognition Debug Node
================================
Subscribes to '/arjuna/camera/image_raw/compressed' and decodes the image in real-time,
visualizing any detected QR codes in a window and saving a snapshot inside the workspace.

-----------------------------------------------------------------------------------------
ARCHITECTURE & CONTROL FLOW:
1. Subscription:
   - Listens on '/arjuna/camera/image_raw/compressed' (sensor_msgs/CompressedImage)
     for JPEG-encoded video frames.
2. OpenCV Decoding (Pure Python):
   - Converts the byte array to numpy and decodes it using cv2.imdecode (no cv_bridge).
3. Dual QR Decoding:
   - Primary: Uses pyzbar to decode multiple QR codes.
   - Fallback: Uses OpenCV's QRCodeDetector if pyzbar is not available.
4. Bounding Box & Label Overlays:
   - Draws a green boundary for pyzbar detections and blue for OpenCV detections.
   - Overlays the QR payload string above the box.
5. Snapshot Persistence:
   - Saves a debug JPEG image ('qr_debug.jpg') inside the workspace directory (defaulting to
     '/home/arjuna/Arjuna_ws/qr_debug.jpg') at a throttled rate (once per second) for inspection.

Company: NEWRRO TECH LLP
Website: www.newrro.in
-----------------------------------------------------------------------------------------
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
import numpy as np
import cv2
import time
import os

TOPIC = '/arjuna/camera/image_raw/compressed'
SHOW_WINDOW = True

# Detect pyzbar presence
try:
    from pyzbar import pyzbar
    HAS_PYZBAR = True
except Exception:
    HAS_PYZBAR = False

class QRDebug(Node):
    def __init__(self):
        super().__init__('qr_recog_debug')
        
        # Declare debug output path parameter to avoid writing directly to root /tmp
        self.declare_parameter('debug_img_path', '/home/arjuna/Arjuna_ws/qr_debug.jpg')
        self.debug_img_path = self.get_parameter('debug_img_path').value
        
        # Ensure target directory exists
        target_dir = os.path.dirname(self.debug_img_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
            
        self.sub = self.create_subscription(CompressedImage, TOPIC, self.cb, 10)
        self.detector = cv2.QRCodeDetector()
        self.last_saved = 0
        
        self.get_logger().info("")
        self.get_logger().info("=" * 60)
        self.get_logger().info("ARJUNA QR RECOGNITION DEBUG NODE - ACTIVE")
        self.get_logger().info(f"Subscribed topic: {TOPIC}")
        self.get_logger().info(f"Using pyzbar: {'YES' if HAS_PYZBAR else 'NO (falling back to OpenCV)'}")
        self.get_logger().info(f"Saving debug image to: {self.debug_img_path}")
        self.get_logger().info("=" * 60)

    def cb(self, msg: CompressedImage):
        """Processes incoming compressed frames, extracts QR, and saves a debug snapshot."""
        now = time.time()
        
        # Decode the JPEG byte stream
        try:
            arr = np.frombuffer(msg.data, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                self.get_logger().warn('cv2.imdecode returned None - raw data might be corrupt.')
                return
        except Exception as e:
            self.get_logger().error(f'Failed to decode image stream: {e}')
            return

        h, w = img.shape[:2]
        self.get_logger().debug(f'Frame received: shape={img.shape} len_data={len(msg.data)}')

        found_any = False
        
        # 1. Decode attempt using pyzbar (supports multiple QR codes)
        if HAS_PYZBAR:
            barcodes = pyzbar.decode(img)
            if barcodes:
                found_any = True
                for barcode in barcodes:
                    txt = barcode.data.decode('utf-8', errors='replace')
                    pts = barcode.polygon
                    self.get_logger().info(f'pyzbar detected QR: "{txt}"')
                    
                    # Draw green bounding polygon around QR
                    pts_t = [(p.x, p.y) for p in pts]
                    for i in range(len(pts_t)):
                        cv2.line(img, pts_t[i], pts_t[(i+1)%len(pts_t)], (0, 255, 0), 2)
                    cv2.putText(img, txt, (pts_t[0][0], max(15, pts_t[0][1]-10)), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # 2. Fallback to OpenCV QRCodeDetector (supports single QR code only)
        if not found_any:
            try:
                text, pts, _ = self.detector.detectAndDecode(img)
            except Exception as e:
                self.get_logger().warn(f'detectAndDecode exception: {e}')
                text, pts = None, None
                
            if text:
                found_any = True
                self.get_logger().info(f'OpenCV QR detected QR: "{text}"')
                if pts is not None and len(pts) > 0:
                    try:
                        # Draw blue bounding box
                        pts = pts.astype(int).reshape((-1, 2))
                        for i in range(len(pts)):
                            p1 = tuple(pts[i])
                            p2 = tuple(pts[(i+1)%len(pts)])
                            cv2.line(img, p1, p2, (255, 0, 0), 2)
                        cv2.putText(img, text, (pts[0][0], max(15, pts[0][1]-10)), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                    except Exception as e:
                        self.get_logger().warn(f'Failed to draw points: {e}')

        # Throttled debug image saving (max 1Hz)
        if now - self.last_saved > 1.0:
            try:
                cv2.imwrite(self.debug_img_path, img)
                self.get_logger().info(f'Saved snapshot: {self.debug_img_path} | Found QR: {found_any}')
                self.last_saved = now
            except Exception as e:
                self.get_logger().warn(f'Failed to save snapshot: {e}')

        # Optional GUI visualization
        if SHOW_WINDOW:
            overlay = img.copy()
            # Overlay frame info bar
            cv2.putText(overlay, f'{w}x{h} | pyzbar={HAS_PYZBAR} | Found QR={found_any}', (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
            cv2.imshow('QR Debug', overlay)
            cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = QRDebug()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        if SHOW_WINDOW:
            cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
