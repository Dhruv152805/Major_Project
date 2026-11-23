#!/usr/bin/env python3
"""
TerrainFleet Home Pose Dispatcher
=================================
Top-level entry script.
Reads fleet_config.yaml and sets AMCL starting poses on both robots automatically.

Usage:
  ./scripts/set_home_poses.py
  ./scripts/set_home_poses.py --config fleet_config.yaml
"""

import sys
from pathlib import Path

# Add src package directory to sys.path
ws_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ws_dir / 'src' / 'arjuna_auction'))

from arjuna_auction.set_home_poses import main

if __name__ == '__main__':
    main()
