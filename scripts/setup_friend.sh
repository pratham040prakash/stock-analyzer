#!/usr/bin/env bash
# One-command setup for beta testers (macOS / Linux)
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Stock Analyzer — setup"
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from template (optional: add Kite / Telegram later)."
fi

echo ""
echo "Start the app:"
echo "  source .venv/bin/activate && streamlit run app.py"
echo ""
echo "Open http://127.0.0.1:8501 → India (Auto) → Market Pulse"
echo "No Zerodha needed for basic testing (uses Yahoo Finance)."
