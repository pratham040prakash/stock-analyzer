"""APEX architecture guardrails and legacy lifecycle registry (APEX-012)."""

from analyzer.architecture.legacy_lifecycle import (
    LEGACY_MODULE_REGISTRY,
    LegacyLifecycle,
    lifecycle_marker,
)

__all__ = [
    "LEGACY_MODULE_REGISTRY",
    "LegacyLifecycle",
    "lifecycle_marker",
]
