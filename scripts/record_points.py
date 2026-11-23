#!/usr/bin/env python3
"""
TerrainFleet Point Recorder
===========================
Top-level entry script.
Records home positions (--home) or task spots (--task) using RViz Publish Point tool.

Usage:
  ./scripts/record_points.py --home
  ./scripts/record_points.py --task --output tasks_setA.csv
"""

import sys
from pathlib import Path

# Add src package directory to sys.path
ws_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ws_dir / 'src' / 'arjuna_auction'))

from arjuna_auction.record_points import main

if __name__ == '__main__':
    main()
