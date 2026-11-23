#!/usr/bin/env python3
"""
TerrainFleet Run Analysis & Comparison Graph Generator
======================================================
Top-level entry script.
Analyzes auction_log.csv and centralized_log.csv to generate comparison metrics
and plots (results_comparison.png).

Usage:
  ./scripts/analyze_runs.py
  ./scripts/analyze_runs.py --auction auction_log.csv --centralized centralized_log.csv --output results_comparison.png
"""

import sys
from pathlib import Path

ws_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ws_dir / 'src' / 'arjuna_auction'))

from arjuna_auction.analyze_runs import main

if __name__ == '__main__':
    main()
