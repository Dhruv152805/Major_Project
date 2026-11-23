/**
 * ARJUNA // Autonomous Fleet Telemetry & Bidding Dashboard
 * Minimalist, Real-Time Controller for Arjuna 1 & Arjuna 2
 */

let currentStatusData = null;
let activeDetailRobot = 'arjuna_1';
let activeView = 'dashboard';
let pollInterval = null;

// ================= INITIALIZATION =================
document.addEventListener('DOMContentLoaded', () => {
  pollStatus();
  pollInterval = setInterval(pollStatus, 800);

  // Close modal on escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeRobotDetailModal();
      closeInjectTaskModal();
    }
  });

  // Close modal on backdrop click
  const detailModal = document.getElementById('robotDetailModal');
  if (detailModal) {
    detailModal.addEventListener('click', (e) => {
      if (e.target === detailModal) closeRobotDetailModal();
    });
  }

  const injectModal = document.getElementById('injectTaskModal');
  if (injectModal) {
    injectModal.addEventListener('click', (e) => {
      if (e.target === injectModal) closeInjectTaskModal();
    });
  }
});

// ================= VIEW SWITCHER (DASHBOARD, LOGS, MAINTENANCE) =================
function switchView(viewName) {
  activeView = viewName;
  const btnDash = document.getElementById('tabBtn-dashboard');
  const btnLogs = document.getElementById('tabBtn-logs');
  const btnMaint = document.getElementById('tabBtn-maintenance');
  const viewDash = document.getElementById('view-dashboard');
  const viewLogs = document.getElementById('view-logs');
  const viewMaint = document.getElementById('view-maintenance');

  if (btnDash) btnDash.classList.toggle('active', viewName === 'dashboard');
  if (btnLogs) btnLogs.classList.toggle('active', viewName === 'logs');
  if (btnMaint) btnMaint.classList.toggle('active', viewName === 'maintenance');

  if (viewDash) viewDash.style.display = (viewName === 'dashboard') ? 'block' : 'none';
  if (viewLogs) viewLogs.style.display = (viewName === 'logs') ? 'block' : 'none';
  if (viewMaint) viewMaint.style.display = (viewName === 'maintenance') ? 'block' : 'none';

  if (currentStatusData) {
    if (viewName === 'logs') {
      renderHistoricalLogs(currentStatusData);
    } else if (viewName === 'maintenance') {
      renderMaintenance(currentStatusData);
    } else {
      renderTaskComparisonTable(currentStatusData);
    }
  }
}

// ================= TELEMETRY POLLING =================
async function pollStatus() {
  try {
    const res = await fetch('/api/status', { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    currentStatusData = data;

    updateConnectionStatus(true);
    renderDashboard(data);
  } catch (err) {
    updateConnectionStatus(false);
  }
}

function updateConnectionStatus(online) {
  const connDot = document.getElementById('connDot');
  const connText = document.getElementById('connText');
  if (connDot && connText) {
    if (online) {
      connDot.className = 'status-indicator-dot dot-green';
      connText.textContent = 'Live Telemetry';
    } else {
      connDot.className = 'status-indicator-dot dot-grey';
      connText.textContent = 'Connecting...';
    }
  }
}

// ================= MAIN RENDER PIPELINE =================
function renderDashboard(data) {
  renderRobotCards(data);
  renderTaskComparisonTable(data);
  renderFormulaComparisonTable(data);
  renderHistoricalLogs(data);
  renderMaintenance(data);

  if (activeDetailRobot && document.getElementById('robotDetailModal')?.style.display === 'flex') {
    renderRobotDetailModalContent(activeDetailRobot, data);
  }
}

// ================= STATUS & BATTERY HELPERS =================
// Rule 1:
// - Grey: When the robot is switched off (OFF)
// - Green: When the robot is switched on but has not been assigned any task (IDLE)
// - Red: When the robot is switched on and actively performing a task (ENGAGED)
function getRobotStatus(r) {
  const isOnline = Boolean(r && r.online && !r.soft_killed);
  const activeTask = r ? r.active_task : null;

  if (!isOnline) {
    return {
      status: 'OFF',
      power: 'OFF',
      label: 'OFF',
      conditionText: 'Switched Off',
      color: 'grey',
      dotClass: 'dot-grey',
      badgeClass: 'badge-grey',
      desc: 'Robot is switched off (no heartbeat)'
    };
  } else if (!activeTask) {
    return {
      status: 'IDLE',
      power: 'ON',
      label: 'IDLE',
      conditionText: 'Switched On • Idle',
      color: 'green',
      dotClass: 'dot-green',
      badgeClass: 'badge-green',
      desc: 'Switched on & standing by (unassigned)'
    };
  } else {
    return {
      status: 'ENGAGED',
      power: 'ON',
      label: 'ENGAGED',
      conditionText: `Switched On • Engaged in ${activeTask}`,
      color: 'red',
      dotClass: 'dot-red',
      badgeClass: 'badge-red',
      desc: `Actively executing ${activeTask}`
    };
  }
}

function getEffectiveBattery(r) {
  if (!r) return null;
  if (r.battery_override !== null && r.battery_override !== undefined) {
    const val = Number(r.battery_override);
    return val <= 1.0 ? val * 100.0 : val;
  }
  if (r.battery_pct !== null && r.battery_pct !== undefined) {
    return Number(r.battery_pct);
  }
  return null;
}

// ================= 1. ROBOT STATUS DISPLAY =================
function renderRobotCards(data) {
  const container = document.getElementById('robotCardsContainer');
  if (!container || !data.robots) return;

  const robotIds = ['arjuna_1', 'arjuna_2'];
  const robots = robotIds.map(id => data.robots[id]).filter(Boolean);

  container.innerHTML = robots.map(r => {
    const isR1 = (r.id === 'arjuna_1');
    const dispName = isR1 ? 'Arjuna 1' : 'Arjuna 2';
    const accentClass = isR1 ? 'r1-accent' : 'r2-accent';
    const avatarClass = isR1 ? 'av-r1' : 'av-r2';
    const avatarText = isR1 ? 'A1' : 'A2';
    const st = getRobotStatus(r);

    // Live battery percentage (no fake values)
    const effBat = getEffectiveBattery(r);
    const hasBat = (effBat !== null && !isNaN(effBat));
    let batValText = '--';
    let batBarWidth = 0;
    let batClass = 'offline';
    let batNote = 'No sensor topic';

    if (hasBat) {
      batValText = `${effBat.toFixed(1)}%`;
      batBarWidth = Math.min(100, Math.max(0, effBat));
      if (effBat < 10.0) {
        batClass = 'critical';
        batNote = 'Critical (< 10%, m = 0)';
      } else if (effBat < 25.0) {
        batClass = 'low';
        batNote = 'Low charge';
      } else {
        batClass = 'normal';
        batNote = 'Healthy charge';
      }
    }

    // Currently assigned task
    const activeTaskDisp = r.active_task ? `Task ${escapeHtml(r.active_task)}` : 'Idle';

    // Position coordinates
    let posText = '--';
    if (r.position && typeof r.position.x === 'number') {
      posText = `${r.position.x.toFixed(1)}, ${r.position.y.toFixed(1)}`;
    }

    return `
      <div class="robot-card-interactive ${accentClass}" id="robotCard-${r.id}" onclick="openRobotDetailModal('${r.id}')" title="Click to view detailed parameters &amp; bidding formula for ${dispName}">
        <div class="card-top-bar">
          <div class="robot-title-cluster">
            <div class="robot-avatar ${avatarClass}">${avatarText}</div>
            <div>
              <div class="robot-title-text">${dispName}</div>
              <div class="robot-id-tag mono">${escapeHtml(r.id)}</div>
            </div>
          </div>

          <!-- Status Indicator: Grey for OFF, Green for IDLE, Red for ENGAGED -->
          <span class="status-badge-custom ${st.badgeClass}">
            <span class="status-indicator-dot ${st.dotClass}"></span>
            <span>${st.label}</span>
          </span>
        </div>

        <!-- Live Battery Box -->
        <div class="robot-battery-box">
          <div class="battery-header">
            <div class="battery-label-cluster">
              <span class="battery-icon">⚡</span>
              <span class="battery-label-text">Battery Level</span>
            </div>
            <span class="battery-pct-large ${hasBat ? '' : 'text-offline'}">${batValText}</span>
          </div>
          <div class="battery-track">
            <div class="battery-level-bar ${batClass}" style="width: ${batBarWidth}%;"></div>
          </div>
          <div class="battery-sub-info">
            <span>${batNote}</span>
            <span class="mono">${hasBat ? `${batBarWidth.toFixed(0)}%` : 'Offline'}</span>
          </div>
        </div>

        <!-- Operational Status, Task & Position -->
        <div class="robot-quick-metrics">
          <div class="metric-pill-box">
            <span class="metric-pill-label">Status</span>
            <span class="metric-pill-val ${st.color === 'red' ? 'text-crimson' : (st.color === 'grey' ? 'text-grey' : 'text-emerald')}">
              ${escapeHtml(st.conditionText)}
            </span>
          </div>

          <div class="metric-pill-box">
            <span class="metric-pill-label">Assignment</span>
            <span class="metric-pill-val ${r.active_task ? 'text-primary bold' : 'text-muted'}">
              ${escapeHtml(activeTaskDisp)}
            </span>
          </div>

          <div class="metric-pill-box">
            <span class="metric-pill-label">Pose (X, Y)</span>
            <span class="metric-pill-val mono text-xs">
              ${posText}
            </span>
          </div>
        </div>

        <div class="card-action-cue">
          <span>View parameters &amp; active bid</span>
          <span class="arrow-icon">&rarr;</span>
        </div>
      </div>
    `;
  }).join('');
}

// ================= 2. TASK BIDDING COMPARISON TABLE (CURRENT SESSION ONLY) =================
// Strictly empty by default. Displays ONLY current session or newly generated bids!
function renderTaskComparisonTable(data) {
  const tbody = document.getElementById('taskComparisonBody');
  if (!tbody) return;

  const rows = data.comparison_table || [];
  // Ensure only live session rows are rendered here; historical logs belong in the Logs tab
  const liveRows = rows.filter(item => item && !item.is_historical);
  if (liveRows.length === 0) {
    tbody.innerHTML = `
      <tr class="empty-row"><td colspan="5">
        <div class="empty-state-card">
          <div class="empty-state-icon">📋</div>
          <div class="empty-state-title">No task bidding records in current session</div>
          <div class="empty-state-desc">Live auction bids and winner comparisons will appear here in real-time when a task is announced. Past session records are available under the <strong>Logs</strong> tab.</div>
        </div>
      </td></tr>`;
    return;
  }

  tbody.innerHTML = liveRows.map(item => renderComparisonRowHtml(item)).join('');
}

// ================= 3. COMPARATIVE TABLE: OLD VS ENHANCED FORMULA =================
function renderFormulaComparisonTable(data) {
  const tbody = document.getElementById('formulaComparisonBody');
  if (!tbody) return;

  const rows = data.formula_comparison_table || [];
  if (rows.length === 0) {
    tbody.innerHTML = `<tr class="empty-row"><td colspan="6">Loading formula comparison data...</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(r => {
    const isMZero = (r.m_variable === 0);
    const mBadge = isMZero
      ? '<span class="m-badge-pill m-zero">m = 0</span>'
      : '<span class="m-badge-pill m-active">m = 1</span>';

    const oldBidStr = (r.old_bid !== null && r.old_bid !== undefined) ? Number(r.old_bid).toFixed(3) : '<span class="text-muted">-- (Standing by)</span>';
    const enhBidStr = (r.enhanced_bid !== null && r.enhanced_bid !== undefined)
      ? Number(r.enhanced_bid).toFixed(3)
      : (isMZero ? '<span class="mono text-crimson bold">0.000</span>' : '<span class="text-muted">-- (Standing by)</span>');

    let outcomePill = '';
    if (isMZero) {
      outcomePill = '<span class="impact-save-pill">🛡️ PREVENTED MID-MISSION STALL</span>';
    } else if (r.badge_type === 'offline') {
      outcomePill = '<span class="impact-normal-pill" style="background:#f1f5f9;color:#475569;border-color:#cbd5e1;">STANDBY</span>';
    } else {
      outcomePill = '<span class="impact-normal-pill">✓ ELIGIBLE BIDDER</span>';
    }

    return `
      <tr>
        <td>
          <strong>${escapeHtml(r.target)}</strong>
        </td>
        <td>
          <span class="mono bold ${r.battery_pct !== null && r.battery_pct < 10 ? 'text-crimson' : (r.battery_pct !== null ? 'text-emerald' : 'text-muted')}">
            ${escapeHtml(r.battery_display)}
          </span>
        </td>
        <td>
          ${mBadge}
        </td>
        <td>
          <span class="mono bold">${oldBidStr}</span>
        </td>
        <td>
          <span class="mono bold ${isMZero ? 'text-crimson' : 'text-emerald'}">${enhBidStr}</span>
          ${isMZero ? ' <span class="badge badge-crimson" style="font-size:9px;padding:1px 4px;">DISQUALIFIED</span>' : ''}
        </td>
        <td class="impact-cell">
          ${outcomePill}
          <div class="text-xs text-muted mt-1">${escapeHtml(r.status_impact)}</div>
        </td>
      </tr>
    `;
  }).join('');
}

// ================= LOGS TAB: ALL HISTORICAL RECORDS =================
function renderHistoricalLogs(data) {
  const tbody = document.getElementById('historicalTaskComparisonBody');
  const countBadge = document.getElementById('logsCountBadge');
  const eventContainer = document.getElementById('eventLogContainer');

  const rows = data.historical_comparison_table || [];

  if (countBadge) {
    countBadge.textContent = `${rows.length} Historical Records`;
  }

  if (tbody) {
    if (rows.length === 0) {
      tbody.innerHTML = `
        <tr class="empty-row"><td colspan="5">
          <div class="empty-state-card">
            <div class="empty-state-icon">📜</div>
            <div class="empty-state-title">No historical bidding records found</div>
            <div class="empty-state-desc">Past task auction logs will appear here once recorded to auction_log.csv.</div>
          </div>
        </td></tr>`;
    } else {
      tbody.innerHTML = rows.map(item => renderComparisonRowHtml(item)).join('');
    }
  }

  if (eventContainer && data.events_log) {
    if (data.events_log.length === 0) {
      eventContainer.innerHTML = `<div class="empty-state">No telemetry events logged yet.</div>`;
    } else {
      eventContainer.innerHTML = data.events_log.slice(0, 50).map(e => `
        <div class="event-log-row ${escapeHtml(e.severity || 'info')}">
          <span class="event-time mono">${escapeHtml(e.timestamp)}</span>
          <span class="event-text">${escapeHtml(e.text)}</span>
        </div>
      `).join('');
    }
  }
}

// ================= 4. MAINTENANCE MONITOR =================
function renderMaintenance(data) {
  const cardsContainer = document.getElementById('maintenanceCardsContainer');
  const tbody = document.getElementById('maintenanceComparisonBody');
  const fleetBadge = document.getElementById('maintFleetStatusBadge');

  const maint = data.maintenance;
  if (!maint || !maint.robots) return;

  const robotIds = ['arjuna_1', 'arjuna_2'];
  const robots = robotIds.map(id => maint.robots[id]).filter(Boolean);

  // Update fleet status badge
  if (fleetBadge && maint.fleet_summary) {
    if (maint.fleet_summary.any_maintenance_required) {
      fleetBadge.className = 'badge badge-crimson mono';
      fleetBadge.textContent = '⚠️ Service Alert: Maintenance Required';
    } else if (maint.fleet_summary.any_maintenance_due_soon) {
      fleetBadge.className = 'badge badge-amber mono';
      fleetBadge.textContent = '⚡ Service Due Soon';
    } else {
      fleetBadge.className = 'badge badge-emerald mono';
      fleetBadge.textContent = '✓ All Systems Operational';
    }
  }

  // Render Side-by-Side Maintenance Cards
  if (cardsContainer) {
    cardsContainer.innerHTML = robots.map(r => {
      const isR1 = (r.robot_id === 'arjuna_1');
      const dispName = r.robot_display || (isR1 ? 'Arjuna 1' : 'Arjuna 2');
      const accentClass = isR1 ? 'r1-accent' : 'r2-accent';

      const isReq = (r.status === 'required');
      const isSoon = (r.status === 'due_soon');
      const statusBadge = isReq
        ? '<span class="status-badge-custom badge-red"><span class="status-indicator-dot dot-red"></span> MAINTENANCE NEEDED</span>'
        : (isSoon
          ? '<span class="status-badge-custom badge-amber"><span class="status-indicator-dot dot-amber"></span> SERVICE DUE SOON</span>'
          : '<span class="status-badge-custom badge-green"><span class="status-indicator-dot dot-green"></span> HEALTHY (NO SERVICE NEEDED)</span>');

      const hoursLimit = r.total_hours_threshold || 50.0;
      const distLimit = r.distance_threshold_m || 500.0;
      const tasksLimit = r.tasks_threshold || 25;

      const hoursPct = Math.min(100, Math.max(0, ((r.total_hours || 0) / hoursLimit) * 100));
      const distPct = Math.min(100, Math.max(0, ((r.total_distance_m || 0) / distLimit) * 100));
      const tasksPct = Math.min(100, Math.max(0, ((r.tasks_completed || 0) / tasksLimit) * 100));

      const hoursBarColor = hoursPct >= 100 ? 'bar-red' : (hoursPct >= 80 ? 'bar-amber' : 'bar-blue');
      const distBarColor = distPct >= 100 ? 'bar-red' : (distPct >= 80 ? 'bar-amber' : 'bar-blue');
      const tasksBarColor = tasksPct >= 100 ? 'bar-red' : (tasksPct >= 80 ? 'bar-amber' : 'bar-blue');

      return `
        <div class="maintenance-robot-card ${accentClass}">
          <div class="card-top-bar">
            <div class="robot-title-cluster">
              <span class="robot-title-text">${dispName}</span>
              <span class="robot-id-tag">${escapeHtml(r.robot_id)}</span>
            </div>
            ${statusBadge}
          </div>

          <!-- 4 Core Metrics Grid -->
          <div class="maint-metrics-grid">
            <!-- 1. Total Hours Worked -->
            <div class="maint-metric-box">
              <div class="maint-metric-header">
                <span class="maint-metric-label">Total Hours Worked</span>
                <span class="maint-metric-thresh mono">Limit: ${hoursLimit} hrs</span>
              </div>
              <div class="maint-metric-val mono">${Number(r.total_hours || 0).toFixed(2)} <span class="maint-unit">hrs</span></div>
              <div class="maint-progress-track">
                <div class="maint-progress-fill ${hoursBarColor}" style="width: ${hoursPct.toFixed(1)}%;"></div>
              </div>
              <div class="maint-metric-footer">
                <span>${hoursPct.toFixed(1)}% of threshold</span>
                <span class="${hoursPct >= 100 ? 'text-crimson bold' : (hoursPct >= 80 ? 'text-amber bold' : 'text-emerald')}">${hoursPct >= 100 ? 'Exceeded' : 'Within Limit'}</span>
              </div>
            </div>

            <!-- 2. Total Time Worked -->
            <div class="maint-metric-box">
              <div class="maint-metric-header">
                <span class="maint-metric-label">Total Time Worked</span>
                <span class="maint-metric-thresh mono">Runtime Meter</span>
              </div>
              <div class="maint-metric-val mono time-val">${escapeHtml(r.total_time_formatted || '0h 00m 00s')}</div>
              <div class="maint-metric-subtext">
                Continuous active runtime accumulator
              </div>
            </div>

            <!-- 3. Total Distance Traveled -->
            <div class="maint-metric-box">
              <div class="maint-metric-header">
                <span class="maint-metric-label">Distance Traveled</span>
                <span class="maint-metric-thresh mono">Limit: ${distLimit} m</span>
              </div>
              <div class="maint-metric-val mono">${Number(r.total_distance_m || 0).toFixed(1)} <span class="maint-unit">m</span></div>
              <div class="maint-progress-track">
                <div class="maint-progress-fill ${distBarColor}" style="width: ${distPct.toFixed(1)}%;"></div>
              </div>
              <div class="maint-metric-footer">
                <span>${distPct.toFixed(1)}% of threshold</span>
                <span class="${distPct >= 100 ? 'text-crimson bold' : (distPct >= 80 ? 'text-amber bold' : 'text-emerald')}">${distPct >= 100 ? 'Exceeded' : 'Within Limit'}</span>
              </div>
            </div>

            <!-- 4. Tasks Completed -->
            <div class="maint-metric-box">
              <div class="maint-metric-header">
                <span class="maint-metric-label">Tasks Completed</span>
                <span class="maint-metric-thresh mono">Limit: ${tasksLimit} tasks</span>
              </div>
              <div class="maint-metric-val mono">${r.tasks_completed || 0} <span class="maint-unit">tasks</span></div>
              <div class="maint-progress-track">
                <div class="maint-progress-fill ${tasksBarColor}" style="width: ${tasksPct.toFixed(1)}%;"></div>
              </div>
              <div class="maint-metric-footer">
                <span>${tasksPct.toFixed(1)}% of threshold</span>
                <span class="${tasksPct >= 100 ? 'text-crimson bold' : (tasksPct >= 80 ? 'text-amber bold' : 'text-emerald')}">${tasksPct >= 100 ? 'Exceeded' : 'Within Limit'}</span>
              </div>
            </div>
          </div>

          <!-- Alert / Health Footer Note -->
          <div class="maint-card-footer ${isReq ? 'footer-alert' : (isSoon ? 'footer-warn' : 'footer-good')}">
            <span class="footer-icon">${isReq ? '⚠️' : (isSoon ? '⚡' : '🛡️')}</span>
            <div class="footer-text">
              ${isReq
                ? `<strong>Maintenance Needed:</strong> ${escapeHtml(r.reasons.join('; '))}`
                : (isSoon
                  ? '<strong>Attention:</strong> Robot is approaching scheduled service thresholds (&ge; 80%).'
                  : '<strong>All Systems Operational:</strong> Operating hours and robot telemetry are safely within maintenance limits.')}
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  // Render Maintenance Comparison Table
  if (tbody) {
    tbody.innerHTML = robots.map(r => {
      const isR1 = (r.robot_id === 'arjuna_1');
      const dispName = r.robot_display || (isR1 ? 'Arjuna 1' : 'Arjuna 2');
      const isReq = (r.status === 'required');
      const isSoon = (r.status === 'due_soon');

      const statusPill = isReq
        ? '<span class="badge badge-crimson bold">SERVICE NEEDED</span>'
        : (isSoon ? '<span class="badge badge-amber bold">DUE SOON</span>' : '<span class="badge badge-emerald bold">HEALTHY</span>');

      return `
        <tr>
          <td>
            <strong>${escapeHtml(dispName)}</strong>
            <span class="text-xs text-muted mono ml-1">(${escapeHtml(r.robot_id)})</span>
          </td>
          <td>
            <span class="mono bold">${Number(r.total_hours || 0).toFixed(2)} hrs</span>
            <span class="text-xs text-muted mono"> / ${r.total_hours_threshold || 50.0} hrs</span>
          </td>
          <td>
            <span class="mono bold text-primary">${escapeHtml(r.total_time_formatted || '0h 00m 00s')}</span>
          </td>
          <td>
            <span class="mono bold">${Number(r.total_distance_m || 0).toFixed(1)} m</span>
            <span class="text-xs text-muted mono"> / ${r.distance_threshold_m || 500.0} m</span>
          </td>
          <td>
            <span class="mono bold">${r.tasks_completed || 0}</span>
            <span class="text-xs text-muted mono"> / ${r.tasks_threshold || 25}</span>
          </td>
          <td>
            ${statusPill}
          </td>
        </tr>
      `;
    }).join('');
  }
}

// Helper: Render Comparison Row HTML
function renderComparisonRowHtml(item) {
  const tid = item.task_id;
  const taskDisp = item.task_display || tid;
  const b1 = item.bid_arjuna_1;
  const b2 = item.bid_arjuna_2;
  const winner = item.winner;
  const winnerDisp = item.winner_display || (winner === 'arjuna_1' ? 'Arjuna 1' : (winner === 'arjuna_2' ? 'Arjuna 2' : '--'));
  const diff = item.difference;

  const b1Str = (b1 !== null && b1 !== undefined) ? Number(b1).toFixed(3) : (item.is_reauction && winner === 'arjuna_2' ? '<span class="text-muted">Offline</span>' : '--');
  const b2Str = (b2 !== null && b2 !== undefined) ? Number(b2).toFixed(3) : (item.is_reauction && winner === 'arjuna_1' ? '<span class="text-muted">Offline</span>' : '--');
  const diffStr = (diff !== null && diff !== undefined) ? Number(diff).toFixed(3) : '--';
  const winnerClass = (winner === 'arjuna_1') ? 'arjuna_1' : ((winner === 'arjuna_2') ? 'arjuna_2' : '');

  return `
    <tr onclick="openRobotDetailModal('${winner || 'arjuna_1'}')" style="cursor: pointer;" title="Click to view robot details">
      <td>
        <span class="task-id-badge">${escapeHtml(taskDisp)}</span>
        ${item.is_reauction ? '<span class="badge badge-amber" style="font-size:10px;margin-left:4px;">RE-AUCTION</span>' : ''}
      </td>
      <td>
        <span class="bid-val-text mono ${winner === 'arjuna_1' ? 'winning' : ''}">${b1Str}</span>
        ${winner === 'arjuna_1' ? ' <span style="color:#10b981;font-weight:700;">✓</span>' : ''}
      </td>
      <td>
        <span class="bid-val-text mono ${winner === 'arjuna_2' ? 'winning' : ''}">${b2Str}</span>
        ${winner === 'arjuna_2' ? ' <span style="color:#10b981;font-weight:700;">✓</span>' : ''}
      </td>
      <td>
        ${winner ? `<span class="winner-badge-pill ${winnerClass}">🏆 ${escapeHtml(winnerDisp)}</span>` : '<span class="text-muted">Pending...</span>'}
      </td>
      <td>
        <span class="diff-pill mono">${diffStr}</span>
      </td>
    </tr>
  `;
}

// ================= ROBOT DETAILED VIEW MODAL =================
function openRobotDetailModal(robotId) {
  activeDetailRobot = robotId || 'arjuna_1';
  const modal = document.getElementById('robotDetailModal');
  if (modal) {
    modal.style.display = 'flex';
  }
  selectDetailRobot(activeDetailRobot);
}

function closeRobotDetailModal() {
  const modal = document.getElementById('robotDetailModal');
  if (modal) {
    modal.style.display = 'none';
  }
}

function selectDetailRobot(robotId) {
  activeDetailRobot = robotId;
  const btn1 = document.getElementById('btnSwitchDetail-arjuna_1');
  const btn2 = document.getElementById('btnSwitchDetail-arjuna_2');
  if (btn1) btn1.classList.toggle('active', robotId === 'arjuna_1');
  if (btn2) btn2.classList.toggle('active', robotId === 'arjuna_2');

  const title = document.getElementById('robotDetailTitle');
  if (title) {
    const dispName = (robotId === 'arjuna_1') ? 'Arjuna 1' : 'Arjuna 2';
    title.innerHTML = `Robot Detailed View // <span class="mono bold text-primary">${dispName}</span>`;
  }

  if (currentStatusData) {
    renderRobotDetailModalContent(robotId, currentStatusData);
  }
}

function renderRobotDetailModalContent(robotId, data) {
  const container = document.getElementById('robotDetailModalBody');
  if (!container || !data.robots) return;

  const r = data.robots[robotId];
  if (!r) {
    container.innerHTML = `<div class="p-4 text-muted">Robot telemetry for ${escapeHtml(robotId)} not found.</div>`;
    return;
  }

  const isR1 = (robotId === 'arjuna_1');
  const dispName = isR1 ? 'Arjuna 1' : 'Arjuna 2';
  const st = getRobotStatus(r);

  // Live battery percentage
  const effBat = getEffectiveBattery(r);
  const hasBat = (effBat !== null && !isNaN(effBat));
  const batStr = hasBat ? `${effBat.toFixed(1)}%` : 'Offline (No sensor topic)';

  // Assigned task
  const activeTask = r.active_task || 'None (Idle)';

  // Measured & calculated parameters
  const params = r.live_bid_params || {};
  const hasActiveTask = Boolean(params.has_active_task);
  const rx = params.robot_x !== undefined ? params.robot_x : 0.0;
  const ry = params.robot_y !== undefined ? params.robot_y : 0.0;
  const wd = params.w_distance || 1.0;
  const wb = params.w_battery || 5.0;
  const wf = params.w_failure || 2.0;
  const batFrac = params.battery_fraction !== null && params.battery_fraction !== undefined ? params.battery_fraction : (hasBat ? (effBat / 100.0) : 1.0);
  const batCost = params.bat_cost !== undefined ? params.bat_cost : (wb * (1.0 - batFrac));
  const m = (params.m_variable !== undefined) ? params.m_variable : ((hasBat && effBat < 10.0) ? 0 : 1);
  const failures = params.failures || 0;
  const failCost = params.fail_cost !== undefined ? params.fail_cost : (wf * failures);
  const busyPenalty = params.busy_penalty !== undefined ? params.busy_penalty : (r.active_task ? 1000.0 : 0.0);
  const reauctPenalty = params.reauct_penalty || 0.0;

  let distStr = '--';
  let distCostStr = '--';
  let oldBidStr = '--';
  let enhBidStr = '--';
  let stepSubStr = 'No active task auction underway. Robot is standing by.';

  if (hasActiveTask && params.distance !== null && params.distance !== undefined) {
    const dist = params.distance;
    const distCost = params.dist_cost;
    const baseCost = params.base_cost;
    const finalBid = params.enhanced_bid;

    distStr = `${dist.toFixed(3)} m`;
    distCostStr = distCost.toFixed(3);
    oldBidStr = baseCost.toFixed(3);
    enhBidStr = finalBid.toFixed(3);
    stepSubStr = params.calculated_step_by_step || `Bid = ${m} × ${baseCost.toFixed(3)} = ${finalBid.toFixed(3)}`;
  }

  // Submitted bid from actual auction
  let submittedBidVal = '--';
  let submittedBidMeta = 'No auction bid submitted in active session';
  let isWonAuction = null;

  if (r.last_submitted_bid && r.last_submitted_bid.bid !== undefined) {
    submittedBidVal = Number(r.last_submitted_bid.bid).toFixed(3);
    isWonAuction = r.last_submitted_bid.won;
    const taskName = r.last_submitted_bid.task_id || 'Active Task';
    submittedBidMeta = isWonAuction === true
      ? `Won auction for ${taskName}`
      : (isWonAuction === false ? `Outbid on ${taskName}` : `Submitted for ${taskName}`);
  }

  container.innerHTML = `
    <!-- Telemetry Banner -->
    <div class="detail-telemetry-banner">
      <div class="detail-metric-card">
        <span class="dm-label">Live Battery Percentage</span>
        <span class="dm-val mono ${hasBat && effBat < 10 ? 'text-crimson' : (hasBat ? 'text-emerald' : 'text-muted')}">${batStr}</span>
        <span class="text-xs text-muted">Topic: /${escapeHtml(robotId)}/battery_state</span>
      </div>

      <div class="detail-metric-card">
        <span class="dm-label">Current Robot Status</span>
        <span class="dm-val ${st.color === 'red' ? 'text-crimson' : (st.color === 'grey' ? 'text-grey' : 'text-emerald')}">
          <span class="status-indicator-dot ${st.dotClass}"></span>
          <span>${st.status}</span>
        </span>
        <span class="text-xs text-muted">${st.power} • ${st.conditionText}</span>
      </div>

      <div class="detail-metric-card">
        <span class="dm-label">Currently Assigned Task</span>
        <span class="dm-val ${r.active_task ? 'text-primary bold' : 'text-muted'}">${escapeHtml(activeTask)}</span>
        <span class="text-xs text-muted">Active fleet allocation</span>
      </div>

      <div class="detail-metric-card">
        <span class="dm-label">Live Position</span>
        <span class="dm-val mono">(${rx.toFixed(2)}, ${ry.toFixed(2)}) m</span>
        <span class="text-xs text-muted">Map coordinate frame</span>
      </div>
    </div>

    <!-- Bidding Formula Comparison & Evaluation -->
    <div class="detail-formula-section">
      <div class="formula-card-title">
        <span>🧮</span>
        <span>The Bidding Formula &amp; Mathematical Evaluation</span>
      </div>

      <div class="formula-display-math">
        <strong>Old Bid Formula:</strong> Bid<sub>old</sub> = (w<sub>distance</sub> · D) + (w<sub>battery</sub> · (1 - B)) + (w<sub>failure</sub> · F) + P<sub>busy</sub> + P<sub>reauct</sub><br>
        <strong>Enhanced Bid Formula:</strong> Bid<sub>enhanced</sub> = <strong>m</strong> × Bid<sub>old</sub>
        <span style="margin-left: 10px; font-size: 11.5px; color: var(--text-muted);">(m = 0 if Battery &lt; 10%, else 1)</span>
      </div>

      <div class="formula-eval-math">
        <strong>Live Parameter Substitution for ${dispName}:</strong><br>
        <pre style="margin: 4px 0 0 0; font-family: inherit; white-space: pre-wrap;">${escapeHtml(stepSubStr)}</pre>
      </div>
    </div>

    <!-- All Measured & Calculated Parameters -->
    <div class="panel-card" style="margin-bottom: 20px;">
      <div class="panel-header compact">
        <div class="panel-title-group">
          <span class="panel-icon">📐</span>
          <h4 class="panel-title text-sm">All Measured &amp; Calculated Bidding Parameters</h4>
        </div>
        <span class="badge badge-subtle mono">${hasActiveTask ? `Target: ${escapeHtml(params.target_task_id)}` : 'No active auction'}</span>
      </div>

      <div class="table-wrapper">
        <table class="detail-params-table">
          <thead>
            <tr>
              <th>Parameter</th>
              <th>Symbol</th>
              <th>Actual Measured Value</th>
              <th>Configured Weight / Rule</th>
              <th>Calculated Cost Contribution</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Euclidean Distance</strong></td>
              <td class="mono">D</td>
              <td class="mono">${distStr}</td>
              <td class="mono">w_distance = ${wd.toFixed(1)}</td>
              <td class="mono bold text-primary">${distCostStr}</td>
            </tr>
            <tr>
              <td><strong>Battery Depletion</strong></td>
              <td class="mono">B, (1 - B)</td>
              <td class="mono">${hasBat ? `${effBat.toFixed(1)}% (B = ${batFrac.toFixed(2)})` : 'Sensor Offline (B = 1.00)'}</td>
              <td class="mono">w_battery = ${wb.toFixed(1)}</td>
              <td class="mono bold text-primary">${batCost.toFixed(3)}</td>
            </tr>
            <tr>
              <td><strong>Safety Multiplier Variable</strong></td>
              <td class="mono">m</td>
              <td class="mono bold ${m === 0 ? 'text-crimson' : 'text-emerald'}">${m}</td>
              <td class="text-xs">0 if Battery &lt; 10%, else 1</td>
              <td>${m === 0 ? '<span class="badge badge-crimson">m = 0 (Disqualified)</span>' : '<span class="badge badge-emerald">m = 1 (Eligible)</span>'}</td>
            </tr>
            <tr>
              <td><strong>Past Failure History</strong></td>
              <td class="mono">F</td>
              <td class="mono">${failures} failures recorded</td>
              <td class="mono">w_failure = ${wf.toFixed(1)}</td>
              <td class="mono bold">${failCost.toFixed(3)}</td>
            </tr>
            <tr>
              <td><strong>Active Task Penalty</strong></td>
              <td class="mono">P_busy</td>
              <td class="mono">${r.active_task ? `Engaged in ${r.active_task}` : 'None (Idle)'}</td>
              <td class="mono">+1000.0 if engaged</td>
              <td class="mono bold ${busyPenalty > 0 ? 'text-crimson' : ''}">${busyPenalty.toFixed(1)}</td>
            </tr>
            <tr>
              <td><strong>Re-Auction Penalty</strong></td>
              <td class="mono">P_reauct</td>
              <td class="mono">0.000</td>
              <td class="mono">+1000.0 if failed peer</td>
              <td class="mono bold">${reauctPenalty.toFixed(1)}</td>
            </tr>
            <tr style="background-color: var(--bg-subtle); font-weight: 700;">
              <td><strong>Old Formula Bid (Base Cost)</strong></td>
              <td class="mono">Bid_old</td>
              <td colspan="2" class="mono text-xs">(w_d·D) + (w_b·(1-B)) + (w_f·F) + Penalties</td>
              <td class="mono bold text-primary">${oldBidStr}</td>
            </tr>
            <tr style="background-color: #eff6ff; font-weight: 700;">
              <td><strong>Enhanced Formula Bid</strong></td>
              <td class="mono">Bid_enhanced</td>
              <td colspan="2" class="mono text-xs">m × Bid_old</td>
              <td class="mono bold text-emerald" style="font-size: 14px;">${enhBidStr}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- The Bid Submitted by the Robot -->
    <div class="submitted-bid-display">
      <div class="submitted-bid-info">
        <span class="submitted-bid-title">Actual Bid Submitted by ${dispName}</span>
        <span class="submitted-bid-score">${submittedBidVal}</span>
        <span class="submitted-bid-meta">${escapeHtml(submittedBidMeta)}</span>
      </div>
      <div>
        ${isWonAuction === true
      ? '<span class="badge badge-emerald bold" style="padding: 6px 14px; font-size: 13px;">🏆 WINNING ROBOT</span>'
      : (isWonAuction === false ? '<span class="badge badge-subtle" style="padding: 6px 14px; font-size: 13px;">OUTBID</span>' : '<span class="badge badge-subtle">STANDBY</span>')}
      </div>
    </div>
  `;
}

// ================= TASK ANNOUNCEMENT =================
function openInjectTaskModal() {
  const modal = document.getElementById('injectTaskModal');
  if (modal) modal.style.display = 'flex';
}

function closeInjectTaskModal() {
  const modal = document.getElementById('injectTaskModal');
  if (modal) modal.style.display = 'none';
}

async function submitInjectTask() {
  const tid = document.getElementById('inpTaskId')?.value.trim() || 'T07';
  const x = parseFloat(document.getElementById('inpTaskX')?.value || 1.5);
  const y = parseFloat(document.getElementById('inpTaskY')?.value || 2.0);

  try {
    const res = await fetch('/api/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        command: 'announce_task',
        task_id: tid,
        x: x,
        y: y,
        heading: 0.0
      })
    });
    if (res.ok) {
      closeInjectTaskModal();
      pollStatus();
    }
  } catch (err) {
    console.error('Error announcing task:', err);
  }
}

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
