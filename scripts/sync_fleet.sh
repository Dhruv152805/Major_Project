#!/usr/bin/env bash
set -e

ROBOT1_IP="$1"
ROBOT2_IP="$2"

if [ -z "$ROBOT1_IP" ] || [ -z "$ROBOT2_IP" ]; then
    echo "Usage: ./scripts/sync_fleet.sh <ROBOT_1_IP> <ROBOT_2_IP>"
    echo "Example: ./scripts/sync_fleet.sh 172.25.73.50 172.25.72.156"
    echo ""
    echo "To sync individually:"
    echo "  ./scripts/sync_to_robot1.sh <ROBOT_1_IP>"
    echo "  ./scripts/sync_to_robot2.sh <ROBOT_2_IP>"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================================"
echo "🚀 SYNCING FLEET CODEBASE TO BOTH ROBOTS"
echo "   Robot 1: $ROBOT1_IP"
echo "   Robot 2: $ROBOT2_IP"
echo "========================================================"

echo ""
echo ">>> [1/2] Syncing to Robot 1 ($ROBOT1_IP)..."
"$SCRIPT_DIR/sync_to_robot1.sh" "$ROBOT1_IP"

echo ""
echo ">>> [2/2] Syncing to Robot 2 ($ROBOT2_IP)..."
"$SCRIPT_DIR/sync_to_robot2.sh" "$ROBOT2_IP"

echo ""
echo "========================================================"
echo "✅ Both robots are now in sync with the latest codebase!"
echo "========================================================"
