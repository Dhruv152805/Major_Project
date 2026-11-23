#!/usr/bin/env python3
"""
TerrainFleet Web Dashboard Server Node
======================================
Runs on the control laptop.
Provides a REST API and serves the interactive fleet monitoring and control
interface for multi-robot navigation experiments.

Features:
  - Serves offline-ready static web assets (Arjuna.html, Arjuna.css, Arjuna.js)
  - Real-time telemetry monitoring: map-frame pose from amcl_pose, battery, heartbeats, task board
  - Mode switch (Decentralized Auction vs Centralized Baseline)
  - Centralized master robot selector
  - Simulated fault toggle (soft-kill) and physical power-off tracking
  - Independent battery and map position test overrides
  - Communication degradation (packet drop rate, transmission delay)
  - Cancel all active navigation goals (STOP ALL)
  - Real fault recovery timeline logging and telemetry

Zero external web framework dependencies (standard library http.server only).

Usage:
  ros2 run arjuna_main fleet_dashboard
  ./scripts/run_dashboard.py
  python3 src/arjuna_main/arjuna_main/fleet_dashboard_server.py --port 8080
"""

import os
import sys
import csv
import json
import math
import time
import threading
import argparse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseWithCovarianceStamped
from sensor_msgs.msg import BatteryState


def find_workspace_root() -> Path:
    candidates = [
        Path.cwd(),
        Path(__file__).resolve().parents[4] if len(Path(__file__).resolve().parents) >= 5 else Path.cwd(),
        Path.home() / 'Arjuna_ws_team3',
        Path('/home/arjuna/Arjuna_ws_team3'),
        Path('/home/dhruv/Arjuna_ws_team3'),
    ]
    for c in candidates:
        if (c / 'tasks_setA.csv').exists() or (c / 'src' / 'arjuna_main').exists():
            return c.resolve()
    return Path.cwd()


class FleetDashboardNode(Node):
    def __init__(self, port: int = 8080, web_dir: str = None):
        super().__init__('fleet_dashboard_server')
        self.port = port
        self.ws_root = find_workspace_root()

        # Discover web assets directory
        if web_dir:
            self.web_dir = Path(web_dir).resolve()
        else:
            candidates = [
                self.ws_root / 'src' / 'arjuna_main' / 'arjuna_main' / 'webpage',
                Path(__file__).parent / 'webpage',
                self.ws_root / 'install' / 'arjuna_main' / 'share' / 'arjuna_main' / 'webpage',
                Path('/home/arjuna/Arjuna_ws_team3/src/arjuna_main/arjuna_main/webpage'),
                Path('/home/dhruv/Arjuna_ws_team3/src/arjuna_main/arjuna_main/webpage'),
            ]
            self.web_dir = candidates[0]
            for c in candidates:
                if c.exists() and (c / 'Arjuna.html').exists():
                    self.web_dir = c.resolve()
                    break

        self.fleet_robot_ids = ['arjuna_1', 'arjuna_2']

        # Load calibrated home positions from fleet_config.yaml
        self.home_positions = {
            'arjuna_1': {'x': 0.0, 'y': 0.0},
            'arjuna_2': {'x': 2.0, 'y': 0.0}
        }
        cfg_file = self.ws_root / 'fleet_config.yaml'
        if cfg_file.exists():
            try:
                with open(cfg_file, 'r') as f:
                    cur_r = None
                    for line in f:
                        l = line.strip()
                        if l.startswith('arjuna_1:'): cur_r = 'arjuna_1'
                        elif l.startswith('arjuna_2:'): cur_r = 'arjuna_2'
                        elif cur_r and l.startswith('x:'):
                            self.home_positions[cur_r]['x'] = float(l.split(':', 1)[1].strip())
                        elif cur_r and l.startswith('y:'):
                            self.home_positions[cur_r]['y'] = float(l.split(':', 1)[1].strip())
            except Exception:
                pass

        # Shared Fleet Telemetry State (using RLock to allow nested calls without deadlocks)
        self.state_lock = threading.RLock()
        self.state: Dict[str, Any] = {
            'server_time': time.time(),
            'mode': 'decentralized',
            'centralized_master': 'arjuna_1',
            'bidding_config': {
                'old_formula': 'Bid_old = (w_distance × D) + (w_battery × (1 - B)) + (w_failure × F) + Penalties',
                'enhanced_formula': 'Bid_enhanced = m × [ (w_distance × D) + (w_battery × (1 - B)) + (w_failure × F) + Penalties ]',
                'formula': 'Bid = m × [ (w_distance × D) + (w_battery × (1 - B)) + (w_failure × F) + Penalties ]',
                'variable': 'm',
                'variable_rule': '0 if Battery < 10% (0.10) else 1',
                'multiplier_variable': 'm',
                'multiplier_rule': '0 if Battery < 10% (0.10) else 1',
                'battery_threshold_pct': 10.0,
                'w_distance': 1.0,
                'w_battery': 5.0,
                'w_failure': 2.0,
                'busy_penalty': 1000.0,
                'reauction_penalty': 1000.0,
            },
            'robots': {
                rid: {
                    'id': rid,
                    'name': 'Arjuna 1' if rid == 'arjuna_1' else 'Arjuna 2',
                    'online': False,
                    'soft_killed': False,
                    'status': 'OFF',  # 'OFF' | 'IDLE' | 'ENGAGED'
                    'power_status': 'OFF',  # 'ON' | 'OFF'
                    'operational_status': 'OFF',  # 'OFF' | 'IDLE' | 'ENGAGED'
                    'status_color': 'grey',  # Grey for OFF, Green for IDLE, Red for ENGAGED
                    'status_display': 'OFF',
                    'status_description': 'Switched Off',
                    'battery_pct': None,  # None means not measured (NO fake values!)
                    'battery_override': None,
                    'battery_fraction': 1.0,
                    'battery_multiplier': 1,  # 0 when battery < 10%, 1 when >= 10%
                    'm_variable': 1,  # variable m: 0 when battery < 10%, 1 when >= 10%
                    'old_bid': None,
                    'enhanced_bid': None,
                    'battery_status': 'offline',  # 'offline' | 'critical' | 'low' | 'normal'
                    'is_eligible': True,
                    'position': None,  # {'x': float, 'y': float} from amcl_pose, or None
                    'position_override': None,
                    'comms_degrade': {'drop_prob': 0.0, 'delay_sec': 0.0},
                    'last_heartbeat': 0.0,
                    'active_task': None,
                    'failure_count': 0,
                    'live_bid_params': None,
                    'last_submitted_bid': None,
                    'last_breakdown': None,
                }
                for rid in self.fleet_robot_ids
            },
            'tasks': {},  # tid -> task record
            'comparison_table': [],  # Current session task comparison records (empty by default)
            'historical_comparison_table': [],  # All previous bidding records and comparisons from logs
            'formula_comparison_table': [],  # list of Old Formula vs Enhanced Formula comparative rows
            'fault_timeline': None,  # latest real fault event record
            'events_log': [],
        }

        # Subscriptions
        for rid in self.fleet_robot_ids:
            # Heartbeats
            self.create_subscription(
                String, f'/fleet/heartbeat/{rid}',
                lambda msg, r=rid: self._heartbeat_cb(msg, r), 10
            )
            # Map-frame Pose from AMCL
            self.create_subscription(
                PoseWithCovarianceStamped, f'/{rid}/amcl_pose',
                lambda msg, r=rid: self._amcl_pose_cb(msg, r), 10
            )
            # Wheel Odometry (as pose fallback)
            self.create_subscription(
                Odometry, f'/{rid}/wheel/odom',
                lambda msg, r=rid: self._odom_cb(msg, r), 10
            )
            # Battery state (optional real topic)
            self.create_subscription(
                BatteryState, f'/{rid}/battery_state',
                lambda msg, r=rid: self._battery_cb(msg, r), 10
            )

        # Fleet coordination topics
        self.create_subscription(String, '/fleet/mode', self._mode_cb, 10)
        self.create_subscription(String, '/fleet/centralized_master', self._master_cb, 10)
        self.create_subscription(String, '/fleet/task_announcement', self._announcement_cb, 10)
        self.create_subscription(String, '/fleet/task_bids', self._bid_cb, 10)
        self.create_subscription(String, '/fleet/task_claims', self._claim_cb, 10)
        self.create_subscription(String, '/fleet/task_completion', self._completion_cb, 10)
        self.create_subscription(String, '/fleet/robot_failure', self._failure_cb, 10)

        # Command Publishers
        self.pub_mode = self.create_publisher(String, '/fleet/mode', 10)
        self.pub_master = self.create_publisher(String, '/fleet/centralized_master', 10)
        self.pub_stop_all = self.create_publisher(String, '/fleet/stop_all', 10)
        self.pub_announcement = self.create_publisher(String, '/fleet/task_announcement', 10)

        self.pub_soft_kill = {
            rid: self.create_publisher(String, f'/fleet/soft_kill/{rid}', 10)
            for rid in self.fleet_robot_ids
        }
        self.pub_override = {
            rid: self.create_publisher(String, f'/fleet/override/{rid}', 10)
            for rid in self.fleet_robot_ids
        }
        self.pub_comms_degrade = {
            rid: self.create_publisher(String, f'/fleet/comms_degrade/{rid}', 10)
            for rid in self.fleet_robot_ids
        }

        # Maintenance Odometer & Runtime Tracker
        self.maintenance_file = self.ws_root / 'maintenance_tracker.json'
        self.prev_positions = {rid: None for rid in self.fleet_robot_ids}
        self.last_maint_alert_state = {rid: False for rid in self.fleet_robot_ids}
        self._init_maintenance_tracker()

        # Periodic watchdog to derive online status from heartbeat age
        self.create_timer(0.5, self._check_heartbeats)

        # Periodic publisher to keep all fleet nodes synchronized with current mode and master
        self.create_timer(1.0, self._broadcast_fleet_state)

        # Periodic flush of maintenance odometer to disk
        self.create_timer(5.0, self._save_maintenance)

        # Preload task history and fault log
        self._load_logs()

        self._add_event("Server initialized. Telemetry and history loaded.", "control")

        self.get_logger().info("=" * 60)
        self.get_logger().info(f"TerrainFleet Dashboard Server live on port {self.port}")
        self.get_logger().info(f"Workspace root detected: {self.ws_root}")
        self.get_logger().info(f"Serving web directory: {self.web_dir}")
        self.get_logger().info("=" * 60)

    def _broadcast_fleet_state(self):
        """Continuously broadcasts fleet mode and master so newly started nodes immediately sync."""
        with self.state_lock:
            mode = self.state.get('mode', 'decentralized')
            master = self.state.get('centralized_master', 'arjuna_1')
        msg_m = String()
        msg_m.data = mode
        self.pub_mode.publish(msg_m)
        msg_c = String()
        msg_c.data = master
        self.pub_master.publish(msg_c)

    def _load_logs(self):
        """Loads tasks and fault history from disk so web dashboard is immediately populated."""
        ws_root = self.ws_root

        # 1. Load task list from tasks_setA.csv
        task_csv = ws_root / 'tasks_setA.csv'
        if task_csv.exists():
            try:
                with open(task_csv, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        tid = row.get('task_id', '').strip()
                        if tid and tid not in self.state['tasks']:
                            self.state['tasks'][tid] = {
                                'task_id': tid,
                                'x': round(float(row.get('x', 0.0)), 2),
                                'y': round(float(row.get('y', 0.0)), 2),
                                'heading': round(float(row.get('heading', 0.0)), 2),
                                'status': 'unannounced',
                                'winner': None,
                                'bids': {},
                                'bid_details': {},
                                'duration': None,
                                'distance': None,
                                'is_reauction': False,
                                'announced_time': 0.0,
                                'completed_time': None,
                            }
            except Exception as e:
                self.get_logger().warn(f"Failed to load tasks_setA.csv: {e}")

        # 2. Update with auction_log.csv and build dynamic task comparison table
        auc_csv = ws_root / 'auction_log.csv'
        if auc_csv.exists():
            try:
                comp_map = {}
                with open(auc_csv, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        tid = row.get('task_id', '').strip()
                        if not tid:
                            continue
                        all_bids_str = row.get('all_bids_json', '').strip()
                        winner = row.get('winner', '').strip()
                        is_reauct = (row.get('is_reauction', '').strip() == 'True')
                        ts = float(row.get('timestamp') or 0.0)

                        bids = {}
                        if all_bids_str:
                            try:
                                bids = json.loads(all_bids_str)
                            except Exception:
                                bids = {}

                        if tid not in self.state['tasks']:
                            self.state['tasks'][tid] = {
                                'task_id': tid,
                                'x': round(float(row.get('task_x') or 0.0), 2),
                                'y': round(float(row.get('task_y') or 0.0), 2),
                                'heading': 0.0,
                                'status': 'done' if succ_val == 'True' else ('failed' if succ_val == 'False' else 'historical'),
                                'winner': None,
                                'bids': {},
                                'bid_details': {},
                                'duration': None,
                                'distance': None,
                                'is_reauction': is_reauct,
                                'announced_time': ts,
                                'completed_time': None,
                            }
                        t = self.state['tasks'][tid]
                        if winner:
                            t['winner'] = winner
                        if bids:
                            # Keep all bids received across rounds
                            t['bids'].update(bids)
                            if 'bid_details' not in t:
                                t['bid_details'] = {}
                            for rk, bval in bids.items():
                                t['bid_details'][rk] = {
                                    'bid': round(float(bval), 3),
                                    'battery_multiplier': 0 if float(bval) == 0.0 else 1,
                                    'is_eligible': float(bval) > 0.0,
                                    'base_cost': round(float(bval), 3),
                                }

                        # Check for task completion
                        succ_val = row.get('nav_success', '').strip()
                        if succ_val != '':
                            t['status'] = 'done' if succ_val == 'True' else 'failed'
                            if row.get('nav_duration_s'):
                                t['duration'] = round(float(row['nav_duration_s']), 2)
                            if row.get('distance_traveled_m'):
                                t['distance'] = round(float(row['distance_traveled_m']), 2)

                        # If bids and winner exist, update comparison record
                        if bids and winner:
                            bid1 = bids.get('arjuna_1')
                            bid2 = bids.get('arjuna_2')
                            b1_val = round(float(bid1), 3) if bid1 is not None else None
                            b2_val = round(float(bid2), 3) if bid2 is not None else None

                            diff = None
                            if b1_val is not None and b2_val is not None:
                                diff = round(abs(b1_val - b2_val), 3)

                            t_num = tid.lstrip('T').lstrip('0')
                            t_disp = f"Task {t_num}" if t_num else tid
                            if is_reauct:
                                t_disp += " (Re-Auction)"

                            w_disp = 'Arjuna 1' if winner == 'arjuna_1' else ('Arjuna 2' if winner == 'arjuna_2' else winner)

                            comp_key = f"{tid}_{is_reauct}"
                            comp_map[comp_key] = {
                                'task_id': tid,
                                'task_display': t_disp,
                                'bid_arjuna_1': b1_val,
                                'bid_arjuna_2': b2_val,
                                'winner': winner,
                                'winner_display': w_disp,
                                'difference': diff,
                                'is_reauction': is_reauct,
                                'timestamp': ts
                            }

                        if not hasattr(self, '_seen_auc_events'):
                            self._seen_auc_events = set()

                        ts_str = row.get('timestamp', '')
                        if succ_val != '':
                            key = f"comp_{tid}_{ts_str}"
                            if key not in self._seen_auc_events:
                                self._seen_auc_events.add(key)
                                succ = (succ_val == 'True')
                                dur = round(float(row.get('nav_duration_s') or 0.0), 1)
                                tag = "SUCCESS" if succ else "FAILED"
                                self._add_event(f"Task {tid} execution by {t.get('winner', 'robot')}: {tag} ({dur}s)", "auction" if succ else "fault")
                        elif row.get('all_bids_json') and row.get('winner'):
                            key = f"bid_{tid}_{ts_str}"
                            if key not in self._seen_auc_events:
                                self._seen_auc_events.add(key)
                                bids_txt = ", ".join([f"{k}:{v}" for k, v in t.get('bids', {}).items()])
                                self._add_event(f"Task {tid} awarded to {t['winner']} (Bids: {bids_txt})", "auction")

                # Populate historical_comparison_table with all previous records from disk (for Logs tab)
                if comp_map:
                    self.state['historical_comparison_table'] = sorted(
                        comp_map.values(),
                        key=lambda x: (x.get('timestamp') or 0.0),
                        reverse=True
                    )
            except Exception as e:
                self.get_logger().warn(f"Failed to load auction_log.csv: {e}")

        # 3. Load latest fault from fault_log.csv
        fault_csv = ws_root / 'fault_log.csv'
        if fault_csv.exists():
            try:
                with open(fault_csv, 'r') as f:
                    rows = list(csv.DictReader(f))
                    if rows:
                        last_row = rows[-1]
                        self.state['fault_timeline'] = {
                            't_fault': float(last_row.get('t_fault') or 0.0),
                            'failed_robot_id': last_row.get('failed_robot_id'),
                            'detected_by': last_row.get('detected_by'),
                            'fault_type': last_row.get('fault_type'),
                            'original_task_id': last_row.get('task_id'),
                            'det_elapsed': float(last_row.get('detection_latency_s') or 0.0),
                            'reann_elapsed': float(last_row.get('reannounce_latency_s') or 0.0) if last_row.get('reannounce_latency_s') else None,
                            'rewin_elapsed': float(last_row.get('rewon_latency_s') or 0.0) if last_row.get('rewon_latency_s') else None,
                            'comp_elapsed': float(last_row.get('total_recovery_time_s') or 0.0) if last_row.get('total_recovery_time_s') else None,
                            'total_recovery_s': float(last_row.get('total_recovery_time_s') or 0.0) if last_row.get('total_recovery_time_s') else None,
                            'survivor_robot_id': last_row.get('survivor_robot_id'),
                        }
            except Exception as e:
                self.get_logger().warn(f"Failed to load fault_log.csv: {e}")

    # --- Callbacks ---
    def _heartbeat_cb(self, msg: String, rid: str):
        now = time.time()
        with self.state_lock:
            if rid in self.state['robots']:
                rdata = self.state['robots'][rid]
                rdata['last_heartbeat'] = now
                if not rdata['soft_killed']:
                    rdata['online'] = True
                    rdata['status'] = 'online'

    def _amcl_pose_cb(self, msg: PoseWithCovarianceStamped, rid: str):
        px = float(msg.pose.pose.position.x)
        py = float(msg.pose.pose.position.y)
        self._record_position_movement(rid, px, py)
        with self.state_lock:
            if rid in self.state['robots']:
                self.state['robots'][rid]['position'] = {
                    'x': round(px, 2),
                    'y': round(py, 2)
                }

    def _odom_cb(self, msg: Odometry, rid: str):
        px = float(msg.pose.pose.position.x)
        py = float(msg.pose.pose.position.y)
        with self.state_lock:
            if rid in self.state['robots']:
                rdata = self.state['robots'][rid]
                # Fallback to wheel odometry if AMCL is not yet localized
                if rdata['position'] is None:
                    self._record_position_movement(rid, px, py)
                    rdata['position'] = {
                        'x': round(px, 2),
                        'y': round(py, 2)
                    }

    def _battery_cb(self, msg: BatteryState, rid: str):
        with self.state_lock:
            if rid in self.state['robots'] and msg.percentage >= 0.0:
                pct = msg.percentage if msg.percentage <= 1.0 else (msg.percentage / 100.0)
                self.state['robots'][rid]['battery_pct'] = round(pct * 100.0, 1)

    def _mode_cb(self, msg: String):
        with self.state_lock:
            new_mode = msg.data.strip()
            if new_mode in ('decentralized', 'centralized'):
                self.state['mode'] = new_mode

    def _master_cb(self, msg: String):
        with self.state_lock:
            self.state['centralized_master'] = msg.data.strip()

    def _announcement_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            tid = str(data.get('task_id', '')).strip()
            if not tid:
                return

            is_reauction = bool(data.get('is_reauction', False))
            now = time.time()

            with self.state_lock:
                self.state['tasks'][tid] = {
                    'task_id': tid,
                    'x': round(float(data.get('x', 0.0)), 2),
                    'y': round(float(data.get('y', 0.0)), 2),
                    'heading': round(float(data.get('heading', 0.0)), 2),
                    'status': 're-auctioned' if is_reauction else 'announced',
                    'winner': None,
                    'bids': {},
                    'duration': None,
                    'distance': None,
                    'is_reauction': is_reauction,
                    'announced_time': now,
                    'completed_time': None,
                }

                # Update fault timeline if re-auction is triggered
                if is_reauction and self.state['fault_timeline']:
                    ft = self.state['fault_timeline']
                    ft['t_reannounced'] = now
                    ft['reann_elapsed'] = round(now - ft['t_fault'], 2)
                    ft['reannounced_task_id'] = tid

                re_txt = " (RE-AUCTION)" if is_reauction else ""
                self._add_event(f"Task {tid} announced at ({data.get('x')}, {data.get('y')}){re_txt}", "auction")
        except Exception:
            pass

    def _bid_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            tid = str(data.get('task_id', '')).strip()
            rid = str(data.get('robot_id', '')).strip()
            bid_val = float(data.get('bid', 0.0))
            breakdown = data.get('breakdown', {})

            with self.state_lock:
                if tid in self.state['tasks']:
                    t = self.state['tasks'][tid]
                    t['bids'][rid] = round(bid_val, 2)
                    if 'bid_details' not in t:
                        t['bid_details'] = {}
                    
                    eff_mult = breakdown.get('battery_multiplier')
                    if eff_mult is None:
                        eff_mult = data.get('battery_multiplier', 0 if (data.get('battery', 1.0) or 1.0) < 0.10 else 1)

                    t['bid_details'][rid] = {
                        'bid': round(bid_val, 3),
                        'battery': breakdown.get('battery', data.get('battery')),
                        'battery_multiplier': int(eff_mult),
                        'distance': breakdown.get('distance', data.get('distance')),
                        'dist_cost': breakdown.get('dist_cost'),
                        'bat_cost': breakdown.get('bat_cost'),
                        'fail_cost': breakdown.get('fail_cost'),
                        'base_cost': breakdown.get('base_cost', data.get('base_cost', bid_val)),
                        'w_distance': breakdown.get('w_distance', 1.0),
                        'w_battery': breakdown.get('w_battery', 5.0),
                        'w_failure': breakdown.get('w_failure', 2.0),
                        'failures': breakdown.get('failures', 0),
                        'busy_penalty': breakdown.get('busy_penalty', 0.0),
                        'is_eligible': breakdown.get('is_eligible', bid_val > 0.0)
                    }
                    if t['status'] == 'announced':
                        t['status'] = 'bidding'

                if rid in self.state['robots']:
                    self.state['robots'][rid]['last_bid'] = round(bid_val, 3)
                    self.state['robots'][rid]['last_submitted_bid'] = {
                        'task_id': tid,
                        'bid': round(bid_val, 3),
                        'won': None,
                        'timestamp': time.time()
                    }
                    if breakdown:
                        self.state['robots'][rid]['last_breakdown'] = breakdown

                self._sync_comparison_table_row(tid)
        except Exception:
            pass

    def _sync_comparison_table_row(self, tid: str):
        if tid not in self.state['tasks']:
            return
        t = self.state['tasks'][tid]
        bids = t.get('bids', {})
        b1 = bids.get('arjuna_1')
        b2 = bids.get('arjuna_2')
        b1_val = round(float(b1), 3) if b1 is not None else None
        b2_val = round(float(b2), 3) if b2 is not None else None
        diff = round(abs(b1_val - b2_val), 3) if (b1_val is not None and b2_val is not None) else None
        winner = t.get('winner')
        winner_disp = 'Arjuna 1' if winner == 'arjuna_1' else ('Arjuna 2' if winner == 'arjuna_2' else (winner or '--'))
        is_reauct = bool(t.get('is_reauction', False))
        t_num = tid.lstrip('T').lstrip('0')
        t_disp = f"Task {t_num}" if t_num else tid
        if is_reauct:
            t_disp += " (Re-Auction)"

        # Only display in comparison table when actual live bids or winner exist
        if b1_val is None and b2_val is None and winner is None:
            return

        found = False
        for row in self.state['comparison_table']:
            if row.get('task_id') == tid and row.get('is_reauction') == is_reauct:
                row['bid_arjuna_1'] = b1_val
                row['bid_arjuna_2'] = b2_val
                row['winner'] = winner
                row['winner_display'] = winner_disp
                row['difference'] = diff
                found = True
                break
        if not found:
            self.state['comparison_table'].append({
                'task_id': tid,
                'task_display': t_disp,
                'bid_arjuna_1': b1_val,
                'bid_arjuna_2': b2_val,
                'winner': winner,
                'winner_display': winner_disp,
                'difference': diff,
                'is_reauction': is_reauct,
                'timestamp': time.time(),
                'is_live_session': True
            })
            self.state['comparison_table'].sort(key=lambda x: (x['task_id'], x['is_reauction']))

        # Also mirror newly generated records into historical_comparison_table for Logs
        found_hist = False
        for row in self.state['historical_comparison_table']:
            if row.get('task_id') == tid and row.get('is_reauction') == is_reauct:
                row['bid_arjuna_1'] = b1_val
                row['bid_arjuna_2'] = b2_val
                row['winner'] = winner
                row['winner_display'] = winner_disp
                row['difference'] = diff
                found_hist = True
                break
        if not found_hist:
            self.state['historical_comparison_table'].insert(0, {
                'task_id': tid,
                'task_display': t_disp,
                'bid_arjuna_1': b1_val,
                'bid_arjuna_2': b2_val,
                'winner': winner,
                'winner_display': winner_disp,
                'difference': diff,
                'is_reauction': is_reauct,
                'timestamp': time.time()
            })

    def _claim_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            tid = str(data.get('task_id', '')).strip()
            rid = str(data.get('robot_id', '')).strip()
            now = time.time()

            with self.state_lock:
                if rid in self.state['robots']:
                    self.state['robots'][rid]['active_task'] = tid
                    if self.state['robots'][rid].get('last_submitted_bid'):
                        if self.state['robots'][rid]['last_submitted_bid'].get('task_id') == tid:
                            self.state['robots'][rid]['last_submitted_bid']['won'] = True

                for other_rid in self.fleet_robot_ids:
                    if other_rid != rid and other_rid in self.state['robots']:
                        if self.state['robots'][other_rid].get('last_submitted_bid'):
                            if self.state['robots'][other_rid]['last_submitted_bid'].get('task_id') == tid:
                                self.state['robots'][other_rid]['last_submitted_bid']['won'] = False

                if tid in self.state['tasks']:
                    t = self.state['tasks'][tid]
                    t['winner'] = rid
                    t['status'] = 'running'

                self._sync_comparison_table_row(tid)

                # Update fault timeline if re-won
                if self.state['fault_timeline'] and self.state['fault_timeline'].get('reannounced_task_id') == tid:
                    ft = self.state['fault_timeline']
                    ft['t_rewon'] = now
                    ft['rewin_elapsed'] = round(now - ft['t_fault'], 2)
                    ft['survivor_robot_id'] = rid

                self._add_event(f"Task {tid} claimed by {rid}", "auction")
        except Exception:
            pass

    def _completion_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            tid = str(data.get('task_id', '')).strip()
            rid = str(data.get('robot_id', '')).strip()
            success = bool(data.get('success', False))
            dur = float(data.get('duration', 0.0))
            dist = float(data.get('distance', 0.0))
            now = time.time()

            with self.state_lock:
                # Clear active task on completing robot
                if rid in self.state['robots']:
                    if self.state['robots'][rid]['active_task'] == tid:
                        self.state['robots'][rid]['active_task'] = None

                if tid in self.state['tasks']:
                    t = self.state['tasks'][tid]
                    t['status'] = 'done' if success else 'failed'
                    t['duration'] = round(dur, 2)
                    t['distance'] = round(dist, 2)
                    t['completed_time'] = now

                # Update fault timeline if completed
                if self.state['fault_timeline'] and self.state['fault_timeline'].get('reannounced_task_id') == tid:
                    ft = self.state['fault_timeline']
                    ft['t_completed'] = now
                    ft['comp_elapsed'] = round(now - ft['t_fault'], 2)
                    ft['total_recovery_s'] = round(now - ft['t_fault'], 2)

                status_str = "completed successfully" if success else "failed"
                self._add_event(f"Task {tid} {status_str} by {rid} in {dur:.1f}s ({dist:.1f}m)", "auction")

            if dist > 0.0:
                self._add_distance(rid, dist)
            if dur > 0.0:
                self._add_runtime_tick(rid, dur)
        except Exception:
            pass

    def _failure_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            failed_id = str(data.get('failed_robot_id', '')).strip()
            detected_by = str(data.get('detected_by', '')).strip()
            det_ts = float(data.get('detection_timestamp', time.time()))
            last_seen_ts = float(data.get('last_seen_timestamp', det_ts - 3.0))
            fault_type = str(data.get('fault_type', ''))

            with self.state_lock:
                if failed_id in self.state['robots']:
                    rdata = self.state['robots'][failed_id]
                    rdata['online'] = False
                    if not rdata['soft_killed']:
                        rdata['status'] = 'silent'
                    if not fault_type:
                        fault_type = 'simulated' if rdata['soft_killed'] else 'physical'
                    abandoned = rdata['active_task']
                    rdata['active_task'] = None
                else:
                    abandoned = None

                # Record real fault timeline
                t_fault = last_seen_ts if last_seen_ts > 0 else (det_ts - 3.0)
                self.state['fault_timeline'] = {
                    'failed_robot_id': failed_id,
                    'detected_by': detected_by,
                    'fault_type': fault_type,
                    'original_task_id': abandoned,
                    'reannounced_task_id': None,
                    'survivor_robot_id': None,
                    't_fault': round(t_fault, 2),
                    't_detected': round(det_ts, 2),
                    'det_elapsed': round(det_ts - t_fault, 2),
                    't_reannounced': None,
                    'reann_elapsed': None,
                    't_rewon': None,
                    'rewin_elapsed': None,
                    't_completed': None,
                    'comp_elapsed': None,
                    'total_recovery_s': None,
                }

                type_label = "Simulated fault" if fault_type == 'simulated' else "Physical power-off"
                self._add_event(f"Fault detected: {failed_id} silent! ({type_label}, detected by {detected_by})", "fault")
        except Exception:
            pass

    def _check_heartbeats(self):
        now = time.time()
        if not hasattr(self, '_last_log_reload') or (now - self._last_log_reload > 2.0):
            self._last_log_reload = now
            self._load_logs()

        with self.state_lock:
            self.state['server_time'] = now

            # Find target task for active bidding if any is currently announced or bidding
            target_task = None
            if self.state['tasks']:
                for t in self.state['tasks'].values():
                    if t.get('status') in ('announced', 'bidding', 're-auctioned'):
                        target_task = t
                        break

            tx = float(target_task['x']) if target_task and 'x' in target_task else None
            ty = float(target_task['y']) if target_task and 'y' in target_task else None
            tid = target_task.get('task_id') if target_task else None

            for rid, rdata in self.state['robots'].items():
                if rdata['soft_killed']:
                    rdata['status'] = 'OFF'
                    rdata['online'] = False
                elif rdata['last_heartbeat'] > 0 and (now - rdata['last_heartbeat'] <= 3.5):
                    rdata['status'] = 'online'
                    rdata['online'] = True
                    self._add_runtime_tick(rid, 0.5)
                else:
                    rdata['status'] = 'OFF'
                    rdata['online'] = False

                # Requirement 1:
                # - Grey: When the robot is switched off.
                # - Green: When the robot is switched on but has not been assigned any task (idle).
                # - Red: When the robot is switched on and actively performing a task (engaged).
                is_online = bool(rdata['online'] and not rdata['soft_killed'])
                active_task = rdata.get('active_task')

                if not is_online:
                    rdata['power_status'] = 'OFF'
                    rdata['operational_status'] = 'OFF'
                    rdata['status'] = 'OFF'
                    rdata['status_color'] = 'grey'  # Grey when switched off
                    rdata['status_display'] = 'OFF'
                    rdata['status_description'] = 'Switched Off'
                elif not active_task:
                    rdata['power_status'] = 'ON'
                    rdata['operational_status'] = 'IDLE'
                    rdata['status'] = 'IDLE'
                    rdata['status_color'] = 'green'  # Green when switched on but not assigned any task
                    rdata['status_display'] = 'IDLE'
                    rdata['status_description'] = 'Switched On • Idle'
                else:
                    rdata['power_status'] = 'ON'
                    rdata['operational_status'] = 'ENGAGED'
                    rdata['status'] = 'ENGAGED'
                    rdata['status_color'] = 'red'    # Red when switched on and actively performing a task
                    rdata['status_display'] = 'ENGAGED'
                    rdata['status_description'] = f'Switched On • Engaged ({active_task})'

                rdata['display_name'] = 'Arjuna 1' if rid == 'arjuna_1' else 'Arjuna 2'

                # Effective battery percentage (from real topic or test override, NO fake defaults)
                bat_fraction = None
                if rdata['battery_override'] is not None:
                    eff_pct = float(rdata['battery_override'])
                    if eff_pct <= 1.0:
                        eff_pct *= 100.0
                    rdata['battery_source'] = 'override'
                elif rdata['battery_pct'] is not None:
                    eff_pct = float(rdata['battery_pct'])
                    rdata['battery_source'] = 'live_sensor'
                else:
                    eff_pct = None
                    rdata['battery_source'] = 'none'

                # Variable m: if battery < 10% then m = 0, otherwise m = 1
                if eff_pct is not None:
                    rdata['effective_battery_pct'] = round(eff_pct, 1)
                    bat_fraction = max(0.0, min(1.0, eff_pct / 100.0))
                    rdata['battery_fraction'] = round(bat_fraction, 3)
                    m = 0 if eff_pct < 10.0 else 1
                    rdata['battery_multiplier'] = m
                    rdata['m_variable'] = m
                    rdata['is_eligible'] = (m > 0)
                    rdata['battery_status'] = 'critical' if eff_pct < 10.0 else ('low' if eff_pct < 25.0 else 'normal')
                else:
                    bat_fraction = None
                    rdata['effective_battery_pct'] = None
                    rdata['battery_fraction'] = None
                    rdata['battery_multiplier'] = 1
                    rdata['m_variable'] = 1
                    rdata['is_eligible'] = True
                    rdata['battery_status'] = 'offline'

                # Robot position: from override, AMCL pose, wheel odom, or calibrated home position
                pos_source = 'live'
                if rdata['position_override'] is not None:
                    rx, ry = float(rdata['position_override']['x']), float(rdata['position_override']['y'])
                    pos_source = 'override'
                elif rdata['position'] is not None:
                    rx, ry = float(rdata['position']['x']), float(rdata['position']['y'])
                    pos_source = 'live'
                else:
                    home = self.home_positions.get(rid, {'x': 0.0, 'y': 0.0})
                    rx, ry = float(home['x']), float(home['y'])
                    pos_source = 'calibrated_home'

                # Determine target task for bidding calculation
                curr_task_obj = None
                if active_task and active_task in self.state['tasks']:
                    curr_task_obj = self.state['tasks'][active_task]
                elif target_task:
                    curr_task_obj = target_task

                w_d = 1.0
                w_b = 5.0
                w_f = 2.0
                bat_for_calc = bat_fraction if bat_fraction is not None else 1.0
                bat_cost = w_b * (1.0 - bat_for_calc)
                fail_cost = w_f * rdata.get('failure_count', 0)
                busy_cost = 1000.0 if active_task else 0.0
                reauct_cost = 0.0
                m = rdata.get('m_variable', 1)

                old_formula_str = "Bid_old = (w_distance × D) + (w_battery × (1 - B)) + (w_failure × F) + P_busy + P_reauction"
                enhanced_formula_str = "Bid_enhanced = m × [ (w_distance × D) + (w_battery × (1 - B)) + (w_failure × F) + P_busy + P_reauction ]"

                if curr_task_obj is not None and 'x' in curr_task_obj and 'y' in curr_task_obj:
                    tx_eff = float(curr_task_obj['x'])
                    ty_eff = float(curr_task_obj['y'])
                    tid_eff = curr_task_obj.get('task_id', 'Active Task')
                    dx = tx_eff - rx
                    dy = ty_eff - ry
                    dist = math.sqrt(dx * dx + dy * dy)
                    dist_cost = w_d * dist
                    base_cost = dist_cost + bat_cost + fail_cost + busy_cost + reauct_cost
                    final_bid = m * base_cost
                    old_b_val = round(base_cost, 3)
                    enh_b_val = round(final_bid, 3)
                    calc_steps_str = (
                        f"Bid_enhanced = m × Bid_old = {m} × [ ({w_d:.1f} × {dist:.3f}) + ({w_b:.1f} × (1 - {bat_for_calc:.2f})) "
                        f"+ ({w_f:.1f} × {rdata.get('failure_count', 0)}) + {busy_cost:.1f} + {reauct_cost:.1f} ] "
                        f"= {m} × [ {dist_cost:.3f} + {bat_cost:.3f} + {fail_cost:.3f} + {busy_cost:.1f} + {reauct_cost:.1f} ] "
                        f"= {m} × {base_cost:.3f} = {final_bid:.3f}"
                    )
                else:
                    tx_eff = None
                    ty_eff = None
                    tid_eff = None
                    dist = None
                    dist_cost = None
                    base_cost = None
                    final_bid = None
                    old_b_val = None
                    enh_b_val = None
                    calc_steps_str = "No active task auction underway. Robot is standing by."

                rdata['old_bid'] = old_b_val
                rdata['enhanced_bid'] = enh_b_val
                rdata['live_bid_params'] = {
                    'has_active_task': (curr_task_obj is not None),
                    'target_task_id': tid_eff,
                    'target_x': round(tx_eff, 2) if tx_eff is not None else None,
                    'target_y': round(ty_eff, 2) if ty_eff is not None else None,
                    'robot_x': round(rx, 2),
                    'robot_y': round(ry, 2),
                    'position_source': pos_source,
                    'distance': round(dist, 3) if dist is not None else None,
                    'w_distance': w_d,
                    'dist_cost': round(dist_cost, 3) if dist_cost is not None else None,
                    'battery_fraction': round(bat_fraction, 3) if bat_fraction is not None else None,
                    'battery_pct': round(eff_pct, 1) if eff_pct is not None else None,
                    'w_battery': w_b,
                    'bat_cost': round(bat_cost, 3),
                    'w_failure': w_f,
                    'failures': rdata.get('failure_count', 0),
                    'fail_cost': round(fail_cost, 2),
                    'busy_penalty': busy_cost,
                    'reauct_penalty': reauct_cost,
                    'base_cost': old_b_val,
                    'old_bid': old_b_val,
                    'm_variable': m,
                    'battery_multiplier': m,
                    'final_bid': enh_b_val,
                    'enhanced_bid': enh_b_val,
                    'old_formula': old_formula_str,
                    'enhanced_formula': enhanced_formula_str,
                    'formula_definition': enhanced_formula_str,
                    'calculated_step_by_step': calc_steps_str,
                    'is_eligible': rdata['is_eligible'],
                    'status_note': 'Eligible bidder (m = 1)' if rdata['is_eligible'] else 'Disqualified: Battery < 10% (m = 0)'
                }

            # Build Comparative Table of Old Bid Formula vs. Enhanced Bid Formula (Live Fleet Only)
            comp_rows = []
            for rid in ('arjuna_1', 'arjuna_2'):
                if rid in self.state['robots']:
                    r = self.state['robots'][rid]
                    p = r.get('live_bid_params') or {}
                    bat_val = r.get('effective_battery_pct')
                    m_val = p.get('m_variable', 1)
                    old_b = p.get('old_bid')
                    enh_b = p.get('enhanced_bid')
                    is_off = (r.get('power_status') == 'OFF')
                    has_active = p.get('has_active_task', False)

                    if bat_val is not None:
                        bat_disp = f"{bat_val:.1f}%"
                    else:
                        bat_disp = "-- Offline"

                    if m_val == 0:
                        impact = "Disqualified: Bid zeroes to 0.000 (Prevents mid-mission stall)"
                        badge_type = "disqualified"
                    elif is_off:
                        impact = "Switched Off: Standing by in dock"
                        badge_type = "offline"
                    elif not has_active:
                        impact = "Eligible (m = 1): Awaiting task auction"
                        badge_type = "eligible"
                    else:
                        impact = "Active: Bid submitted for auction"
                        badge_type = "eligible"

                    comp_rows.append({
                        'category': 'live',
                        'target': r.get('display_name', rid),
                        'robot_id': rid,
                        'battery_display': bat_disp,
                        'battery_pct': bat_val,
                        'm_variable': m_val,
                        'old_bid': old_b,
                        'enhanced_bid': enh_b,
                        'difference': round(enh_b - old_b, 3) if (enh_b is not None and old_b is not None) else None,
                        'status_impact': impact,
                        'badge_type': badge_type
                    })

            self.state['formula_comparison_table'] = comp_rows

    def _add_event(self, text: str, severity: str = 'info'):
        timestamp = time.strftime('%H:%M:%S')
        with self.state_lock:
            self.state['events_log'].insert(0, {
                'timestamp': timestamp,
                'text': text,
                'severity': severity,  # 'info' | 'auction' | 'fault' | 'control' | 'maintenance'
            })
            if len(self.state['events_log']) > 250:
                self.state['events_log'].pop()

    # --- Maintenance & Odometer System ---
    def _init_maintenance_tracker(self):
        default_data = {
            'thresholds': {
                'distance_m': 500.0,
                'runtime_s': 180000.0,
                'tasks': 25,
            },
            'robots': {
                'arjuna_1': {
                    'total_distance_m': 0.0,
                    'service_distance_m': 0.0,
                    'total_runtime_s': 0.0,
                    'service_runtime_s': 0.0,
                    'last_service_time': 'None',
                    'service_count': 0,
                },
                'arjuna_2': {
                    'total_distance_m': 0.0,
                    'service_distance_m': 0.0,
                    'total_runtime_s': 0.0,
                    'service_runtime_s': 0.0,
                    'last_service_time': 'None',
                    'service_count': 0,
                }
            },
            'history': []
        }

        if self.maintenance_file.exists():
            try:
                with open(self.maintenance_file, 'r') as f:
                    loaded = json.load(f)
                    if 'thresholds' in loaded and 'robots' in loaded:
                        default_data['thresholds'].update(loaded['thresholds'])
                        for rid in self.fleet_robot_ids:
                            if rid in loaded.get('robots', {}):
                                default_data['robots'][rid].update(loaded['robots'][rid])
                        if 'history' in loaded:
                            default_data['history'] = loaded['history']
            except Exception as e:
                self.get_logger().warn(f"Failed loading maintenance_tracker.json: {e}")

        self.maintenance_data = default_data
        self._update_maintenance_state()
        self._save_maintenance()

    def _save_maintenance(self):
        """Flushes maintenance state to disk."""
        try:
            temp_path = self.maintenance_file.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(self.maintenance_data, f, indent=2)
            temp_path.replace(self.maintenance_file)
        except Exception as e:
            self.get_logger().warn(f"Failed saving maintenance_tracker.json: {e}")

    def _record_position_movement(self, rid: str, x: float, y: float):
        prev = self.prev_positions.get(rid)
        if prev is not None:
            dx = x - prev[0]
            dy = y - prev[1]
            dist = math.sqrt(dx * dx + dy * dy)
            if 0.01 <= dist <= 3.0:  # Valid step, ignoring noise or teleport jump
                self._add_distance(rid, dist)
        self.prev_positions[rid] = (x, y)

    def _add_distance(self, rid: str, dist: float):
        if rid in self.maintenance_data['robots']:
            r = self.maintenance_data['robots'][rid]
            r['service_distance_m'] = round(r.get('service_distance_m', 0.0) + dist, 2)
            r['total_distance_m'] = round(r.get('total_distance_m', 0.0) + dist, 2)
            self._update_maintenance_state()

    def _add_runtime_tick(self, rid: str, dt: float):
        if rid in self.maintenance_data['robots']:
            r = self.maintenance_data['robots'][rid]
            r['service_runtime_s'] = round(r.get('service_runtime_s', 0.0) + dt, 1)
            r['total_runtime_s'] = round(r.get('total_runtime_s', 0.0) + dt, 1)
            self._update_maintenance_state()

    def _update_maintenance_state(self):
        thresh_d = float(self.maintenance_data['thresholds'].get('distance_m', 500.0))
        thresh_t = float(self.maintenance_data['thresholds'].get('runtime_s', 180000.0))  # 50 hours default
        thresh_tasks = float(self.maintenance_data['thresholds'].get('tasks', 25.0))

        fleet_tot_dist = 0.0
        fleet_tot_run = 0.0
        any_req = False
        any_soon = False

        robots_status = {}
        for rid in self.fleet_robot_ids:
            r_entry = self.maintenance_data['robots'].setdefault(rid, {
                'total_distance_m': 0.0,
                'service_distance_m': 0.0,
                'total_runtime_s': 0.0,
                'service_runtime_s': 0.0,
                'last_service_time': 'Initial Commissioning',
                'service_count': 0
            })

            s_dist = round(float(r_entry.get('service_distance_m', 0.0)), 2)
            t_dist = round(float(r_entry.get('total_distance_m', 0.0)), 2)
            s_time = round(float(r_entry.get('service_runtime_s', 0.0)), 1)
            t_time = round(float(r_entry.get('total_runtime_s', 0.0)), 1)

            fleet_tot_dist += t_dist
            fleet_tot_run += t_time

            # Calculate total hours and formatted time
            hours_val = round(t_time / 3600.0, 2)
            thresh_hours = round(thresh_t / 3600.0, 1)

            h = int(t_time // 3600)
            m = int((t_time % 3600) // 60)
            s = int(t_time % 60)
            time_worked_fmt = f"{h}h {m:02d}m {s:02d}s"

            # Count completed tasks
            tasks_done = 0
            for t in self.state.get('tasks', {}).values():
                if t.get('winner') == rid and t.get('status') in ('done', 'completed'):
                    tasks_done += 1

            dist_pct = round((s_dist / thresh_d * 100.0) if thresh_d > 0 else 0.0, 1)
            time_pct = round((s_time / thresh_t * 100.0) if thresh_t > 0 else 0.0, 1)
            tasks_pct = round((tasks_done / thresh_tasks * 100.0) if thresh_tasks > 0 else 0.0, 1)

            reasons = []
            if s_time >= thresh_t:
                reasons.append(f"Operating hours threshold exceeded ({hours_val:.2f}h / {thresh_hours:.1f}h)")
            if s_dist >= thresh_d:
                reasons.append(f"Distance threshold exceeded ({s_dist:.1f}m / {thresh_d:.1f}m)")
            if tasks_done >= thresh_tasks:
                reasons.append(f"Completed tasks threshold reached ({tasks_done} / {int(thresh_tasks)} tasks)")

            is_req = (len(reasons) > 0)
            is_soon = (not is_req) and (dist_pct >= 80.0 or time_pct >= 80.0 or tasks_pct >= 80.0)

            if is_req:
                any_req = True
                status = 'required'
                status_label = 'MAINTENANCE REQUIRED'
                status_color = 'red'
                if not self.last_maint_alert_state.get(rid, False):
                    self.last_maint_alert_state[rid] = True
                    self._add_event(f"MAINTENANCE REQUIRED for {rid}: {', '.join(reasons)}", "maintenance")
            elif is_soon:
                any_soon = True
                status = 'due_soon'
                status_label = 'Service Due Soon'
                status_color = 'amber'
                self.last_maint_alert_state[rid] = False
            else:
                status = 'good'
                status_label = 'Healthy (No Maintenance Needed)'
                status_color = 'green'
                self.last_maint_alert_state[rid] = False

            robots_status[rid] = {
                'robot_id': rid,
                'robot_display': 'Arjuna 1' if rid == 'arjuna_1' else 'Arjuna 2',
                'total_hours': hours_val,
                'total_hours_threshold': thresh_hours,
                'total_time_formatted': time_worked_fmt,
                'total_runtime_s': t_time,
                'service_runtime_s': s_time,
                'time_threshold_s': thresh_t,
                'time_pct': time_pct,
                'total_distance_m': t_dist,
                'service_distance_m': s_dist,
                'distance_threshold_m': thresh_d,
                'distance_pct': dist_pct,
                'tasks_completed': tasks_done,
                'tasks_threshold': int(thresh_tasks),
                'tasks_pct': tasks_pct,
                'status': status,
                'status_label': status_label,
                'status_color': status_color,
                'maintenance_required': is_req,
                'maintenance_due_soon': is_soon,
                'reasons': reasons,
                'last_service_time': r_entry.get('last_service_time', 'Initial Commissioning'),
                'service_count': r_entry.get('service_count', 0),
            }

        with self.state_lock:
            self.state['maintenance'] = {
                'thresholds': {
                    'distance_m': thresh_d,
                    'runtime_s': thresh_t,
                    'runtime_hr': round(thresh_t / 3600.0, 1),
                    'tasks': int(thresh_tasks),
                },
                'robots': robots_status,
                'fleet_summary': {
                    'total_distance_m': round(fleet_tot_dist, 2),
                    'total_runtime_s': round(fleet_tot_run, 1),
                    'total_hours': round(fleet_tot_run / 3600.0, 2),
                    'any_maintenance_required': any_req,
                    'any_maintenance_due_soon': any_soon,
                },
                'history': self.maintenance_data.get('history', [])
            }

    def set_maintenance_thresholds(self, distance_m: float, runtime_s: float):
        distance_m = max(1.0, float(distance_m))
        runtime_s = max(10.0, float(runtime_s))
        self.maintenance_data['thresholds']['distance_m'] = distance_m
        self.maintenance_data['thresholds']['runtime_s'] = runtime_s
        self._update_maintenance_state()
        self._save_maintenance()
        self._add_event(f"Maintenance thresholds updated: {distance_m:.1f} m distance, {runtime_s/60.0:.1f} min runtime", "control")

    def reset_maintenance(self, robot_id: str, note: str = ""):
        if robot_id in self.maintenance_data['robots']:
            r_entry = self.maintenance_data['robots'][robot_id]
            prev_d = r_entry.get('service_distance_m', 0.0)
            prev_t = r_entry.get('service_runtime_s', 0.0)
            r_entry['service_distance_m'] = 0.0
            r_entry['service_runtime_s'] = 0.0
            r_entry['service_count'] = r_entry.get('service_count', 0) + 1
            now_str = time.strftime('%Y-%m-%d %H:%M:%S')
            r_entry['last_service_time'] = now_str

            history_record = {
                'timestamp': now_str,
                'robot_id': robot_id,
                'event': f"Service Reset (#{r_entry['service_count']})",
                'distance_at_service_m': round(prev_d, 2),
                'runtime_at_service_s': round(prev_t, 1),
                'note': note or "Standard maintenance checklist completed."
            }
            self.maintenance_data.setdefault('history', []).insert(0, history_record)
            self.last_maint_alert_state[robot_id] = False
            self._update_maintenance_state()
            self._save_maintenance()
            self._add_event(f"Maintenance reset for {robot_id} (Odometer: {prev_d:.1f}m, Runtime: {prev_t/60.0:.1f}m). Service #{r_entry['service_count']} logged.", "maintenance")

    def simulate_maintenance_wear(self, robot_id: str, add_distance_m: float = 0.0, add_runtime_s: float = 0.0):
        if robot_id in self.maintenance_data['robots']:
            r_entry = self.maintenance_data['robots'][robot_id]
            r_entry['service_distance_m'] = max(0.0, r_entry.get('service_distance_m', 0.0) + float(add_distance_m))
            r_entry['total_distance_m'] = max(0.0, r_entry.get('total_distance_m', 0.0) + float(add_distance_m))
            r_entry['service_runtime_s'] = max(0.0, r_entry.get('service_runtime_s', 0.0) + float(add_runtime_s))
            r_entry['total_runtime_s'] = max(0.0, r_entry.get('total_runtime_s', 0.0) + float(add_runtime_s))
            self._update_maintenance_state()
            self._save_maintenance()
            self._add_event(f"Simulated wear added to {robot_id}: +{add_distance_m:.1f}m distance, +{add_runtime_s/60.0:.1f}m runtime", "control")

    def get_all_logs(self) -> dict:
        with self.state_lock:
            events = list(self.state.get('events_log', []))
            tasks = list(self.state.get('tasks', {}).values())
            fault = self.state.get('fault_timeline')
            maintenance = self.state.get('maintenance', {})
            m_history = list(self.maintenance_data.get('history', []))

        ws_root = self.ws_root
        auc_rows = []
        raw_auc = ""
        auc_csv = ws_root / 'auction_log.csv'
        if auc_csv.exists():
            try:
                with open(auc_csv, 'r') as f:
                    raw_auc = f.read()
                with open(auc_csv, 'r') as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        auc_rows.append(r)
            except Exception:
                pass

        fault_rows = []
        raw_fault = ""
        fault_csv = ws_root / 'fault_log.csv'
        if fault_csv.exists():
            try:
                with open(fault_csv, 'r') as f:
                    raw_fault = f.read()
                with open(fault_csv, 'r') as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        fault_rows.append(r)
            except Exception:
                pass

        return {
            'status': 'ok',
            'server_time': time.time(),
            'events_log': events,
            'auction_log_entries': auc_rows,
            'raw_auction_csv': raw_auc,
            'fault_log_entries': fault_rows,
            'raw_fault_csv': raw_fault,
            'maintenance_log_entries': m_history,
            'active_tasks': tasks,
            'fault_timeline': fault,
            'maintenance_summary': maintenance
        }

    # --- Actions ---
    def set_mode(self, mode: str):
        if mode in ('decentralized', 'centralized'):
            with self.state_lock:
                self.state['mode'] = mode
                self._add_event(f"Fleet mode changed to {mode.upper()}", "control")
            msg = String()
            msg.data = mode
            self.pub_mode.publish(msg)

    def set_master(self, master_id: str):
        if master_id in self.fleet_robot_ids:
            with self.state_lock:
                self.state['centralized_master'] = master_id
                self._add_event(f"Centralized baseline master set to {master_id}", "control")
            msg = String()
            msg.data = master_id
            self.pub_master.publish(msg)

    def set_soft_kill(self, robot_id: str, killed: bool):
        if robot_id in self.pub_soft_kill:
            with self.state_lock:
                self.state['robots'][robot_id]['soft_killed'] = killed
                if killed:
                    self.state['robots'][robot_id]['status'] = 'soft_killed'
                    self.state['robots'][robot_id]['online'] = False
                state_str = "simulated fault activated" if killed else "simulated fault cleared"
                self._add_event(f"{robot_id}: {state_str}", "fault" if killed else "control")
            msg = String()
            msg.data = json.dumps({'killed': killed})
            self.pub_soft_kill[robot_id].publish(msg)

    def set_override(self, robot_id: str, payload: dict):
        if robot_id not in self.pub_override:
            return

        ros_payload = {}
        with self.state_lock:
            rdata = self.state['robots'][robot_id]

            # Battery override
            if payload.get('clear_battery', False) or payload.get('reset_all', False):
                rdata['battery_override'] = None
                ros_payload['clear_battery'] = True
            elif 'battery_override' in payload:
                val = payload['battery_override']
                if val is not None:
                    rdata['battery_override'] = float(val)
                    ros_payload['battery_override'] = float(val)
                else:
                    rdata['battery_override'] = None
                    ros_payload['clear_battery'] = True

            # Position override
            if payload.get('clear_position', False) or payload.get('reset_all', False):
                rdata['position_override'] = None
                ros_payload['clear_position'] = True
            elif 'position_override' in payload:
                pos = payload['position_override']
                if pos is not None and 'x' in pos and 'y' in pos:
                    rdata['position_override'] = {'x': float(pos['x']), 'y': float(pos['y'])}
                    ros_payload['position_override'] = {'x': float(pos['x']), 'y': float(pos['y'])}
                else:
                    rdata['position_override'] = None
                    ros_payload['clear_position'] = True

            if payload.get('reset_all', False):
                ros_payload['reset_all'] = True
                self._add_event(f"All overrides cleared for {robot_id}", "control")
            else:
                self._add_event(f"Override updated for {robot_id}: {ros_payload}", "control")

        msg = String()
        msg.data = json.dumps(ros_payload)
        self.pub_override[robot_id].publish(msg)

    def set_comms_degrade(self, robot_id: str, drop_prob: float, delay_sec: float):
        if robot_id in self.pub_comms_degrade:
            payload = {'drop_prob': float(drop_prob), 'delay_sec': float(delay_sec)}
            with self.state_lock:
                self.state['robots'][robot_id]['comms_degrade'] = payload
                self._add_event(f"Comms degradation for {robot_id}: drop={drop_prob}, delay={delay_sec}s", "control")
            msg = String()
            msg.data = json.dumps(payload)
            self.pub_comms_degrade[robot_id].publish(msg)

    def trigger_stop_all(self):
        with self.state_lock:
            self._add_event("All active navigation goals cancelled via Wi-Fi command.", "control")
            for rid in self.fleet_robot_ids:
                self.state['robots'][rid]['active_task'] = None
        msg = String()
        msg.data = json.dumps({'stop': True})
        self.pub_stop_all.publish(msg)

    def announce_task(self, task_id: str, x: float, y: float, heading: float = 0.0):
        """Announces a task to the fleet over /fleet/task_announcement for interactive testing."""
        msg = String()
        msg.data = json.dumps({
            'task_id': task_id,
            'x': float(x),
            'y': float(y),
            'heading': float(heading),
            'is_reauction': False
        })
        self.pub_announcement.publish(msg)
        self._add_event(f"Task announced from dashboard: {task_id} at ({x:.2f}, {y:.2f})", "auction")

    def simulate_bid(self, payload: dict) -> dict:
        """Returns step-by-step mathematical bid calculation for any simulated parameters."""
        rx = float(payload.get('robot_x', 0.0))
        ry = float(payload.get('robot_y', 0.0))
        tx = float(payload.get('task_x', 2.5))
        ty = float(payload.get('task_y', 3.2))
        bat_pct = float(payload.get('battery_pct', 80.0))
        failures = int(payload.get('failures', 0))
        is_busy = bool(payload.get('is_busy', False))

        dx = tx - rx
        dy = ty - ry
        dist = math.sqrt(dx * dx + dy * dy)
        bat_fraction = max(0.0, min(1.0, bat_pct / 100.0))

        # Battery multiplier variable: 0 if < 10%, 1 if >= 10%
        multiplier = 0 if bat_pct < 10.0 else 1
        w_d = 1.0
        w_b = 5.0
        w_f = 2.0
        dist_cost = w_d * dist
        bat_cost = w_b * (1.0 - bat_fraction)
        fail_cost = w_f * failures
        busy_cost = 1000.0 if is_busy else 0.0
        base_cost = dist_cost + bat_cost + fail_cost + busy_cost
        final_bid = multiplier * base_cost

        return {
            'status': 'ok',
            'robot_pos': [rx, ry],
            'task_pos': [tx, ty],
            'distance': round(dist, 3),
            'w_distance': w_d,
            'dist_cost': round(dist_cost, 3),
            'battery_pct': round(bat_pct, 1),
            'battery_fraction': round(bat_fraction, 3),
            'w_battery': w_b,
            'bat_cost': round(bat_cost, 3),
            'failures': failures,
            'w_failure': w_f,
            'fail_cost': round(fail_cost, 3),
            'busy_cost': round(busy_cost, 3),
            'base_cost': round(base_cost, 3),
            'battery_multiplier': multiplier,
            'final_bid': round(final_bid, 3),
            'is_eligible': multiplier > 0,
            'status_note': 'Eligible bidder' if multiplier > 0 else 'Disqualified (Battery < 10%, μ=0)'
        }


class DashboardHTTPHandler(SimpleHTTPRequestHandler):
    ros_node: FleetDashboardNode = None
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(self.ros_node.web_dir), **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def _send_json(self, data_dict: dict, code: int = 200):
        try:
            payload = json.dumps(data_dict).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(payload)
        except Exception:
            pass

    def translate_path(self, path):
        path = path.split('?', 1)[0].split('#', 1)[0]
        if path in ('/', '', '/index.html'):
            return str(self.ros_node.web_dir / 'Arjuna.html')
        clean_path = path.lstrip('/')
        return str(self.ros_node.web_dir / clean_path)

    def do_GET(self):
        clean_path = self.path.split('?')[0].split('#')[0]
        if clean_path in ('/api/status', '/api/state'):
            with self.ros_node.state_lock:
                self.ros_node.state['server_time'] = time.time()
                data = dict(self.ros_node.state)
            self._send_json(data)
        elif clean_path == '/api/logs':
            self._send_json(self.ros_node.get_all_logs())
        elif clean_path == '/api/maintenance':
            with self.ros_node.state_lock:
                data = dict(self.ros_node.state.get('maintenance', {}))
            self._send_json(data)
        else:
            super().do_GET()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8') if length > 0 else ''
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        response = {'status': 'ok'}

        if self.path == '/api/stop_all':
            self.ros_node.trigger_stop_all()
        elif self.path == '/api/mode':
            self.ros_node.set_mode(data.get('mode', 'decentralized'))
        elif self.path == '/api/master':
            self.ros_node.set_master(data.get('master', 'arjuna_1'))
        elif self.path == '/api/soft_kill':
            rid = data.get('robot_id')
            killed = bool(data.get('killed', False))
            self.ros_node.set_soft_kill(rid, killed)
        elif self.path == '/api/override':
            rid = data.get('robot_id')
            self.ros_node.set_override(rid, data)
        elif self.path == '/api/comms_degrade':
            rid = data.get('robot_id')
            drop = float(data.get('drop_prob', 0.0))
            delay = float(data.get('delay_sec', 0.0))
            self.ros_node.set_comms_degrade(rid, drop, delay)
        elif self.path == '/api/announce_task':
            tid = str(data.get('task_id', f"T{int(time.time())%1000:03d}"))
            x = float(data.get('x', 2.5))
            y = float(data.get('y', 3.2))
            h = float(data.get('heading', 0.0))
            self.ros_node.announce_task(tid, x, y, h)
            response['task_id'] = tid
        elif self.path == '/api/simulate_bid':
            response = self.ros_node.simulate_bid(data)
        elif self.path == '/api/maintenance/thresholds':
            dist = float(data.get('distance_threshold_m', data.get('distance_m', 500.0)))
            time_s = float(data.get('time_threshold_s', data.get('time_s', float(data.get('runtime_min', 120.0)) * 60.0)))
            self.ros_node.set_maintenance_thresholds(dist, time_s)
            response['thresholds'] = {'distance_m': dist, 'runtime_s': time_s}
        elif self.path == '/api/maintenance/reset':
            rid = data.get('robot_id')
            note = data.get('note', '')
            self.ros_node.reset_maintenance(rid, note)
            response['reset_robot_id'] = rid
        elif self.path == '/api/maintenance/simulate':
            rid = data.get('robot_id')
            add_dist = float(data.get('add_distance_m', 0.0))
            add_time = float(data.get('add_time_s', float(data.get('add_runtime_min', 0.0)) * 60.0))
            self.ros_node.simulate_maintenance_wear(rid, add_dist, add_time)
            response['simulated'] = {'robot_id': rid, 'add_distance_m': add_dist, 'add_time_s': add_time}
        else:
            self._send_json({'error': 'Not Found'}, code=404)
            return

        self._send_json(response)

    def log_message(self, format, *args):
        # Suppress routine GET logging for static assets and polling
        return


def run_http_server(node: FleetDashboardNode, port: int):
    DashboardHTTPHandler.ros_node = node
    server = ThreadingHTTPServer(('0.0.0.0', port), DashboardHTTPHandler)
    server.serve_forever()


def main(args=None):
    parser = argparse.ArgumentParser(description="TerrainFleet Web Dashboard Server")
    parser.add_argument('--port', '-p', type=int, default=8080, help="Web server port (default: 8080)")

    filtered_args = []
    ros_args = []
    is_ros = False
    for a in sys.argv[1:]:
        if a == '--ros-args':
            is_ros = True
        if is_ros:
            ros_args.append(a)
        else:
            filtered_args.append(a)

    parsed = parser.parse_args(filtered_args)

    rclpy.init(args=ros_args)
    node = FleetDashboardNode(port=parsed.port)

    http_thread = threading.Thread(target=run_http_server, args=(node, parsed.port), daemon=True)
    http_thread.start()

    print(f"\n🚀 Dashboard UI is live at: http://localhost:{parsed.port}")
    print(f"   (Local network access: http://<laptop-ip>:{parsed.port})\n")

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
