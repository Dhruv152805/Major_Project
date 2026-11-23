#!/usr/bin/env bash
set -e

ROBOT2_IP="$1"

if [ -z "$ROBOT2_IP" ]; then
    echo "Usage: ./sync_to_robot2.sh <ROBOT_2_IP>"
    echo "Example: ./sync_to_robot2.sh 172.25.72.156"
    exit 1
fi

echo "========================================================"
echo " Syncing updated files from Robot 1 to Robot 2 ($ROBOT2_IP)..."
echo "========================================================"

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Ensure target directories exist on Robot 2
ssh "arjuna@$ROBOT2_IP" "mkdir -p ~/Arjuna_ws_team3/scripts \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/launch \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/config \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/scripts/Arjuna_navigation \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/scripts/Newrro_NavLib"

# 1. Sync launch files
echo "-> Syncing launch files (bringup_launch.py & mapping_launch.py)..."
scp "$WORKSPACE_DIR/src/arjuna_main/arjuna_main/launch/"*.py \
    "arjuna@$ROBOT2_IP:~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/launch/"

# 2. Sync tuned nav2 params
echo "-> Syncing nav2_params.yaml..."
scp "$WORKSPACE_DIR/src/arjuna_main/arjuna_main/config/nav2_params.yaml" \
    "arjuna@$ROBOT2_IP:~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/config/"

# 3. Sync auction package
echo "-> Syncing arjuna_auction package..."
scp "$WORKSPACE_DIR/src/arjuna_auction/package.xml" \
    "$WORKSPACE_DIR/src/arjuna_auction/setup.py" \
    "arjuna@$ROBOT2_IP:~/Arjuna_ws_team3/src/arjuna_auction/"
scp "$WORKSPACE_DIR/src/arjuna_auction/arjuna_auction/"*.py \
    "arjuna@$ROBOT2_IP:~/Arjuna_ws_team3/src/arjuna_auction/arjuna_auction/"

# 4. Sync nearest robot controller & baseline package
echo "-> Syncing arjuna_baseline package..."
scp "$WORKSPACE_DIR/src/arjuna_baseline/package.xml" \
    "$WORKSPACE_DIR/src/arjuna_baseline/setup.py" \
    "arjuna@$ROBOT2_IP:~/Arjuna_ws_team3/src/arjuna_baseline/"
scp "$WORKSPACE_DIR/src/arjuna_baseline/arjuna_baseline/nearest_robot_controller.py" \
    "arjuna@$ROBOT2_IP:~/Arjuna_ws_team3/src/arjuna_baseline/arjuna_baseline/"

# 5. Sync setup permissions script
echo "-> Syncing setup_robot2_permissions.sh..."
scp "$WORKSPACE_DIR/scripts/setup_robot2_permissions.sh" \
    "arjuna@$ROBOT2_IP:~/Arjuna_ws_team3/scripts/"

# 6. Sync goal dispatcher & navigation scripts
echo "-> Syncing navigation scripts & setup.py..."
scp "$WORKSPACE_DIR/src/arjuna_main/setup.py" \
    "$WORKSPACE_DIR/src/arjuna_main/package.xml" \
    "arjuna@$ROBOT2_IP:~/Arjuna_ws_team3/src/arjuna_main/"
scp "$WORKSPACE_DIR/scripts/send_fleet_goal.py" \
    "arjuna@$ROBOT2_IP:~/Arjuna_ws_team3/scripts/"
scp "$WORKSPACE_DIR/src/arjuna_main/arjuna_main/scripts/Arjuna_navigation/"*.py \
    "arjuna@$ROBOT2_IP:~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/scripts/Arjuna_navigation/"
scp "$WORKSPACE_DIR/src/arjuna_main/arjuna_main/scripts/Newrro_NavLib/"*.py \
    "arjuna@$ROBOT2_IP:~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/scripts/Newrro_NavLib/"

echo ""
echo "Files synced successfully!"
echo ""
echo "Next steps on Robot 2 ($ROBOT2_IP):"
echo "  1. Ensure ROS_DOMAIN_ID=44 is set in ~/.bashrc"
echo "  2. Fix permissions: ./setup_robot2_permissions.sh"
echo "  3. Build and launch:"
echo "       cd ~/Arjuna_ws_team3"
echo "       colcon build --symlink-install"
echo "       source install/setup.bash"
echo "       ros2 launch arjuna_main bringup_launch.py robot_id:=arjuna_2 run_map_server:=False gui:=False"
