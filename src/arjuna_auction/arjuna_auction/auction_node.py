#!/usr/bin/env python3
"""
TerrainFleet - Phase 1 & 8: Decentralized Auction Node (+ Dashboard Fault Injection & Learned Bidder)
==================================================================================================

Runs identically on each robot (parameterized by robot_id).
In decentralized mode, there is NO central dispatcher: every robot independently computes
its own bid, broadcasts it, and independently determines the winner from the same broadcast
bids received by all robots.

BIDDING MODES:
1. Heuristic Bid (Default):
     bid = w_distance * distance_to_task
         + w_battery * (1.0 - battery_level)
         + w_failure * failure_history_count

2. Learned Bidder (Part 8):
     When `use_learned_bid:=True` and `model_path` (e.g. `bid_model.json`) exists,
     evaluates the trained regression model to predict the navigation cost.

DASHBOARD FAULT INJECTION & CONTROLS:
  - /fleet/override/<robot_id>      : {"battery_override": 0.15, "x_override": 1.2, "y_override": 3.0}
  - /fleet/comms_degrade/<robot_id> : {"drop_prob": 0.3, "delay_sec": 0.5}
  - /fleet/soft_kill/<robot_id>     : {"killed": true}
  - /fleet/mode                     : "decentralized" or "centralized"
  - /fleet/stop_all                 : Immediately cancels active navigation goals

USAGE:
  ros2 run arjuna_auction auction_node --ros-args \
      -p robot_id:=arjuna_1 \
      -p fleet_robot_ids:="['arjuna_1','arjuna_2']" \
      -p odom_topic:=/arjuna_1/odom \
      -p battery_topic:=/arjuna_1/battery_state \
      -p bid_window_sec:=2.0 \
      -p frame_id:=map
"""

import csv
import json
import math
import random
import threading
import time
from pathlib import Path
from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from sensor_msgs.msg import BatteryState
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped


class AuctionNode(Node):
    def __init__(self, node_name: str = 'auction_node'):
        super().__init__(node_name)

        # --- Parameters ---
        self.declare_parameter('robot_id', 'arjuna_1')
        self.declare_parameter('fleet_robot_ids', ['arjuna_1', 'arjuna_2'])
        self.declare_parameter('bid_window_sec', 2.0)
        self.declare_parameter('planner_id', 'GridBased')
        self.declare_parameter('frame_id', 'map')
        self.declare_parameter('pose_topic', '')
        self.declare_parameter('odom_topic', 'wheel/odom')
        self.declare_parameter('battery_topic', 'battery_state')
        self.declare_parameter('w_distance', 1.0)
        self.declare_parameter('w_battery', 5.0)
        self.declare_parameter('w_failure', 2.0)
        self.declare_parameter('log_path', 'auction_log.csv')
        self.declare_parameter('use_learned_bid', False)
        self.declare_parameter('model_path', 'bid_model.json')

        self.robot_id = self.get_parameter('robot_id').value
        self.fleet_robot_ids = self.get_parameter('fleet_robot_ids').value
        self.bid_window = float(self.get_parameter('bid_window_sec').value)
        self.planner_id = self.get_parameter('planner_id').value
        self.frame_id = self.get_parameter('frame_id').value
        self.w_distance = float(self.get_parameter('w_distance').value)
        self.w_battery = float(self.get_parameter('w_battery').value)
        self.w_failure = float(self.get_parameter('w_failure').value)
        self.log_path = self.get_parameter('log_path').value
        self.use_learned_bid = bool(self.get_parameter('use_learned_bid').value)
        self.model_path = self.get_parameter('model_path').value

        # --- Real sensor state ---
        self.current_pose = None
        self.battery_level = 1.0
        self.failure_history_count = 0

        # --- Distance/speed tracking for the currently-executing task ---
        self.tracking_task_id = None
        self.task_distance_m = 0.0
        self.last_tracked_pose = None
        self.current_goal_handle = None

        # --- Dashboard overrides & fault states ---
        self.battery_override = None     # None = use real sensor
        self.position_override = None    # None = use real map pose; else (x, y)
        self.soft_killed = False
        self.comms_drop_prob = 0.0
        self.comms_delay_sec = 0.0
        self.current_mode = 'decentralized'

        self.open_tasks = {}
        self.in_progress = {}
        self.bid_timers = {}
        self.pending_tasks = []          # Queue for tasks won while busy: [(task_id, x, y, heading)]

        # --- Load learned bidder model if available ---
        self.learned_model = self._load_learned_model()

        self.log_fieldnames = [
            'timestamp', 'task_id', 'observing_robot_id', 'my_bid', 'all_bids_json',
            'winner', 'is_reauction', 'planner_id', 'task_x', 'task_y',
            'nav_success', 'nav_duration_s', 'mode',
            'distance_traveled_m', 'avg_speed_mps',
        ]

        # --- Subscriptions ---
        pose_topic = self.get_parameter('pose_topic').value
        if not pose_topic:
            pose_topic = f'/{self.robot_id}/amcl_pose'
        elif not pose_topic.startswith('/'):
            pose_topic = f'/{self.robot_id}/{pose_topic}'

        odom_topic = self.get_parameter('odom_topic').value
        if not odom_topic.startswith('/'):
            odom_topic = f'/{self.robot_id}/{odom_topic}'
        battery_topic = self.get_parameter('battery_topic').value
        if not battery_topic.startswith('/'):
            battery_topic = f'/{self.robot_id}/{battery_topic}'

        self.create_subscription(PoseWithCovarianceStamped, pose_topic, self.amcl_pose_callback, 10)
        self.create_subscription(Odometry, odom_topic, self.odom_callback, 10)
        self.create_subscription(BatteryState, battery_topic, self.battery_callback, 10)

        # Fleet auction topics
        self.create_subscription(String, '/fleet/task_announcement', self.task_announcement_callback, 10)
        self.create_subscription(String, '/fleet/task_bids', self.task_bid_callback, 10)
        self.create_subscription(String, '/fleet/task_claims', self.task_claim_callback, 10)
        self.create_subscription(String, '/fleet/task_completion', self.task_completion_callback, 10)
        self.create_subscription(String, '/fleet/robot_failure', self.robot_failure_callback, 10)

        # Dashboard / Control topics
        self.create_subscription(String, f'/fleet/override/{self.robot_id}', self.override_callback, 10)
        self.create_subscription(String, f'/fleet/comms_degrade/{self.robot_id}', self.comms_degrade_callback, 10)
        self.create_subscription(String, f'/fleet/soft_kill/{self.robot_id}', self.soft_kill_callback, 10)
        self.create_subscription(String, '/fleet/mode', self.mode_callback, 10)
        self.create_subscription(String, '/fleet/stop_all', self.stop_all_callback, 10)

        # Publishers
        self.bid_pub = self.create_publisher(String, '/fleet/task_bids', 10)
        self.claim_pub = self.create_publisher(String, '/fleet/task_claims', 10)
        self.completion_pub = self.create_publisher(String, '/fleet/task_completion', 10)
        self.announcement_pub = self.create_publisher(String, '/fleet/task_announcement', 10)

        # Nav2 Action Client
        nav_action_name = f'/{self.robot_id}/navigate_to_pose'
        self.nav_client = ActionClient(self, NavigateToPose, nav_action_name)

        self.get_logger().info("=" * 60)
        self.get_logger().info(
            f"AuctionNode started for [{self.robot_id}] | Fleet: {self.fleet_robot_ids}"
        )
        self.get_logger().info(
            f"Bidding: {'LEARNED' if (self.use_learned_bid and self.learned_model) else 'HEURISTIC'} "
            f"| Bid Window: {self.bid_window}s | Pose: {pose_topic}"
        )
        self.get_logger().info("=" * 60)

    # --- Learned Model Helper ---
    def _load_learned_model(self):
        if not self.use_learned_bid:
            return None
        p = Path(self.model_path)
        if not p.exists():
            self.get_logger().warn(f"Learned model path '{self.model_path}' not found. Falling back to heuristic.")
            return None
        try:
            with open(p, 'r') as f:
                model_data = json.load(f)
            self.get_logger().info(f"Loaded learned bidding weights from {self.model_path}")
            return model_data
        except Exception as e:
            self.get_logger().warn(f"Failed to load learned model: {e}. Using heuristic.")
            return None

    # --- Logging ---
    def _log_row(self, row: dict):
        write_header = not Path(self.log_path).exists()
        with open(self.log_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.log_fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow(row)

    # --- Real Sensor Updates ---
    def amcl_pose_callback(self, msg: PoseWithCovarianceStamped):
        # Position in map frame from AMCL localization
        self.current_pose = (msg.pose.pose.position.x, msg.pose.pose.position.y)

    def odom_callback(self, msg: Odometry):
        # Fallback for current pose if AMCL has not yet localized
        if self.current_pose is None:
            self.current_pose = (msg.pose.pose.position.x, msg.pose.pose.position.y)

        pos = (msg.pose.pose.position.x, msg.pose.pose.position.y)
        if self.tracking_task_id is not None:
            if self.last_tracked_pose is not None:
                dx = pos[0] - self.last_tracked_pose[0]
                dy = pos[1] - self.last_tracked_pose[1]
                self.task_distance_m += math.sqrt(dx * dx + dy * dy)
            self.last_tracked_pose = pos

    def battery_callback(self, msg: BatteryState):
        if msg.percentage >= 0.0:
            self.battery_level = msg.percentage if msg.percentage <= 1.0 else msg.percentage / 100.0

    # --- Dashboard Callbacks ---
    def override_callback(self, msg: String):
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            self.get_logger().warn(f"Malformed override message: {msg.data}")
            return

        # Independent battery override handling
        if data.get('clear_battery', False):
            self.battery_override = None
        elif 'battery_override' in data:
            battery_val = data['battery_override']
            self.battery_override = float(battery_val) if battery_val is not None else None

        # Independent position override handling
        if data.get('clear_position', False):
            self.position_override = None
        elif 'position_override' in data:
            pos_val = data['position_override']
            if pos_val is not None and 'x' in pos_val and 'y' in pos_val:
                self.position_override = (float(pos_val['x']), float(pos_val['y']))
            else:
                self.position_override = None
        elif 'x_override' in data and 'y_override' in data:
            x_val = data.get('x_override')
            y_val = data.get('y_override')
            if x_val is not None and y_val is not None:
                self.position_override = (float(x_val), float(y_val))

        # Full reset
        if data.get('reset_all', False):
            self.battery_override = None
            self.position_override = None

        self.get_logger().info(
            f"Override state updated: battery={self.battery_override}, position={self.position_override}"
        )

    def comms_degrade_callback(self, msg: String):
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        self.comms_drop_prob = float(data.get('drop_prob', 0.0))
        self.comms_delay_sec = float(data.get('delay_sec', 0.0))
        self.get_logger().info(
            f"Comms degradation: drop_prob={self.comms_drop_prob}, delay_sec={self.comms_delay_sec}"
        )

    def soft_kill_callback(self, msg: String):
        try:
            data = json.loads(msg.data)
            self.soft_killed = bool(data.get('killed', False))
            if self.soft_killed:
                self.get_logger().warn(f"[{self.robot_id}] SOFT-KILLED. Stopping participation in auctions.")
                # Cancel current goal if running
                if self.current_goal_handle:
                    self.current_goal_handle.cancel_goal_async()
            else:
                self.get_logger().info(f"[{self.robot_id}] REVIVED from soft-kill.")
        except Exception:
            pass

    def mode_callback(self, msg: String):
        new_mode = msg.data.strip()
        if new_mode in ('decentralized', 'centralized') and new_mode != self.current_mode:
            self.current_mode = new_mode
            self.get_logger().warn(f"Auction node mode switched to: {self.current_mode}")

    def stop_all_callback(self, msg: String):
        self.get_logger().warn(f"🚨 EMERGENCY STOP received! Cancelling navigation on [{self.robot_id}]")
        if self.current_goal_handle is not None:
            try:
                self.current_goal_handle.cancel_goal_async()
            except Exception as e:
                self.get_logger().error(f"Error cancelling goal: {e}")
            self.current_goal_handle = None

    def _degraded_publish(self, publisher, msg):
        if self.soft_killed:
            return
        if self.comms_drop_prob > 0.0 and random.random() < self.comms_drop_prob:
            self.get_logger().warn(f"[comms_degrade] Dropped outgoing message from {self.robot_id}")
            return
        if self.comms_delay_sec > 0.0:
            threading.Timer(self.comms_delay_sec, lambda: publisher.publish(msg)).start()
        else:
            publisher.publish(msg)

    # --- Auction Bidding Logic ---
    def compute_bid(self, task_x: float, task_y: float, is_reauction: bool = False, failed_by: str = '') -> float:
        bid, _ = self.compute_bid_breakdown(task_x, task_y, is_reauction=is_reauction, failed_by=failed_by)
        return float(bid)

    def compute_bid_breakdown(self, task_x: float, task_y: float, is_reauction: bool = False, failed_by: str = '') -> tuple:
        """
        Computes the bid and returns (bid, breakdown_dict) including all formula parameters:
        - battery level B and battery multiplier variable mu_battery (0 if B < 0.10 else 1)
        - distance D and weighted distance cost
        - inverted battery cost
        - failure count F and weighted failure cost
        - busy and re-auction penalties
        - base formula cost
        - final bid = mu_battery * base_formula_cost
        """
        if self.position_override is not None:
            x, y = self.position_override
        elif self.current_pose is not None:
            x, y = self.current_pose
        else:
            x, y = None, None

        if x is None:
            distance = 1e6
        else:
            dx = task_x - x
            dy = task_y - y
            distance = math.sqrt(dx * dx + dy * dy)

        battery = self.battery_override if self.battery_override is not None else self.battery_level
        busy_penalty = 1000.0 if (self.current_goal_handle is not None or self.robot_id in self.in_progress) else 0.0

        # Battery multiplier variable:
        # Value is 0 when battery < 10% (0.10), and 1 when battery >= 10%
        battery_multiplier = 0.0 if battery < 0.10 else 1.0

        reauct_penalty = 0.0
        if (is_reauction and failed_by == self.robot_id) or (is_reauction and self.failure_history_count > 0 and failed_by == self.robot_id):
            reauct_penalty = 1000.0  # Massive penalty ensures healthy peer wins the re-auctioned task!

        # If learned model is active
        if self.use_learned_bid and self.learned_model is not None:
            try:
                coefs = self.learned_model.get('coefficients', {})
                intercept = float(self.learned_model.get('intercept', 0.0))
                base_bid = (
                    intercept
                    + coefs.get('distance', 1.0) * distance
                    + coefs.get('battery_inv', 5.0) * (1.0 - battery)
                    + coefs.get('failures', 2.0) * self.failure_history_count
                    + busy_penalty
                    + reauct_penalty
                )
                final_bid = battery_multiplier * max(0.001, float(base_bid))
                breakdown = {
                    'battery': round(float(battery), 3),
                    'battery_multiplier': int(battery_multiplier),
                    'is_eligible': bool(battery_multiplier > 0),
                    'distance': round(float(distance), 3) if distance < 1e5 else -1.0,
                    'base_cost': round(float(base_bid), 3),
                    'final_bid': round(float(final_bid), 3),
                    'w_distance': float(coefs.get('distance', 1.0)),
                    'w_battery': float(coefs.get('battery_inv', 5.0)),
                    'w_failure': float(coefs.get('failures', 2.0)),
                    'failures': self.failure_history_count,
                    'busy_penalty': busy_penalty,
                    'reauct_penalty': reauct_penalty,
                    'mode': 'learned'
                }
                return float(final_bid), breakdown
            except Exception as e:
                self.get_logger().warn(f"Learned bid evaluation failed ({e}); falling back to heuristic.")

        # Default Heuristic formula
        dist_cost = self.w_distance * distance
        bat_cost = self.w_battery * (1.0 - battery)
        fail_cost = self.w_failure * self.failure_history_count
        base_bid = dist_cost + bat_cost + fail_cost + busy_penalty + reauct_penalty

        # Multiply base formula by battery threshold variable
        final_bid = battery_multiplier * float(base_bid)

        breakdown = {
            'battery': round(float(battery), 3),
            'battery_multiplier': int(battery_multiplier),
            'is_eligible': bool(battery_multiplier > 0),
            'distance': round(float(distance), 3) if distance < 1e5 else -1.0,
            'dist_cost': round(float(dist_cost), 3) if distance < 1e5 else -1.0,
            'bat_cost': round(float(bat_cost), 3),
            'fail_cost': round(float(fail_cost), 3),
            'base_cost': round(float(base_bid), 3),
            'final_bid': round(float(final_bid), 3),
            'w_distance': self.w_distance,
            'w_battery': self.w_battery,
            'w_failure': self.w_failure,
            'failures': self.failure_history_count,
            'busy_penalty': busy_penalty,
            'reauct_penalty': reauct_penalty,
            'mode': 'heuristic'
        }
        return float(final_bid), breakdown

    def task_announcement_callback(self, msg: String):
        if self.current_mode != 'decentralized' or self.soft_killed:
            return

        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            self.get_logger().warn(f"Malformed task announcement: {msg.data}")
            return

        task_id = data['task_id']
        task_x = float(data['x'])
        task_y = float(data['y'])
        heading = float(data.get('heading', 0.0))
        is_reauction = bool(data.get('is_reauction', False))
        failed_by = data.get('failed_by', '')

        # Guard: If I am currently navigating to this task, do NOT abort or restart it!
        if self.in_progress.get(self.robot_id) == task_id and self.current_goal_handle is not None:
            self.get_logger().warn(
                f"[{task_id}] Received announcement, but I am ALREADY actively navigating to it! Ignoring."
            )
            # Re-assert claim so other robots know I am still executing it
            claim_msg = String()
            claim_msg.data = json.dumps({'task_id': task_id, 'robot_id': self.robot_id})
            self._degraded_publish(self.claim_pub, claim_msg)
            return

        if task_id in self.open_tasks:
            # If not a reauction and already decided, skip duplicate announcement
            if not is_reauction and self.open_tasks[task_id].get('decided', False):
                return

        self.open_tasks[task_id] = {
            'x': task_x, 'y': task_y, 'heading': heading,
            'bids': {}, 'decided': False, 'is_reauction': is_reauction,
        }

        my_bid, breakdown = self.compute_bid_breakdown(task_x, task_y, is_reauction=is_reauction, failed_by=failed_by)
        self.open_tasks[task_id]['bids'][self.robot_id] = my_bid

        bid_payload = {
            'task_id': task_id,
            'robot_id': self.robot_id,
            'bid': my_bid,
            'breakdown': breakdown,
            'battery': breakdown.get('battery'),
            'battery_multiplier': breakdown.get('battery_multiplier'),
            'distance': breakdown.get('distance'),
            'base_cost': breakdown.get('base_cost'),
            'is_eligible': breakdown.get('is_eligible', True),
        }

        bid_msg = String()
        bid_msg.data = json.dumps(bid_payload)
        self._degraded_publish(self.bid_pub, bid_msg)

        re_txt = f" (RE-AUCTION, failed_by={failed_by})" if is_reauction else ""
        elig_txt = "ELIGIBLE" if breakdown.get('is_eligible') else "DISQUALIFIED (battery < 10%, multiplier=0)"
        self.get_logger().info(
            f"[{task_id}] Announced{re_txt}. My bid: {my_bid:.3f} [{elig_txt}] (mult={breakdown.get('battery_multiplier')}, bat={breakdown.get('battery')})"
        )

        # Cancel any previous timer for this task to avoid leaking repeating timers
        if task_id in self.bid_timers:
            try:
                self.bid_timers[task_id].cancel()
                self.destroy_timer(self.bid_timers[task_id])
            except Exception:
                pass

        timer = self.create_timer(self.bid_window, lambda t=task_id: self.decide_winner(t))
        self.bid_timers[task_id] = timer

    def task_bid_callback(self, msg: String):
        try:
            data = json.loads(msg.data)
            task_id = data['task_id']
            robot_id = data['robot_id']
            bid = float(data['bid'])
            if task_id in self.open_tasks:
                self.open_tasks[task_id]['bids'][robot_id] = bid
        except Exception:
            pass

    def decide_winner(self, task_id: str):
        # Cancel and cleanup repeating timer
        timer = self.bid_timers.pop(task_id, None)
        if timer is not None:
            try:
                timer.cancel()
                self.destroy_timer(timer)
            except Exception:
                pass

        task = self.open_tasks.get(task_id)
        if task is None or task.get('decided', False):
            return
        task['decided'] = True

        bids = task['bids']
        if not bids:
            self.get_logger().warn(f"[{task_id}] No bids received - cannot decide winner.")
            return

        # Lowest bid wins among eligible robots.
        # Bids where battery_multiplier == 0 (battery < 10%, bid == 0.0) are disqualified.
        eligible_bids = {k: v for k, v in bids.items() if v > 0.0}
        if not eligible_bids:
            self.get_logger().warn(
                f"[{task_id}] All bids disqualified (multiplier=0 / battery < 10%). No winner can be chosen."
            )
            return

        winner = min(eligible_bids.items(), key=lambda kv: (kv[1], kv[0]))[0]

        self._log_row({
            'timestamp': time.time(),
            'task_id': task_id,
            'observing_robot_id': self.robot_id,
            'my_bid': bids.get(self.robot_id, ''),
            'all_bids_json': json.dumps({k: round(v, 3) for k, v in bids.items()}),
            'winner': winner,
            'is_reauction': task['is_reauction'],
            'planner_id': self.planner_id,
            'task_x': task['x'],
            'task_y': task['y'],
            'nav_success': '',
            'nav_duration_s': '',
            'mode': self.current_mode,
            'distance_traveled_m': '',
            'avg_speed_mps': '',
        })

        if winner == self.robot_id:
            claim_msg = String()
            claim_msg.data = json.dumps({'task_id': task_id, 'robot_id': self.robot_id})
            self._degraded_publish(self.claim_pub, claim_msg)

            if self.current_goal_handle is not None:
                self.get_logger().info(
                    f"🏆 [{task_id}] I WON! Currently executing [{self.in_progress.get(self.robot_id)}], "
                    f"queuing [{task_id}] to execute next."
                )
                self.pending_tasks.append((task_id, task['x'], task['y'], task.get('heading', 0.0)))
            else:
                self.get_logger().info(f"🏆 [{task_id}] I WON! Bids: {bids}. Executing task...")
                self.in_progress[self.robot_id] = task_id
                self.execute_task(task_id, task['x'], task['y'], task.get('heading', 0.0))
        else:
            self.get_logger().info(f"[{task_id}] Won by [{winner}] (bids: {bids}).")

    def task_claim_callback(self, msg: String):
        try:
            data = json.loads(msg.data)
            rid = data.get('robot_id')
            tid = data.get('task_id')
            self.in_progress[rid] = tid
            if hasattr(self, 'active_fault_record') and self.active_fault_record and self.active_fault_record.get('task_id') == tid:
                now = time.time()
                self.active_fault_record['t_rewon'] = now
                self.active_fault_record['rewon_latency_s'] = round(now - self.active_fault_record['t_reannounced'], 3)
                self.active_fault_record['survivor_robot_id'] = rid
        except Exception:
            pass

    def task_completion_callback(self, msg: String):
        try:
            data = json.loads(msg.data)
            c_rid = data.get('robot_id')
            c_tid = data.get('task_id')
            # Peer completed or failed: clear in_progress tracking
            if c_rid in self.in_progress:
                self.in_progress.pop(c_rid, None)
            if c_tid in self.open_tasks:
                self.open_tasks.pop(c_tid, None)
        except Exception:
            pass

    # --- Nav2 Task Execution ---
    def execute_task(self, task_id: str, x: float, y: float, heading: float = 0.0):
        self.tracking_task_id = task_id
        self.task_distance_m = 0.0
        self.last_tracked_pose = self.current_pose

        if not self.nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error(f"[{task_id}] navigate_to_pose action server not available.")
            self._record_nav_result(task_id, False, 0.0)
            return

        goal_msg = NavigateToPose.Goal()
        pose = PoseStamped()
        pose.header.frame_id = self.frame_id
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        # Orientation from heading yaw
        pose.pose.orientation.z = math.sin(heading / 2.0)
        pose.pose.orientation.w = math.cos(heading / 2.0)
        goal_msg.pose = pose

        t0 = time.time()
        send_future = self.nav_client.send_goal_async(goal_msg)
        send_future.add_done_callback(
            lambda future: self._nav_goal_response(future, task_id, t0)
        )

    def _nav_goal_response(self, future, task_id: str, t0: float):
        goal_handle = future.result()
        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error(f"[{task_id}] Nav goal rejected by Nav2.")
            dur = time.time() - t0
            self._record_nav_result(task_id, False, dur)
            self.failure_history_count += 1
            self.in_progress.pop(self.robot_id, None)
            self.open_tasks.pop(task_id, None)
            comp_msg = String()
            comp_msg.data = json.dumps({
                'task_id': task_id,
                'robot_id': self.robot_id,
                'success': False,
                'duration': round(dur, 3),
                'distance': 0.0,
                'avg_speed': 0.0,
                'timestamp': time.time(),
            })
            self._degraded_publish(self.completion_pub, comp_msg)
            return

        self.current_goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            lambda fut: self._nav_result(fut, task_id, t0)
        )

    def _nav_result(self, future, task_id: str, t0: float):
        self.current_goal_handle = None
        duration = time.time() - t0
        result = future.result()
        success = (result is not None and result.status == 4)
        if not success:
            self.failure_history_count += 1

        distance = self.task_distance_m
        avg_speed = distance / duration if duration > 0 else 0.0
        self.tracking_task_id = None

        self.get_logger().info(
            f"✅ [{task_id}] Nav finished: success={success}, duration={duration:.2f}s, "
            f"distance={distance:.2f}m, avg_speed={avg_speed:.3f}m/s"
        )
        self._record_nav_result(task_id, success, duration, distance, avg_speed)
        self.in_progress.pop(self.robot_id, None)
        self.open_tasks.pop(task_id, None)

        # Broadcast completion to entire fleet and dashboard
        comp_msg = String()
        comp_msg.data = json.dumps({
            'task_id': task_id,
            'robot_id': self.robot_id,
            'success': success,
            'duration': round(duration, 3),
            'distance': round(distance, 3),
            'avg_speed': round(avg_speed, 3),
            'timestamp': time.time(),
        })
        self._degraded_publish(self.completion_pub, comp_msg)

        # If there are queued pending tasks, execute next one immediately
        if self.pending_tasks:
            next_t = self.pending_tasks.pop(0)
            next_tid, next_x, next_y, next_heading = next_t
            self.get_logger().info(f"🚀 Executing next queued task [{next_tid}] from pending queue...")
            self.in_progress[self.robot_id] = next_tid
            self.execute_task(next_tid, next_x, next_y, next_heading)

        # Log fault recovery timeline if this was a recovery task
        if hasattr(self, 'active_fault_record') and self.active_fault_record and self.active_fault_record.get('task_id') == task_id:
            now = time.time()
            self.active_fault_record['t_completed'] = now
            self.active_fault_record['total_recovery_time_s'] = round(now - self.active_fault_record['t_fault'], 3)
            self.active_fault_record['nav_success'] = success
            self.active_fault_record['survivor_robot_id'] = self.robot_id
            self._log_fault_row(self.active_fault_record)
            self.active_fault_record = None

    def _record_nav_result(self, task_id, success, duration, distance=0.0, avg_speed=0.0):
        self._log_row({
            'timestamp': time.time(),
            'task_id': task_id,
            'observing_robot_id': self.robot_id,
            'my_bid': '',
            'all_bids_json': '',
            'winner': self.robot_id,
            'is_reauction': '',
            'planner_id': self.planner_id,
            'task_x': '', 'task_y': '',
            'nav_success': success,
            'nav_duration_s': round(duration, 3),
            'mode': self.current_mode,
            'distance_traveled_m': round(distance, 3),
            'avg_speed_mps': round(avg_speed, 3),
        })

    def _log_fault_row(self, fault_data: dict):
        fieldnames = [
            'timestamp', 'failed_robot_id', 'detected_by', 'fault_type',
            't_fault', 't_detected', 'detection_latency_s',
            't_reannounced', 'reannounce_latency_s',
            't_rewon', 'rewon_latency_s',
            't_completed', 'total_recovery_time_s',
            'task_id', 'survivor_robot_id', 'nav_success'
        ]
        log_file = Path('fault_log.csv')
        write_header = not log_file.exists()
        try:
            with open(log_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if write_header:
                    writer.writeheader()
                writer.writerow({
                    'timestamp': time.time(),
                    'failed_robot_id': fault_data.get('failed_robot_id', ''),
                    'detected_by': fault_data.get('detected_by', ''),
                    'fault_type': fault_data.get('fault_type', 'power_off'),
                    't_fault': fault_data.get('t_fault', ''),
                    't_detected': fault_data.get('t_detected', ''),
                    'detection_latency_s': fault_data.get('detection_latency_s', ''),
                    't_reannounced': fault_data.get('t_reannounced', ''),
                    'reannounce_latency_s': fault_data.get('reannounce_latency_s', ''),
                    't_rewon': fault_data.get('t_rewon', ''),
                    'rewon_latency_s': fault_data.get('rewon_latency_s', ''),
                    't_completed': fault_data.get('t_completed', ''),
                    'total_recovery_time_s': fault_data.get('total_recovery_time_s', ''),
                    'task_id': fault_data.get('task_id', ''),
                    'survivor_robot_id': fault_data.get('survivor_robot_id', ''),
                    'nav_success': fault_data.get('nav_success', ''),
                })
            self.get_logger().info(f"Recorded real fault recovery event to fault_log.csv: {fault_data}")
        except Exception as e:
            self.get_logger().error(f"Error logging fault record: {e}")

    # --- Fault Handling: Re-Auction on Peer Robot Failure ---
    def robot_failure_callback(self, msg: String):
        if self.current_mode != 'decentralized' or self.soft_killed:
            return

        try:
            data = json.loads(msg.data)
            failed_robot = data['failed_robot_id']
        except Exception:
            return

        if failed_robot == self.robot_id:
            # Peer reported me offline, but I am alive! Ignore.
            return

        abandoned_task = self.in_progress.get(failed_robot)
        if abandoned_task is None:
            return

        detection_ts = float(data.get('detection_timestamp', time.time()))
        last_seen_ts = float(data.get('last_seen_timestamp', detection_ts - 3.0))
        fault_type = data.get('fault_type', 'power_off')

        self.get_logger().warn(
            f"⚠️ Peer [{failed_robot}] failed mid-task '{abandoned_task}'. Triggering RE-AUCTION."
        )
        original = self.open_tasks.get(abandoned_task)
        if original is None:
            self.get_logger().error(f"Cannot re-auction '{abandoned_task}': missing location record.")
            return

        self.open_tasks.pop(abandoned_task, None)
        self.in_progress.pop(failed_robot, None)

        now = time.time()
        self.active_fault_record = {
            'failed_robot_id': failed_robot,
            'detected_by': data.get('detected_by', self.robot_id),
            'fault_type': fault_type,
            't_fault': last_seen_ts,
            't_detected': detection_ts,
            'detection_latency_s': round(detection_ts - last_seen_ts, 3),
            't_reannounced': now,
            'reannounce_latency_s': round(now - detection_ts, 3),
            'task_id': abandoned_task,
        }

        reannounce_msg = String()
        reannounce_msg.data = json.dumps({
            'task_id': abandoned_task,
            'x': original['x'],
            'y': original['y'],
            'heading': original.get('heading', 0.0),
            'is_reauction': True,
        })
        self._degraded_publish(self.announcement_pub, reannounce_msg)


def main(args=None):
    # Parse robot_id from args if passed, to avoid node name collisions in multi-robot DDS graph
    import sys
    robot_id = 'arjuna_unknown'
    raw_args = sys.argv[1:] if args is None else args
    for a in raw_args:
        if 'robot_id:=' in a:
            robot_id = a.split('robot_id:=')[1].strip("'\"")
            break

    node_name = f'auction_node_{robot_id}' if robot_id != 'arjuna_unknown' else 'auction_node'

    rclpy.init(args=args)
    node = AuctionNode(node_name=node_name)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        if rclpy.ok():
            try:
                rclpy.shutdown()
            except Exception:
                pass


if __name__ == '__main__':
    main()
