#!/usr/bin/env bash
set -e

ROBOT1_IP="$1"

if [ -z "$ROBOT1_IP" ]; then
    echo "Usage: ./scripts/sync_to_robot1.sh <ROBOT_1_IP>"
    echo "Example: ./scripts/sync_to_robot1.sh 172.25.73.50"
    exit 1
fi

echo "========================================================"
echo " Syncing updated code files to Robot 1 ($ROBOT1_IP)..."
echo "========================================================"

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Ensure target directories exist on Robot 1
echo "-> Ensuring directories exist on Robot 1..."
ssh "arjuna@$ROBOT1_IP" "mkdir -p ~/Arjuna_ws_team3/scripts \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/launch \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/config \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/maps \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/webpage \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/scripts/Arjuna_navigation \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/scripts/Newrro_NavLib \
    ~/Arjuna_ws_team3/src/arjuna_auction/arjuna_auction \
    ~/Arjuna_ws_team3/src/arjuna_baseline/arjuna_baseline"

# 1. Sync launch files
echo "-> Syncing launch files (bringup_launch.py & mapping_launch.py)..."
scp "$WORKSPACE_DIR/src/arjuna_main/arjuna_main/launch/"*.py \
    "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/launch/"

# 2. Sync config & map files
echo "-> Syncing config files & maps..."
scp "$WORKSPACE_DIR/src/arjuna_main/arjuna_main/config/"*.yaml \
    "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/config/"
scp "$WORKSPACE_DIR/src/arjuna_main/arjuna_main/maps/"* \
    "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/maps/"

# 3. Sync dashboard server, webpage & arjuna_main setup
echo "-> Syncing dashboard server & webpage..."
scp "$WORKSPACE_DIR/src/arjuna_main/setup.py" \
    "$WORKSPACE_DIR/src/arjuna_main/package.xml" \
    "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/src/arjuna_main/"
scp "$WORKSPACE_DIR/src/arjuna_main/arjuna_main/fleet_dashboard_server.py" \
    "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/"
scp "$WORKSPACE_DIR/src/arjuna_main/arjuna_main/webpage/Arjuna.html" \
    "$WORKSPACE_DIR/src/arjuna_main/arjuna_main/webpage/Arjuna.css" \
    "$WORKSPACE_DIR/src/arjuna_main/arjuna_main/webpage/Arjuna.js" \
    "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/webpage/"
ssh "arjuna@$ROBOT1_IP" "rm -f ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/webpage/index.html \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/launch/*.bak \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/launch/*.backup"

# 4. Sync arjuna_auction package
echo "-> Syncing arjuna_auction package..."
scp "$WORKSPACE_DIR/src/arjuna_auction/package.xml" \
    "$WORKSPACE_DIR/src/arjuna_auction/setup.py" \
    "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/src/arjuna_auction/"
scp "$WORKSPACE_DIR/src/arjuna_auction/arjuna_auction/"*.py \
    "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/src/arjuna_auction/arjuna_auction/"

# 5. Sync arjuna_baseline package
echo "-> Syncing arjuna_baseline package..."
scp "$WORKSPACE_DIR/src/arjuna_baseline/package.xml" \
    "$WORKSPACE_DIR/src/arjuna_baseline/setup.py" \
    "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/src/arjuna_baseline/"
scp "$WORKSPACE_DIR/src/arjuna_baseline/arjuna_baseline/"*.py \
    "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/src/arjuna_baseline/arjuna_baseline/"

# 6. Sync scripts directory
echo "-> Syncing utility scripts..."
scp "$WORKSPACE_DIR/scripts/"*.py \
    "$WORKSPACE_DIR/scripts/"*.sh \
    "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/scripts/"

# 7. Sync navigation scripts
echo "-> Syncing navigation scripts..."
scp "$WORKSPACE_DIR/src/arjuna_main/arjuna_main/scripts/Arjuna_navigation/"*.py \
    "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/scripts/Arjuna_navigation/"
scp "$WORKSPACE_DIR/src/arjuna_main/arjuna_main/scripts/Newrro_NavLib/"*.py \
    "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/scripts/Newrro_NavLib/"

# 8. Sync root fleet configs and tasks
echo "-> Syncing fleet configs & tasks..."
[ -f "$WORKSPACE_DIR/tasks_setA.csv" ] && scp "$WORKSPACE_DIR/tasks_setA.csv" "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/"
[ -f "$WORKSPACE_DIR/fleet_config.yaml" ] && scp "$WORKSPACE_DIR/fleet_config.yaml" "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/"
[ -f "$WORKSPACE_DIR/maintenance_tracker.json" ] && scp "$WORKSPACE_DIR/maintenance_tracker.json" "arjuna@$ROBOT1_IP:~/Arjuna_ws_team3/"

echo ""
echo "========================================================"
echo "✅ All code files synced successfully to Robot 1 ($ROBOT1_IP)!"
echo "========================================================"
echo ""
echo "Next steps on Robot 1 ($ROBOT1_IP):"
echo "  1. SSH into Robot 1:"
echo "       ssh arjuna@$ROBOT1_IP"
echo ""
echo "  2. Ensure ROS_DOMAIN_ID=44 is set in ~/.bashrc:"
echo "       grep ROS_DOMAIN_ID ~/.bashrc || echo 'export ROS_DOMAIN_ID=44' >> ~/.bashrc"
echo "       source ~/.bashrc"
echo ""
echo "  3. Build workspace:"
echo "       cd ~/Arjuna_ws_team3"
echo "       colcon build --symlink-install"
echo "       source install/setup.bash"
echo ""
echo "  4. Launch Robot 1 (Note: run_map_server:=True because Robot 1 shares map):"
echo "       ros2 launch arjuna_main bringup_launch.py robot_id:=arjuna_1 run_map_server:=True gui:=False"
echo ""
echo "  5. Launch Fleet Nodes on Robot 1:"
echo "       ros2 run arjuna_auction heartbeat_monitor --ros-args -p robot_id:=arjuna_1 -p fleet_robot_ids:=\"['arjuna_1','arjuna_2']\""
echo "       ros2 run arjuna_auction auction_node --ros-args -p robot_id:=arjuna_1 -p fleet_robot_ids:=\"['arjuna_1','arjuna_2']\" -p odom_topic:=/arjuna_1/odom -p battery_topic:=/arjuna_1/battery_state"
echo ""
