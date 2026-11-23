#!/usr/bin/env bash
set -e

LAPTOP_IP="${1:-172.25.73.103}"
LAPTOP_USER="${2:-dhruv}"

if [ -z "$LAPTOP_IP" ]; then
    echo "Usage: ./scripts/sync_to_laptop.sh <LAPTOP_IP> [LAPTOP_USER]"
    echo "Example: ./scripts/sync_to_laptop.sh 172.25.73.103 dhruv"
    exit 1
fi

echo "========================================================"
echo " Syncing all updated files to Laptop ($LAPTOP_USER@$LAPTOP_IP)..."
echo "========================================================"

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Ensure target directories exist on Laptop
echo "-> Ensuring directories exist on Laptop..."
ssh "$LAPTOP_USER@$LAPTOP_IP" "mkdir -p ~/Arjuna_ws_team3/scripts \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/launch \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/config \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/maps \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/webpage \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/scripts/Arjuna_navigation \
    ~/Arjuna_ws_team3/src/arjuna_main/arjuna_main/scripts/Newrro_NavLib \
    ~/Arjuna_ws_team3/src/arjuna_auction/arjuna_auction \
    ~/Arjuna_ws_team3/src/arjuna_baseline/arjuna_baseline"

# 1. Sync all source packages
echo "-> Syncing src/arjuna_main..."
rsync -avz "$WORKSPACE_DIR/src/arjuna_main/" "$LAPTOP_USER@$LAPTOP_IP:~/Arjuna_ws_team3/src/arjuna_main/"

echo "-> Syncing src/arjuna_auction..."
rsync -avz "$WORKSPACE_DIR/src/arjuna_auction/" "$LAPTOP_USER@$LAPTOP_IP:~/Arjuna_ws_team3/src/arjuna_auction/"

echo "-> Syncing src/arjuna_baseline..."
rsync -avz "$WORKSPACE_DIR/src/arjuna_baseline/" "$LAPTOP_USER@$LAPTOP_IP:~/Arjuna_ws_team3/src/arjuna_baseline/"

# 2. Sync scripts
echo "-> Syncing scripts..."
rsync -avz "$WORKSPACE_DIR/scripts/" "$LAPTOP_USER@$LAPTOP_IP:~/Arjuna_ws_team3/scripts/"

# 3. Sync configs, tasks, and maintenance tracker
echo "-> Syncing configs, tasks, and maintenance tracker..."
[ -f "$WORKSPACE_DIR/tasks_setA.csv" ] && scp "$WORKSPACE_DIR/tasks_setA.csv" "$LAPTOP_USER@$LAPTOP_IP:~/Arjuna_ws_team3/"
[ -f "$WORKSPACE_DIR/fleet_config.yaml" ] && scp "$WORKSPACE_DIR/fleet_config.yaml" "$LAPTOP_USER@$LAPTOP_IP:~/Arjuna_ws_team3/"
[ -f "$WORKSPACE_DIR/maintenance_tracker.json" ] && scp "$WORKSPACE_DIR/maintenance_tracker.json" "$LAPTOP_USER@$LAPTOP_IP:~/Arjuna_ws_team3/"

echo ""
echo "========================================================"
echo "✅ All code files synced successfully to Laptop ($LAPTOP_IP)!"
echo "========================================================"
echo ""
echo "Next step on Laptop ($LAPTOP_IP):"
echo "  cd ~/Arjuna_ws_team3 && colcon build --symlink-install"
echo "  source install/setup.bash && export ROS_DOMAIN_ID=44"
echo ""
