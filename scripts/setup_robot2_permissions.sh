#!/usr/bin/env bash
# ==============================================================================
# setup_robot2_permissions.sh
# Fixes serial port permissions for motor controller and lidar on Robot 2
# ==============================================================================

set -e

echo "=== [1/4] Adding user '$USER' to 'dialout' group ==="
sudo usermod -aG dialout "$USER"

echo "=== [2/4] Installing persistent udev rules for /dev/ttyACM* and /dev/ttyUSB* ==="
cat << 'UDEV_RULE' | sudo tee /etc/udev/rules.d/99-arjuna-serial.rules > /dev/null
# Allow read/write access to motor controller and RPLIDAR serial devices
KERNEL=="ttyACM[0-9]*", MODE="0666", GROUP="dialout"
KERNEL=="ttyUSB[0-9]*", MODE="0666", GROUP="dialout"
UDEV_RULE

echo "=== [3/4] Reloading and triggering udev rules ==="
sudo udevadm control --reload-rules
sudo udevadm trigger
sudo chmod 666 /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || true

echo "=== [4/4] Verifying device access ==="
PASS=true

if [ -r /dev/ttyACM0 ] && [ -w /dev/ttyACM0 ]; then
    echo "  [OK] /dev/ttyACM0 (Motor Controller) is readable and writable."
else
    echo "  [FAIL] /dev/ttyACM0 is NOT accessible."
    PASS=false
fi

if [ -r /dev/ttyUSB0 ] && [ -w /dev/ttyUSB0 ]; then
    echo "  [OK] /dev/ttyUSB0 (RPLidar) is readable and writable."
else
    echo "  [FAIL] /dev/ttyUSB0 is NOT accessible."
    PASS=false
fi

if [ -r /dev/i2c-7 ] && [ -w /dev/i2c-7 ]; then
    echo "  [OK] /dev/i2c-7 (BNO055 IMU) is readable and writable."
else
    echo "  [WARN] /dev/i2c-7 is NOT accessible."
fi

echo ""
if [ "$PASS" = true ]; then
    echo "Permissions successfully configured!"
    echo "NOTE: To apply group changes in this shell, run: newgrp dialout"
    echo "      (or log out and back in)."
else
    echo "Some checks failed. Please check device connections."
fi
