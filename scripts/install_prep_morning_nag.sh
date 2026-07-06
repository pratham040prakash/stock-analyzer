#!/bin/bash
# Install macOS launchd — 8:45 AM prep incomplete Telegram nag.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.stockanalyzer.prepmorning.plist"
VENV_PYTHON="$ROOT/.venv/bin/python"
SCRIPT="$ROOT/scripts/prep_morning_nag.py"

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
  <string>com.stockanalyzer.prepmorning</string>
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
    <integer>8</integer>
    <key>Minute</key>
    <integer>45</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>$ROOT/logs/prep_morning_nag.log</string>
  <key>StandardErrorPath</key>
  <string>$ROOT/logs/prep_morning_nag.err</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "Installed: $PLIST"
echo "Runs daily at 8:45 AM (system local time)."
echo "Test now: $VENV_PYTHON $SCRIPT --force"
