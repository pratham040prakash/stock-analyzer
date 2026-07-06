#!/bin/bash
# Install macOS launchd job — MIS session reminders at 9:15, 15:15, 15:20 (local time / IST).

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.stockanalyzer.sessionreminders.plist"
VENV_PYTHON="$ROOT/.venv/bin/python"
SCRIPT="$ROOT/scripts/session_reminders.py"

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
  <string>com.stockanalyzer.sessionreminders</string>
  <key>ProgramArguments</key>
  <array>
    <string>$VENV_PYTHON</string>
    <string>$SCRIPT</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$ROOT</string>
  <key>StartCalendarInterval</key>
  <array>
    <dict>
      <key>Hour</key>
      <integer>9</integer>
      <key>Minute</key>
      <integer>15</integer>
    </dict>
    <dict>
      <key>Hour</key>
      <integer>15</integer>
      <key>Minute</key>
      <integer>15</integer>
    </dict>
    <dict>
      <key>Hour</key>
      <integer>15</integer>
      <key>Minute</key>
      <integer>20</integer>
    </dict>
  </array>
  <key>StandardOutPath</key>
  <string>$ROOT/logs/session_reminders.log</string>
  <key>StandardErrorPath</key>
  <string>$ROOT/logs/session_reminders.err</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "Installed: $PLIST"
echo "Runs daily at 9:15 AM, 3:15 PM, and 3:20 PM (system local time)."
echo "Test open: $VENV_PYTHON $SCRIPT open"
echo "Test square-off: $VENV_PYTHON $SCRIPT square_off"
echo "Logs: $ROOT/logs/session_reminders.log"
