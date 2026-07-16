"""Proof Canvas presentation models — AI-drawn structure evidence."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ZoneAnnotation:
    kind: str  # danger | supply | demand | reward | risk | uncertainty | invalidation | fossil
    price_top: float
    price_bottom: float
    human_label: str
    expand_label: str | None = None


@dataclass(frozen=True)
class PathAnnotation:
    kind: str  # expected | alternative | outcome
    points: tuple[tuple[float, float], ...]  # (price, bar_index_offset) normalized 0..1 x uses bar position


@dataclass(frozen=True)
class PriceMarkers:
    entry: float | None = None
    stop: float | None = None
    target: float | None = None
    current: float | None = None


@dataclass(frozen=True)
class CandleBar:
    time: str
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class StructureProof:
    symbol: str
    verdict_state: str  # trade | wait | pause | rest
    proof_mode: str  # trade | wait | pause | rest | ask | fossil
    echo_line: str
    mentor_line: str
    action_line: str
    zones: tuple[ZoneAnnotation, ...]
    paths: tuple[PathAnnotation, ...] = ()
    markers: PriceMarkers = field(default_factory=PriceMarkers)
    price_min: float = 0.0
    price_max: float = 1.0
    timeframe: str = "15m"
    fossil_date: str | None = None
    fossil_badge: str | None = None
    learning_note: str | None = None
    candles: tuple[CandleBar, ...] = ()
    primary_label: str = "Back to Today"
    origin: str = "today"  # today | trades | ask | trust
    blur_candles: bool = True
    chart_opacity: float = 1.0
