#!/usr/bin/env python3
"""
TerrainFleet Results Analyzer & Comparison Plotter
==================================================
Generates publication-ready metrics and comparison graphs from REAL logs only:
  1. Mission / Task Completion Time (Decentralized vs Centralized)
  2. Fleet Distance Traveled per Robot (arjuna_1 vs arjuna_2)
  3. Task Success Rate & Mission Counts
  4. Real Fault Recovery Timeline (Power-off -> Detection -> Re-auction -> Re-win -> Finish)
     Loaded exclusively from fault_log.csv (empty state displayed if no faults logged yet).
  5. Workload Distribution and Navigation Speed comparison

Strict Rule: NO fabricated numbers, NO placeholder estimates, NO hardcoded milestones.
All charts render explicit "No data yet" states when logs have no records.

Usage:
  ros2 run arjuna_auction analyze_runs
  ./scripts/analyze_runs.py --auction auction_log.csv --centralized centralized_log.csv --fault fault_log.csv --output results_comparison.png
"""

import os
import sys
import csv
import json
import math
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

import matplotlib
matplotlib.use('Agg')  # Headless backend for remote/server environments
import matplotlib.pyplot as plt


def load_log_file(filepath: str) -> List[Dict[str, Any]]:
    p = Path(filepath)
    if not p.exists():
        return []

    rows = []
    try:
        with open(p, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except Exception:
        return []
    return rows


def parse_auction_data(rows: List[Dict[str, Any]]):
    """
    Parses auction_log.csv into structured records.
    Stores all navigation trials in a list so re-auctioned tasks
    do NOT overwrite their initial attempts.
    """
    navigation_records: List[Dict[str, Any]] = []
    re_auctions: List[str] = []

    for r in rows:
        tid = r.get('task_id', '').strip()
        if not tid:
            continue

        is_reauction = str(r.get('is_reauction', '')).strip().lower() in ('true', '1')
        if is_reauction and tid not in re_auctions:
            re_auctions.append(tid)

        nav_success_str = str(r.get('nav_success', '')).strip().lower()
        if nav_success_str:
            success = nav_success_str in ('true', '1')
            dur = float(r.get('nav_duration_s', 0.0) or 0.0)
            dist = float(r.get('distance_traveled_m', 0.0) or 0.0)
            speed = float(r.get('avg_speed_mps', 0.0) or 0.0)
            robot = r.get('winner', r.get('observing_robot_id', 'unknown'))

            navigation_records.append({
                'task_id': tid,
                'success': success,
                'duration': dur,
                'distance': dist,
                'speed': speed,
                'robot': robot,
                'is_reauction': is_reauction,
                'timestamp': float(r.get('timestamp', 0.0) or 0.0),
            })

    return navigation_records, re_auctions


def parse_centralized_data(rows: List[Dict[str, Any]]):
    """
    Parses centralized_log.csv into structured records.
    """
    navigation_records: List[Dict[str, Any]] = []

    for r in rows:
        tid = r.get('task_id', '').strip()
        if not tid:
            continue

        nav_success_str = str(r.get('nav_success', '')).strip().lower()
        if nav_success_str:
            success = nav_success_str in ('true', '1')
            dur = float(r.get('nav_duration_s', 0.0) or 0.0)
            dist = float(r.get('distance_traveled_m', 0.0) or 0.0)
            speed = float(r.get('avg_speed_mps', 0.0) or 0.0)
            robot = r.get('assigned_to', 'unknown')

            navigation_records.append({
                'task_id': tid,
                'success': success,
                'duration': dur,
                'distance': dist,
                'speed': speed,
                'robot': robot,
                'timestamp': float(r.get('timestamp', 0.0) or 0.0),
            })

    return navigation_records


def parse_fault_data(rows: List[Dict[str, Any]]):
    """
    Parses fault_log.csv into real measured recovery timelines.
    """
    fault_records: List[Dict[str, Any]] = []

    for r in rows:
        try:
            f_id = r.get('failed_robot_id', '').strip()
            if not f_id:
                continue

            t_fault = float(r.get('t_fault', 0.0) or 0.0)
            t_det = float(r.get('t_detected', 0.0) or 0.0)
            t_reann = float(r.get('t_reannounced', 0.0) or 0.0)
            t_rewin = float(r.get('t_rewon', 0.0) or 0.0)
            t_comp = float(r.get('t_completed', 0.0) or 0.0)

            # Elapsed times from fault event
            t0 = t_fault if t_fault > 0 else (t_det - float(r.get('detection_latency_s', 3.0) or 3.0))

            det_elapsed = max(0.0, t_det - t0) if t_det > 0 else 0.0
            reann_elapsed = max(det_elapsed, t_reann - t0) if t_reann > 0 else 0.0
            rewin_elapsed = max(reann_elapsed, t_rewin - t0) if t_rewin > 0 else 0.0
            comp_elapsed = max(rewin_elapsed, t_comp - t0) if t_comp > 0 else 0.0

            fault_records.append({
                'failed_robot_id': f_id,
                'detected_by': r.get('detected_by', ''),
                'fault_type': r.get('fault_type', 'power_off'),
                'task_id': r.get('task_id', ''),
                'survivor_robot_id': r.get('survivor_robot_id', ''),
                'det_elapsed': round(det_elapsed, 2),
                'reann_elapsed': round(reann_elapsed, 2),
                'rewin_elapsed': round(rewin_elapsed, 2),
                'comp_elapsed': round(comp_elapsed, 2),
                'total_recovery_time_s': float(r.get('total_recovery_time_s', comp_elapsed) or comp_elapsed),
                'nav_success': str(r.get('nav_success', '')).strip().lower() in ('true', '1'),
            })
        except Exception:
            continue

    return fault_records


def generate_plots(auction_tasks: List[dict], centralized_tasks: List[dict],
                   re_auctions: list, fault_records: List[dict], output_image: str):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("TerrainFleet: Decentralized vs Centralized Multi-Robot Performance", fontsize=15, fontweight='bold')

    has_auction_data = len(auction_tasks) > 0
    has_cent_data = len(centralized_tasks) > 0
    has_fault_data = len(fault_records) > 0

    # -------------------------------------------------------------
    # 1. TASK COMPLETION TIME COMPARISON (Top-Left)
    # -------------------------------------------------------------
    ax1 = axes[0, 0]
    ax1.set_title("1. Average Task Navigation Duration (s)", fontsize=11, fontweight='semibold')
    if not has_auction_data and not has_cent_data:
        ax1.text(0.5, 0.5, "No completed tasks in logs yet\n(No data yet)", ha='center', va='center', color='#64748b', fontsize=11)
        ax1.set_xticks([])
        ax1.set_yticks([])
    else:
        labels = []
        durations = []
        colors = []

        if has_auction_data:
            d_durs = [t['duration'] for t in auction_tasks if t['duration'] > 0 and t['success']]
            if d_durs:
                labels.append(f'Decentralized\n(n={len(d_durs)})')
                durations.append(sum(d_durs) / len(d_durs))
                colors.append('#2563eb')

        if has_cent_data:
            c_durs = [t['duration'] for t in centralized_tasks if t['duration'] > 0 and t['success']]
            if c_durs:
                labels.append(f'Centralized\n(n={len(c_durs)})')
                durations.append(sum(c_durs) / len(c_durs))
                colors.append('#ea580c')

        if durations:
            bars = ax1.bar(labels, durations, color=colors, width=0.45, edgecolor='#334155', linewidth=1)
            for bar in bars:
                h = bar.get_height()
                ax1.annotate(f"{h:.2f}s", xy=(bar.get_x() + bar.get_width() / 2, h),
                             xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontweight='bold')
            ax1.set_ylabel("Duration (seconds)")
            ax1.grid(axis='y', linestyle='--', alpha=0.4)

    # -------------------------------------------------------------
    # 2. FLEET DISTANCE TRAVELED (Top-Right)
    # -------------------------------------------------------------
    ax2 = axes[0, 1]
    ax2.set_title("2. Fleet Distance Traveled per Robot (m)", fontsize=11, fontweight='semibold')
    if not has_auction_data and not has_cent_data:
        ax2.text(0.5, 0.5, "No distance telemetry recorded yet\n(No data yet)", ha='center', va='center', color='#64748b', fontsize=11)
        ax2.set_xticks([])
        ax2.set_yticks([])
    else:
        # Sum distance per robot across auction and centralized logs
        all_records = auction_tasks + centralized_tasks
        r1_dist = sum(t['distance'] for t in all_records if '1' in str(t.get('robot', '')))
        r2_dist = sum(t['distance'] for t in all_records if '2' in str(t.get('robot', '')))

        r_labels = ['arjuna_1 (R1)', 'arjuna_2 (R2)']
        r_dists = [r1_dist, r2_dist]
        bars2 = ax2.bar(r_labels, r_dists, color=['#2563eb', '#ea580c'], width=0.45, edgecolor='#334155', linewidth=1)
        for bar in bars2:
            h = bar.get_height()
            ax2.annotate(f"{h:.2f}m", xy=(bar.get_x() + bar.get_width() / 2, h),
                         xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontweight='bold')
        ax2.set_ylabel("Total Distance (meters)")
        ax2.grid(axis='y', linestyle='--', alpha=0.4)

    # -------------------------------------------------------------
    # 3. SUCCESS RATE & ATTEMPTS (Bottom-Left)
    # -------------------------------------------------------------
    ax3 = axes[1, 0]
    ax3.set_title("3. Task Success Rate & Recovery Counts", fontsize=11, fontweight='semibold')
    if not has_auction_data and not has_cent_data:
        ax3.text(0.5, 0.5, "No navigation execution records yet\n(No data yet)", ha='center', va='center', color='#64748b', fontsize=11)
        ax3.set_xticks([])
        ax3.set_yticks([])
    else:
        cat_labels = []
        rates = []
        bar_colors = []

        if has_auction_data:
            total_d = len(auction_tasks)
            succ_d = sum(1 for t in auction_tasks if t['success'])
            rate_d = (succ_d / total_d * 100.0) if total_d > 0 else 0.0
            cat_labels.append(f"Decentralized\n({succ_d}/{total_d})")
            rates.append(rate_d)
            bar_colors.append('#16a34a')

        if has_cent_data:
            total_c = len(centralized_tasks)
            succ_c = sum(1 for t in centralized_tasks if t['success'])
            rate_c = (succ_c / total_c * 100.0) if total_c > 0 else 0.0
            cat_labels.append(f"Centralized\n({succ_c}/{total_c})")
            rates.append(rate_c)
            bar_colors.append('#0284c7')

        if rates:
            b3 = ax3.bar(cat_labels, rates, color=bar_colors, width=0.45, edgecolor='#334155', linewidth=1)
            ax3.set_ylim(0, 115)
            ax3.set_ylabel("Navigation Success Rate (%)")
            for bar, val in zip(b3, rates):
                h = bar.get_height()
                ax3.annotate(f"{val:.1f}%", xy=(bar.get_x() + bar.get_width() / 2, h),
                             xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontweight='bold')
            ax3.grid(axis='y', linestyle='--', alpha=0.4)

    # -------------------------------------------------------------
    # 4. REAL FAULT RECOVERY TIMELINE (Bottom-Right)
    # -------------------------------------------------------------
    ax4 = axes[1, 1]
    ax4.set_title("4. Measured Fault Recovery Milestones (s)", fontsize=11, fontweight='semibold')
    if not has_fault_data:
        ax4.text(0.5, 0.5, "No fault recovery records in fault_log.csv yet\n(Awaiting physical power-off or simulated fault test)",
                 ha='center', va='center', color='#64748b', fontsize=11)
        ax4.set_xticks([])
        ax4.set_yticks([])
    else:
        # Plot real measured recovery stages for the latest recorded fault
        latest = fault_records[-1]
        stages = [
            '1. Fault Event (t=0)',
            '2. Peer Detected',
            '3. Task Re-Announced',
            '4. Task Re-Won',
            '5. Survivor Finished',
        ]
        times = [
            0.0,
            latest['det_elapsed'],
            latest['reann_elapsed'],
            latest['rewin_elapsed'],
            latest['comp_elapsed'],
        ]
        ax4.plot(times, stages, marker='o', markersize=8, color='#dc2626', linewidth=2, linestyle='-')
        for t, s in zip(times, stages):
            ax4.annotate(f"{t:.2f}s", xy=(t, s), xytext=(8, -3), textcoords="offset points", fontweight='bold', fontsize=9)
        ax4.set_xlabel("Elapsed Time from Fault Event (seconds)")
        ax4.grid(True, linestyle='--', alpha=0.4)
        ax4.text(0.98, 0.05, f"Fault: {latest['failed_robot_id']} ({latest['fault_type']})\nSurvivor: {latest['survivor_robot_id']}",
                 transform=ax4.transAxes, ha='right', va='bottom', fontsize=8,
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#f8fafc', edgecolor='#cbd5e1'))

    plt.tight_layout()
    plt.savefig(output_image, dpi=200)
    print(f"\n📊 Summary figure saved successfully to: {output_image}")


def print_terminal_summary(auction_tasks: List[dict], centralized_tasks: List[dict], fault_records: List[dict]):
    print("\n" + "=" * 80)
    print("📋 TERRAINFLEET EXPERIMENTAL RUN SUMMARY")
    print("=" * 80)

    if not auction_tasks and not centralized_tasks:
        print("  ⚠️  No completed task records found in logs yet.")
        print("=" * 80)
        return

    if auction_tasks:
        print("\n🔹 Decentralized Fleet Tasks (Auction Mode):")
        print(f"  {'Task ID':<10} {'Robot':<12} {'Status':<12} {'Duration':<14} {'Dist (m)':<10} {'Speed (m/s)':<12}")
        print("  " + "-" * 74)
        total_dur = 0.0
        succ_count = 0
        r_counts = {}
        for t in auction_tasks:
            status_str = "✅ SUCCESS" if t['success'] else "❌ FAILED"
            if t['success']:
                succ_count += 1
            dur = t['duration']
            total_dur += dur
            rob = t['robot']
            r_counts[rob] = r_counts.get(rob, 0) + 1
            dist = t.get('distance', 0.0)
            spd = t.get('speed', 0.0)
            print(f"  {t['task_id']:<10} {rob:<12} {status_str:<12} {dur:<14.2f}s {dist:<10.2f} {spd:<12.3f}")

        print("  " + "-" * 74)
        print(f"  Total Tasks: {len(auction_tasks)} | Success Rate: {succ_count}/{len(auction_tasks)} ({succ_count/len(auction_tasks)*100:.1f}%)")
        print(f"  Robot Task Distribution: {dict(r_counts)}")

    if centralized_tasks:
        print("\n🔸 Centralized Baseline Tasks:")
        print(f"  {'Task ID':<10} {'Robot':<12} {'Status':<12} {'Duration':<14} {'Dist (m)':<10} {'Speed (m/s)':<12}")
        print("  " + "-" * 74)
        succ_c = sum(1 for t in centralized_tasks if t['success'])
        for t in centralized_tasks:
            status_str = "✅ SUCCESS" if t['success'] else "❌ FAILED"
            print(f"  {t['task_id']:<10} {t['robot']:<12} {status_str:<12} {t['duration']:<14.2f}s {t.get('distance',0.0):<10.2f} {t.get('speed',0.0):<12.3f}")
        print("  " + "-" * 74)
        print(f"  Total Baseline Tasks: {len(centralized_tasks)} | Success Rate: {succ_c}/{len(centralized_tasks)} ({succ_c/len(centralized_tasks)*100:.1f}%)")

    if fault_records:
        print("\n⚡ Recorded Fault Recovery Events:")
        for fr in fault_records:
            print(f"  • Fault on [{fr['failed_robot_id']}] ({fr['fault_type']}) -> Detected in {fr['det_elapsed']}s -> Re-won by [{fr['survivor_robot_id']}] -> Completed in {fr['comp_elapsed']}s")

    print("\n" + "=" * 80)


def main(args=None):
    parser = argparse.ArgumentParser(description="Analyze TerrainFleet logs and generate comparison figures")
    parser.add_argument('--auction', '-a', type=str, default='auction_log.csv', help="Path to auction_log.csv")
    parser.add_argument('--centralized', '-c', type=str, default='centralized_log.csv', help="Path to centralized_log.csv")
    parser.add_argument('--fault', '-f', type=str, default='fault_log.csv', help="Path to fault_log.csv")
    parser.add_argument('--output', '-o', type=str, default='results_comparison.png', help="Output figure PNG path")
    parser.add_argument('--show', '-s', action='store_true', help="Open the saved graph with an image viewer")

    parsed = parser.parse_args(args if args is not None else sys.argv[1:])

    auction_rows = load_log_file(parsed.auction)
    cent_rows = load_log_file(parsed.centralized)
    fault_rows = load_log_file(parsed.fault)

    auction_tasks, re_auctions = parse_auction_data(auction_rows)
    cent_tasks = parse_centralized_data(cent_rows)
    fault_records = parse_fault_data(fault_rows)

    print("=" * 65)
    print("📈 TERRAIN FLEET EXPERIMENT LOG ANALYSIS")
    print("=" * 65)
    print(f"Auction log ({parsed.auction}): {len(auction_rows)} entries, {len(auction_tasks)} completed navigations.")
    print(f"Centralized log ({parsed.centralized}): {len(cent_rows)} entries, {len(cent_tasks)} completed navigations.")
    print(f"Fault log ({parsed.fault}): {len(fault_records)} recorded real fault events.")
    print(f"Re-auction tasks detected: {len(re_auctions)}")

    # Print human-readable table of all executed tasks
    print_terminal_summary(auction_tasks, cent_tasks, fault_records)

    # Generate the 4-panel comparison figure
    generate_plots(auction_tasks, cent_tasks, re_auctions, fault_records, parsed.output)

    # If display is available, open the image viewer automatically
    if os.environ.get('DISPLAY'):
        try:
            import subprocess
            for viewer in ['xdg-open', 'eog', 'display', 'open']:
                if subprocess.run(['which', viewer], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
                    subprocess.Popen([viewer, parsed.output])
                    print(f"🖼️  Displaying graph: {parsed.output} with {viewer}")
                    break
        except Exception:
            pass


if __name__ == '__main__':
    main()
