#!/usr/bin/env python3
"""
TerrainFleet Web Dashboard Runner
=================================
Top-level entry script.
Launches the control dashboard server on http://localhost:8080

Usage:
  ./scripts/run_dashboard.py
  ./scripts/run_dashboard.py --port 8080
"""

import sys
from pathlib import Path

ws_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ws_dir / 'src' / 'arjuna_main'))

from arjuna_main.fleet_dashboard_server import main

if __name__ == '__main__':
    main()
