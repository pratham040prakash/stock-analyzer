"""T1/T2/T3 profit ladder with progressive stop-loss for MIS equity and options."""

from __future__ import annotations

from dataclasses import dataclass, field

NEAR_PCT = 0.35
LADDER_PARTIALS = (0.40, 0.30, 0.30)
OPTIONS_TARGET_MULTS = (1.5, 2.0, 2.5)
OPTIONS_STOP_MULT = 0.65


@dataclass
class TradeLadder:
    """Price ladder for equity MIS (long or short)."""

    side: str  # LONG | SHORT
    entry: float
    initial_stop: float
    targets: tuple[float, float, float]  # T1, T2, T3
    partials: tuple[float, float, float] = LADDER_PARTIALS
    stops_after: tuple[float, float, float] = field(default_factory=tuple)
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.stops_after:
            self.stops_after = self._default_stops_after()

    def _default_stops_after(self) -> tuple[float, float, float]:
        t1, t2, _t3 = self.targets
        if self.side == "LONG":
            return (self.entry, t1, t2)
        return (self.entry, t1, t2)

    @property
    def target(self) -> float:
        return self.targets[0]

    @property
    def target2(self) -> float:
        return self.targets[1]

    @property
    def target3(self) -> float:
        return self.targets[2]

    @property
    def stop_loss(self) -> float:
        return self.initial_stop


@dataclass
class OptionsLadder:
    """Premium ladder for index CE/PE MIS."""

    entry: float
    initial_stop: float
    targets: tuple[float, float, float]
    partials: tuple[float, float, float] = LADDER_PARTIALS
    stops_after: tuple[float, float, float] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.stops_after:
            e, t1, t2 = self.entry, self.targets[0], self.targets[1]
            self.stops_after = (e, t1, t2)

    @property
    def target(self) -> float:
        return self.targets[0]

    @property
    def target2(self) -> float:
        return self.targets[1]

    @property
    def target3(self) -> float:
        return self.targets[2]


@dataclass
class LadderStatus:
    symbol: str
    ltp: float | None
    stage: int  # 0 before T1, 1 after T1, 2 after T2, 3 at/after T3
    active_stop: float
    next_target: float | None
    label: str
    emoji: str
    detail: str
    ladder_note: str = ""


def _round_price(v: float) -> float:
    return round(v, 2)


def build_equity_ladder(
    side: str,
    entry: float,
    stop: float,
    target: float,
    *,
    pivot_r2: float | None = None,
    pivot_s2: float | None = None,
) -> TradeLadder:
    """T1 = written target; T2/T3 extend by risk (pivot-aware when available)."""
    risk = abs(entry - stop)
    if risk <= 0:
        risk = entry * 0.005

    if side == "SHORT":
        t1 = target
        t2 = min(entry - 2 * risk, t1 - risk * 0.5)
        if pivot_s2 and pivot_s2 < t1:
            t2 = pivot_s2
        t3 = min(entry - 3 * risk, t2 - risk)
        notes = [
            f"**T1 ₹{t1:,.2f}** — book **40%**; move stop to **breakeven ₹{entry:,.2f}**",
            f"**T2 ₹{t2:,.2f}** — book **30%**; move stop to **T1 ₹{t1:,.2f}**",
            f"**T3 ₹{t3:,.2f}** — exit remaining **30%**; trail stop at **T2 ₹{t2:,.2f}**",
        ]
        return TradeLadder(
            side="SHORT",
            entry=_round_price(entry),
            initial_stop=_round_price(stop),
            targets=(
                _round_price(t1),
                _round_price(t2),
                _round_price(t3),
            ),
            notes=notes,
        )

    t1 = target
    t2 = max(entry + 2 * risk, t1 + risk * 0.5)
    if pivot_r2 and pivot_r2 > t1:
        t2 = pivot_r2
    t3 = max(entry + 3 * risk, t2 + risk)
    notes = [
        f"**T1 ₹{t1:,.2f}** — book **40%**; move stop to **breakeven ₹{entry:,.2f}**",
        f"**T2 ₹{t2:,.2f}** — book **30%**; move stop to **T1 ₹{t1:,.2f}**",
        f"**T3 ₹{t3:,.2f}** — exit remaining **30%**; trail stop at **T2 ₹{t2:,.2f}**",
    ]
    return TradeLadder(
        side="LONG",
        entry=_round_price(entry),
        initial_stop=_round_price(stop),
        targets=(_round_price(t1), _round_price(t2), _round_price(t3)),
        notes=notes,
    )


def build_options_ladder(
    entry_premium: float,
    *,
    stop_mult: float = OPTIONS_STOP_MULT,
    target_mults: tuple[float, float, float] = OPTIONS_TARGET_MULTS,
) -> OptionsLadder:
    """Premium ladder: T1/T2/T3 multiples with stop ratcheting."""
    if entry_premium <= 0:
        return OptionsLadder(
            entry=0.0,
            initial_stop=0.0,
            targets=(0.0, 0.0, 0.0),
        )
    stop = _round_price(entry_premium * stop_mult)
    targets = tuple(_round_price(entry_premium * m) for m in target_mults)
    return OptionsLadder(
        entry=_round_price(entry_premium),
        initial_stop=stop,
        targets=targets,
    )


def _near(ltp: float, level: float) -> bool:
    if level <= 0:
        return False
    return abs(ltp - level) / level * 100 <= NEAR_PCT


def _stage_from_ltp(ltp: float, ladder: TradeLadder | OptionsLadder, *, long_bias: bool = True) -> int:
    t1, t2, t3 = ladder.targets
    if long_bias:
        if ltp >= t3:
            return 3
        if ltp >= t2:
            return 2
        if ltp >= t1:
            return 1
        return 0
    if ltp <= t3:
        return 3
    if ltp <= t2:
        return 2
    if ltp <= t1:
        return 1
    return 0


def stop_for_stage(ladder: TradeLadder | OptionsLadder, stage: int) -> float:
    """Stop to hold *after* stage N target is hit (stage 0 = initial)."""
    if stage <= 0:
        return ladder.initial_stop
    if stage == 1:
        return ladder.stops_after[0]
    if stage == 2:
        return ladder.stops_after[1]
    return ladder.stops_after[2]


def format_stop_trail_guide(ladder: TradeLadder | OptionsLadder, *, currency: bool = True) -> str:
    """Explicit stop ₹ to set on Kite after each target."""
    t1, t2, _t3 = ladder.targets
    s0 = ladder.initial_stop
    s1 = ladder.stops_after[0]
    s2 = ladder.stops_after[1]
    s3 = ladder.stops_after[2]

    def _fmt(v: float) -> str:
        return f"₹{v:,.2f}" if currency else f"{v:,.2f}"

    if isinstance(ladder, TradeLadder) and ladder.side == "SHORT":
        return (
            f"Before T1: stop **{_fmt(s0)}** · "
            f"after T1: **{_fmt(s1)}** (entry) · "
            f"after T2: **{_fmt(s2)}** (T1 {_fmt(t1)}) · "
            f"after T3: **{_fmt(s3)}** (T2 {_fmt(t2)}) — exit rest if hit"
        )
    return (
        f"Before T1: stop **{_fmt(s0)}** · "
        f"after T1: **{_fmt(s1)}** (entry) · "
        f"after T2: **{_fmt(s2)}** (T1 {_fmt(t1)}) · "
        f"after T3: **{_fmt(s3)}** (T2 {_fmt(t2)}) — exit rest if hit"
    )


def format_stop_trail_telegram(ladder: TradeLadder | OptionsLadder) -> str:
    t1, t2, t3 = ladder.targets
    s0, s1, s2, s3 = (
        ladder.initial_stop,
        ladder.stops_after[0],
        ladder.stops_after[1],
        ladder.stops_after[2],
    )
    if isinstance(ladder, OptionsLadder):
        return (
            f"Stop trail (prem):\n"
            f"· Start **₹{s0:,.2f}** → T1 hit → **₹{s1:,.2f}** (entry)\n"
            f"· T2 hit → **₹{s2:,.2f}** (T1 ₹{t1:,.2f})\n"
            f"· T3 hit → **₹{s3:,.2f}** (T2 ₹{t2:,.2f}), exit rest if breached"
        )
    return (
        f"Stop trail:\n"
        f"· Start **₹{s0:,.0f}** → T1 hit → **₹{s1:,.0f}** (entry)\n"
        f"· T2 hit → **₹{s2:,.0f}** (T1 ₹{t1:,.0f})\n"
        f"· T3 hit → **₹{s3:,.0f}** (T2 ₹{t2:,.0f}), exit rest if breached"
    )


def active_stop_for_stage(ladder: TradeLadder | OptionsLadder, stage: int) -> float:
    return stop_for_stage(ladder, stage)


def next_target_for_stage(ladder: TradeLadder | OptionsLadder, stage: int) -> float | None:
    if stage >= 3:
        return None
    return ladder.targets[stage]


def assess_equity_ladder(
    ltp: float | None,
    ladder: TradeLadder,
    *,
    symbol: str = "",
) -> LadderStatus:
    sym = symbol or "—"
    if ltp is None or ltp <= 0:
        return LadderStatus(
            sym, None, 0, ladder.initial_stop, ladder.targets[0],
            "LTP unavailable", "⚪", "Refresh or connect Kite for live price.",
        )

    long_bias = ladder.side == "LONG"
    stage = _stage_from_ltp(ltp, ladder, long_bias=long_bias)
    active_stop = active_stop_for_stage(ladder, stage)
    nxt = next_target_for_stage(ladder, stage)
    t1, t2, t3 = ladder.targets

    hit_stop = (long_bias and ltp <= active_stop) or (not long_bias and ltp >= active_stop)
    if hit_stop:
        label = "At/below stop" if long_bias else "At/above stop"
        return LadderStatus(
            sym, ltp, stage, active_stop, nxt, label, "🔴",
            f"LTP ₹{ltp:,.2f} — active stop ₹{active_stop:,.2f}. Exit per plan.",
            ladder_note=_ladder_note(ladder, stage),
        )

    if long_bias and _near(ltp, active_stop):
        return LadderStatus(
            sym, ltp, stage, active_stop, nxt, "Near stop", "🟠",
            f"LTP ₹{ltp:,.2f} approaching stop ₹{active_stop:,.2f}.",
            ladder_note=_ladder_note(ladder, stage),
        )

    if stage == 3 or (long_bias and ltp >= t3) or (not long_bias and ltp <= t3):
        trail = ladder.stops_after[2]
        return LadderStatus(
            sym, ltp, 3, active_stop, None, "T3 hit — exit rest", "🟢",
            f"T3 ₹{t3:,.2f} hit — book final **30%**. "
            f"Trail stop on remainder: **₹{trail:,.2f}** (T2). Exit if LTP ≤ that.",
            ladder_note=_ladder_note(ladder, 3),
        )
    if stage == 2:
        if long_bias and _near(ltp, t3):
            return LadderStatus(
                sym, ltp, 2, active_stop, t3, "Near T3", "🟢",
                f"LTP ₹{ltp:,.2f} approaching T3 ₹{t3:,.2f}. "
                f"Hold stop **₹{active_stop:,.2f}** (T1) until T3 books.",
                ladder_note=_ladder_note(ladder, 2),
            )
        return LadderStatus(
            sym, ltp, 2, active_stop, t3, "T2 hit — trail to T3", "🟢",
            f"T2 ₹{t2:,.2f} hit — book **30%**. "
            f"Move stop to **₹{active_stop:,.2f}** (T1). Next T3 **₹{t3:,.2f}**.",
            ladder_note=_ladder_note(ladder, 2),
        )
    if stage == 1:
        if long_bias and _near(ltp, t2):
            return LadderStatus(
                sym, ltp, 1, active_stop, t2, "Near T2", "🟢",
                f"LTP ₹{ltp:,.2f} approaching T2 ₹{t2:,.2f}.",
                ladder_note=_ladder_note(ladder, 1),
            )
        return LadderStatus(
            sym, ltp, 1, active_stop, t2, "T1 hit — book 40%", "🟢",
            f"T1 ₹{t1:,.2f} hit — book **40%**. "
            f"Move stop to **₹{active_stop:,.2f}** (entry). Next T2 **₹{t2:,.2f}**.",
            ladder_note=_ladder_note(ladder, 1),
        )

    if long_bias and _near(ltp, t1):
        return LadderStatus(
            sym, ltp, 0, active_stop, t1, "Near T1", "🟢",
            f"LTP ₹{ltp:,.2f} approaching T1 ₹{t1:,.2f}.",
            ladder_note=_ladder_note(ladder, 0),
        )
    if long_bias and ltp >= t1:
        return LadderStatus(
            sym, ltp, 1, active_stop, t2, "T1 hit — book 40%", "🟢",
            f"T1 ₹{t1:,.2f} hit — book **40%**. "
            f"Move stop to **₹{active_stop:,.2f}** (breakeven). Next T2 **₹{t2:,.2f}**.",
            ladder_note=_ladder_note(ladder, 1),
        )

    if _near(ltp, ladder.entry):
        return LadderStatus(
            sym, ltp, 0, active_stop, t1, "At entry", "🟡",
            f"LTP ₹{ltp:,.2f} at entry ₹{ladder.entry:,.2f}.",
            ladder_note=_ladder_note(ladder, 0),
        )

    if long_bias and ltp < ladder.entry and not _near(ltp, ladder.entry):
        return LadderStatus(
            sym, ltp, 0, active_stop, t1, "Below entry", "⚪",
            f"Wait — LTP ₹{ltp:,.2f} below entry ₹{ladder.entry:,.2f}.",
            ladder_note=_ladder_note(ladder, 0),
        )

    return LadderStatus(
        sym, ltp, 0, active_stop, t1, "In trade zone", "🔵",
        f"LTP ₹{ltp:,.2f} · T1 **₹{t1:,.2f}** · T2 **₹{t2:,.2f}** · T3 **₹{t3:,.2f}**.",
        ladder_note=_ladder_note(ladder, 0),
    )


def assess_options_ladder(
    premium: float | None,
    ladder: OptionsLadder,
    *,
    label: str = "",
) -> LadderStatus:
    return assess_equity_ladder(
        premium,
        TradeLadder(
            side="LONG",
            entry=ladder.entry,
            initial_stop=ladder.initial_stop,
            targets=ladder.targets,
            partials=ladder.partials,
            stops_after=ladder.stops_after,
        ),
        symbol=label,
    )


def _ladder_note(ladder: TradeLadder | OptionsLadder, stage: int) -> str:
    t1, t2, t3 = ladder.targets
    pct = int(ladder.partials[0] * 100), int(ladder.partials[1] * 100), int(ladder.partials[2] * 100)
    s0, s1, s2, s3 = (
        ladder.initial_stop,
        ladder.stops_after[0],
        ladder.stops_after[1],
        ladder.stops_after[2],
    )
    if stage == 0:
        return (
            f"T1 ₹{t1:,.2f} ({pct[0]}%) → T2 ₹{t2:,.2f} ({pct[1]}%) → T3 ₹{t3:,.2f} ({pct[2]}%) · "
            f"stop now **₹{s0:,.2f}**"
        )
    if stage == 1:
        return (
            f"After T1: stop **₹{s1:,.2f}** (entry) · aim T2 ₹{t2:,.2f} · "
            f"then stop **₹{s2:,.2f}** (T1)"
        )
    if stage == 2:
        return (
            f"After T2: stop **₹{s2:,.2f}** (T1) · aim T3 ₹{t3:,.2f} · "
            f"then trail **₹{s3:,.2f}** (T2)"
        )
    return f"After T3: trail stop **₹{s3:,.2f}** (T2) · exit remaining 30% if breached"


def format_equity_ladder_telegram(ladder: TradeLadder) -> str:
    t1, t2, t3 = ladder.targets
    return (
        f"T1 ₹{t1:,.0f} (40%) → T2 ₹{t2:,.0f} (30%) → T3 ₹{t3:,.0f} (30%)\n"
        f"{format_stop_trail_telegram(ladder)}"
    )


def format_options_ladder_telegram(ladder: OptionsLadder) -> str:
    t1, t2, t3 = ladder.targets
    return (
        f"T1 ₹{t1:,.2f} (40%) → T2 ₹{t2:,.2f} (30%) → T3 ₹{t3:,.2f} (30%)\n"
        f"{format_stop_trail_telegram(ladder)}"
    )


def ladder_exit_rules(ladder: TradeLadder) -> list[str]:
    rules = [
        f"**Initial stop:** ₹{ladder.initial_stop:,.2f} — full exit if hit before T1.",
    ]
    rules.extend(ladder.notes)
    rules.append("**Time exit:** square off any remainder before **3:20 PM IST**.")
    return rules
