#!/bin/bash
# Install macOS launchd — options CE/PE re-scan at 9:46 AM IST (after OR forms).

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.stockanalyzer.morning_options.plist"
VENV_PYTHON="$ROOT/.venv/bin/python"
SCRIPT="$ROOT/scripts/morning_options_rescan.py"

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
  <string>com.stockanalyzer.morning_options</string>
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
    <integer>9</integer>
    <key>Minute</key>
    <integer>46</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>$ROOT/logs/morning_options_rescan.log</string>
  <key>StandardErrorPath</key>
  <string>$ROOT/logs/morning_options_rescan.err</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "Installed: $PLIST"
echo "Runs daily at 9:46 AM (system local time — set Mac to IST)."
