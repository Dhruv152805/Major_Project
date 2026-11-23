# TerrainFleet Multi-Robot Experimental Workflow Guide
**Arjuna Autonomous Robot Fleet (arjuna_1 & arjuna_2)**

This handbook outlines the complete end-to-end operation of the TerrainFleet multi-robot system across **Parts 1 through 8**, matching the decentralized auction, centralized baseline, fault injection, and web telemetry architecture.

---

## 🏗️ Architecture & File Organization

The workspace is cleanly structured into modular directories:

```
Arjuna_ws_team3/
│
├── scripts/                               # 📁 Executable CLI tools & runners
│   ├── record_points.py                   # RViz point recorder (home poses & task lists)
│   ├── set_home_poses.py                  # Automatic AMCL starting pose dispatcher
│   ├── run_dashboard.py                   # Modern Web Control Deck runner (http://localhost:8080)
│   ├── analyze_runs.py                    # Results & comparison graph plotter (Part 8)
│   ├── send_fleet_goal.py                 # Goal dispatcher for individual spot testing
│   ├── sync_to_robot1.sh                  # Syncs updated code & launch nodes to Robot 1
│   ├── sync_to_robot2.sh                  # Syncs updated code & launch nodes to Robot 2
│   ├── sync_fleet.sh                      # One-command sync to both robots
│   └── setup_robot2_permissions.sh        # Device & serial permissions setup for Robot 2
│
├── docs/                                  # 📁 Documentation & TF diagnostic graphs
│   └── frames/                            # TF transform frame trees (.gv, .pdf)
│
├── archive/                               # 📁 Archive packages & backups
│   ├── google-chrome-stable_current_amd64.deb
│   ├── src.zip
│   └── src1.zip
│
└── src/                                   # 📁 Clean ROS 2 Packages
    ├── arjuna_auction/                    # Decentralized Auction & Fleet Tools
    │   ├── arjuna_auction/
    │   │   ├── auction_node.py            # Independent bidding, execution, learned bidder & re-auction
    │   │   ├── heartbeat_monitor.py       # Peer failure detection & soft-kill listener
    │   │   ├── task_injector.py           # Laptop task list announcer (/fleet/task_announcement)
    │   │   ├── task_marker_node.py        # 3D RViz colored marker visualizer
    │   │   ├── record_points.py           # Core recorder node
    │   │   ├── set_home_poses.py          # Core home pose setter node
    │   │   ├── train_bid_model.py         # XGBoost / regularized learned bidder trainer
    │   │   └── analyze_runs.py            # Metrics comparison engine
    │   ├── package.xml
    │   └── setup.py
    │
    ├── arjuna_baseline/                   # Centralized Baseline
    │   ├── arjuna_baseline/
    │   │   └── nearest_robot_controller.py # Multi-robot remote dispatcher fix
    │   ├── package.xml
    │   └── setup.py
    │
    └── arjuna_main/                       # Drivers, Launch & Web Deck
        ├── fleet_dashboard_server.py     # Lightweight Python REST API & web server
        ├── webpage/                       # Cyberpunk-style modern UI (HTML, CSS, JS)
        ├── package.xml
        └── setup.py
```

---

## Part 1: Workspace & Wi-Fi Setup

1. **Network Configuration**:
   - Ensure the laptop, Robot 1 (`arjuna_1`), and Robot 2 (`arjuna_2`) are connected to the same Wi-Fi network.
   - Verify both robots share `ROS_DOMAIN_ID=44` in their `~/.bashrc`.
2. **Sync Code to the Robots**:
   - **To sync Robot 1**:
     ```bash
     ./scripts/sync_to_robot1.sh <ROBOT_1_IP>
     ```
   - **To sync Robot 2**:
     ```bash
     ./scripts/sync_to_robot2.sh <ROBOT_2_IP>
     ```
   - **To sync both robots at once**:
     ```bash
     ./scripts/sync_fleet.sh <ROBOT_1_IP> <ROBOT_2_IP>
     ```
3. **Start Robot 1** (Terminal SSH to Robot 1):
   ```bash
   ros2 launch arjuna_main bringup_launch.py robot_id:=arjuna_1 run_map_server:=True gui:=False
   ```
4. **Start Robot 2** (Terminal SSH to Robot 2):
   ```bash
   ros2 launch arjuna_main bringup_launch.py robot_id:=arjuna_2 run_map_server:=False gui:=False
   ```
5. **Open RViz on Laptop**:
   ```bash
   rviz2 -d src/arjuna_main/arjuna_main/rviz/arjuna.rviz
   ```
   *Displays the shared map, red scan (`arjuna_1`), cyan scan (`arjuna_2`), and both robot paths.*

---

## Part 2: Home Positions Setup

1. Tape two home spots on the floor at opposite ends of the map.
2. Run the recorder in **home mode** on your laptop:
   ```bash
   ./scripts/record_points.py --home
   # or: ros2 run arjuna_auction record_points --home
   ```
3. In RViz, use the **Publish Point** tool to click 4 times in sequence:
   - **Click 1**: Position where `arjuna_1` stands.
   - **Click 2**: Point straight ahead of `arjuna_1` (computes heading).
   - **Click 3**: Position where `arjuna_2` stands.
   - **Click 4**: Point straight ahead of `arjuna_2` (computes heading).
   *The coordinates are rounded to centimetres and saved automatically to `fleet_config.yaml`.*
4. Initialize AMCL starting poses at any time:
   ```bash
   ./scripts/set_home_poses.py
   # or: ros2 run arjuna_auction set_home_poses
   ```
5. Verify in RViz that the laser scans align with the walls. If needed, drive a robot slightly to settle particles.

---

## Part 3: Task Lists Creation

1. Tape 10 to 20 numbered task spots on the open floor (away from obstacles).
2. Record task spots in **task mode**:
   ```bash
   ./scripts/record_points.py --task --output tasks_setA.csv
   ```
3. In RViz, click each task spot using the **Publish Point** tool:
   - Each click appends `T01`, `T02`, etc., directly to `tasks_setA.csv`.
   - If continuing an existing set, numbering carries on automatically.
4. **Test Each Spot** (Verify reachability by sending one robot):
   ```bash
   ./scripts/send_fleet_goal.py --robot arjuna_1 --x 1.50 --y -0.80
   ```
   *If the robot cannot reach the spot, adjust the tape mark and record again.*
5. Create separate lists (e.g., `tasks_setA.csv`, `tasks_setB.csv`, `tasks_setC.csv`) for different experimental scenarios.

---

## Part 4: Run the Decentralized Fleet

1. **On Robot 1**:
   ```bash
   ros2 run arjuna_auction heartbeat_monitor --ros-args -p robot_id:=arjuna_1 -p fleet_robot_ids:="['arjuna_1','arjuna_2']"
   ros2 run arjuna_auction auction_node --ros-args -p robot_id:=arjuna_1 -p fleet_robot_ids:="['arjuna_1','arjuna_2']" -p odom_topic:=/arjuna_1/odom -p battery_topic:=/arjuna_1/battery_state
   ```
2. **On Robot 2**:
   ```bash
   ros2 run arjuna_auction heartbeat_monitor --ros-args -p robot_id:=arjuna_2 -p fleet_robot_ids:="['arjuna_1','arjuna_2']"
   ros2 run arjuna_auction auction_node --ros-args -p robot_id:=arjuna_2 -p fleet_robot_ids:="['arjuna_1','arjuna_2']" -p odom_topic:=/arjuna_2/odom -p battery_topic:=/arjuna_2/battery_state
   ```
3. **On Laptop** (Start Task Marker RViz visualizer):
   ```bash
   ros2 run arjuna_auction task_marker_node
   ```
   *Visualizes markers in RViz: Red for tasks won by `arjuna_1`, Cyan for `arjuna_2`, Green when done, Orange for re-auction.*
4. **On Laptop** (Inject Tasks):
   ```bash
   ros2 run arjuna_auction task_injector --task-file tasks_setA.csv --mode on_completion
   # Or fixed interval:
   # ros2 run arjuna_auction task_injector --task-file tasks_setA.csv --mode interval --interval 20.0
   # Or manual step-by-step:
   # ros2 run arjuna_auction task_injector --task-file tasks_setA.csv --mode manual
   ```

---

## Part 5: Centralized Baseline Comparison

1. Launch `nearest_robot_controller` on the master robot (or laptop):
   ```bash
   ros2 run arjuna_baseline nearest_robot_controller --ros-args \
     -p robot_id:=arjuna_1 \
     -p fleet_robot_ids:="['arjuna_1','arjuna_2']" \
     -p my_odom_topic:=/arjuna_1/odom \
     -p other_robot_odom_topics:="['/arjuna_2/odom']"
   ```
2. Switch fleet mode to centralized via topic or dashboard:
   ```bash
   ros2 topic pub /fleet/mode std_msgs/String '{data: "centralized"}' --once
   ros2 topic pub /fleet/centralized_master std_msgs/String '{data: "arjuna_1"}' --once
   ```
3. Announce the identical task list with `task_injector`. The centralized controller directly commands whichever robot is closest via Nav2 ActionClients and logs all results to `centralized_log.csv`.

---

## Part 6: Fault Injection & Re-Auction Test

1. **Hardware Power-Off**: While a robot is driving to a task, switch off its power.
2. **Dashboard Soft-Kill**: Alternatively, toggle the soft-kill switch on the web dashboard (or publish `{"killed": true}` on `/fleet/soft_kill/<robot_id>`).
3. **Autonomous Recovery**:
   - The survivor notices missing heartbeats after `3.0s`.
   - Heartbeat monitor declares `/fleet/robot_failure`.
   - The survivor re-auctions the abandoned task (`is_reauction: true`), wins it, and drives to finish it without human intervention.

---

## Part 7: Web Telemetry & Control Dashboard

1. Launch the dashboard server on the laptop:
   ```bash
   ./scripts/run_dashboard.py --port 8080
   # or: ros2 run arjuna_main fleet_dashboard
   ```
2. Open your browser at **`http://localhost:8080`** (or access from tablet/phone at `http://<laptop-ip>:8080`).
3. **Controls available**:
   - **STOP ALL**: Pulsating red button that halts all robots immediately.
   - **Soft-Kill Switches**: Toggles heartbeat silence for repeatable fault tests.
   - **Overrides**: Set test battery levels or virtual positions.
   - **Comms Degradation**: Inject packet drop percentage and latency.
   - **Mode Switch**: Toggle between Decentralized Auction and Centralized Baseline.
   - **Centralized Master Selector**: Choose which robot acts as centralized dispatcher.

---

## Part 8: Results Analysis & Learned Bidder

1. **Generate Graphs & Metrics**:
   ```bash
   ./scripts/analyze_runs.py --auction auction_log.csv --centralized centralized_log.csv --output results_comparison.png
   ```
   *Generates comparison bar charts for completion time, distance traveled, success rate, and fault recovery timeline. Leaves charts empty with an informative note if no data exists yet.*
2. **Train Learned Bidder (XGBoost)**:
   ```bash
   ros2 run arjuna_auction train_bid_model --log auction_log.csv --output bid_model.json
   ```
   *Evaluates RMSE against the heuristic formula. If the learned model outperforms the heuristic, it saves `bid_model.json`.*
3. **Activate Learned Bidder**:
   Launch `auction_node` with:
   ```bash
   ros2 run arjuna_auction auction_node --ros-args -p use_learned_bid:=True -p model_path:=bid_model.json ...
   ```
