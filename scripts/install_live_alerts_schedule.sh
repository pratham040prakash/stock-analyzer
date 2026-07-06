#!/bin/bash
# Install macOS launchd — live entry/stop/target alerts every 5 min (no app open needed).

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.stockanalyzer.livealerts.plist"
VENV_PYTHON="$ROOT/.venv/bin/python"
SCRIPT="$ROOT/scripts/watchlist_live_alerts.py"

if [[ ! -x "$VENV_PYTHON" ]]; then
  VENV_PYTHON="$(command -v python3)"
fi

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$ROOT/logs"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.stockanalyzer.livealerts</string>
  <key>ProgramArguments</key>
  <array>
    <string>$VENV_PYTHON</string>
    <string>$SCRIPT</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$ROOT</string>
  <key>StartInterval</key>
  <integer>300</integer>
  <key>StandardOutPath</key>
  <string>$ROOT/logs/watchlist_live_alerts.log</string>
  <key>StandardErrorPath</key>
  <string>$ROOT/logs/watchlist_live_alerts.err</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "Installed: $PLIST"
echo "Polls every 5 minutes (alerts only during NSE open hours on trading days)."
echo "Test now: $VENV_PYTHON $SCRIPT"
echo "Logs: $ROOT/logs/watchlist_live_alerts.log"
