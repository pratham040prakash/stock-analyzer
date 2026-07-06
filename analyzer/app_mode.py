"""App deployment mode — full local vs simplified cloud UX."""

from __future__ import annotations

import os


def is_simple_cloud_mode() -> bool:
    """
    Optional simplified nav (Suggestions + Track Record + Alpha AI only).
    Full nav is the default everywhere. Opt in with SIMPLE_CLOUD_MODE=1 in env/secrets.
    """
    override = os.getenv("SIMPLE_CLOUD_MODE", "").strip().lower()
    return override in ("1", "true", "yes", "on")
