#!/bin/bash
# Install macOS launchd job — MIS EOD summary at 3:35 PM local time (set Mac to IST).

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.stockanalyzer.miseod.plist"
VENV_PYTHON="$ROOT/.venv/bin/python"
SCRIPT="$ROOT/scripts/mis_eod_summary.py"

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
  <string>com.stockanalyzer.miseod</string>
  <key>ProgramArguments</key>
  <array>
    <string>$VENV_PYTHON</string>
    <string>$SCRIPT</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$ROOT</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>15</integer>
    <key>Minute</key>
    <integer>35</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>$ROOT/logs/mis_eod_summary.log</string>
  <key>StandardErrorPath</key>
  <string>$ROOT/logs/mis_eod_summary.err</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "Installed: $PLIST"
echo "Runs daily at 3:35 PM (system local time)."
echo "Test now: $VENV_PYTHON $SCRIPT --force"
echo "Logs: $ROOT/logs/mis_eod_summary.log"
