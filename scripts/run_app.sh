#!/usr/bin/env bash
# Run Stock Analyzer locally — use Safari/Chrome, not Cursor preview.
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
exec streamlit run app.py --server.address 127.0.0.1 --server.port 8501
