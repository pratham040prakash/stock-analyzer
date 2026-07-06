"""App deployment mode — full local vs simplified cloud UX."""

from __future__ import annotations

import os


def is_simple_cloud_mode() -> bool:
    """
    Streamlit Cloud: hide Research / More trading nav; nudge local run for NSE options.
    Override with SIMPLE_CLOUD_MODE=0 locally if you want full nav while testing cloud URL.
    """
    override = os.getenv("SIMPLE_CLOUD_MODE", "").strip().lower()
    if override in ("1", "true", "yes", "on"):
        return True
    if override in ("0", "false", "no", "off"):
        return False
    try:
        from analyzer.zerodha import kite_runs_on_cloud

        return kite_runs_on_cloud()
    except Exception:
        return False
