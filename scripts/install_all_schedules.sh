#!/bin/bash
# Install all suggestion automation launchd jobs on your Mac:
# post-close scan (3:45 PM), EOD score (3:50 PM), morning list (8:50 AM), nightly prep, reminders.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Installing stock-analyzer autopilot schedules from $ROOT"
bash "$ROOT/scripts/install_post_close_scan.sh"
bash "$ROOT/scripts/install_eod_schedule.sh"
bash "$ROOT/scripts/install_morning_schedule.sh"
bash "$ROOT/scripts/install_prep_morning_nag.sh"
bash "$ROOT/scripts/install_nightly_schedule.sh"
bash "$ROOT/scripts/install_trade_selection_auto.sh"
bash "$ROOT/scripts/install_session_reminders.sh"
bash "$ROOT/scripts/install_live_alerts_schedule.sh"
bash "$ROOT/scripts/install_autopilot_health.sh"

echo ""
echo "All schedules installed. Set Mac timezone to Asia/Kolkata for IST."
echo "Unified uninstall: launchctl unload each plist in ~/Library/LaunchAgents/com.stockanalyzer.*"
