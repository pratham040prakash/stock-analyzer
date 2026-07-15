"""Long-term wealth plan — SIP + trading pool split toward a crore goal."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.intraday_prefs import IntradayPrefs, load_intraday_prefs
from analyzer.sip_planner import future_value_sip, required_monthly_sip

IST = ZoneInfo("Asia/Kolkata")
DEFAULT_HORIZON_YEARS = 20
DEFAULT_ANNUAL_RETURN_PCT = 12.0


@dataclass
class WealthPhase:
    id: str
    title: str
    year_range: str
    target_net_worth_inr: float
    monthly_sip_inr: float
    trading_capital_inr: float
    focus: str
    checklist: list[str] = field(default_factory=list)


@dataclass
class WealthMilestone:
    year: int
    projected_corpus_inr: float
    label: str


@dataclass
class WealthPlan:
    goal_inr: float
    trading_capital_inr: float
    monthly_sip_inr: float
    monthly_income_inr: float | None
    horizon_years: int
    annual_return_pct: float
    required_sip_inr: float
    projected_corpus_inr: float
    progress_pct: float
    years_to_goal_at_current_sip: float | None
    phases: list[WealthPhase] = field(default_factory=list)
    milestones: list[WealthMilestone] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    this_week: list[str] = field(default_factory=list)
    trading_track_rules: list[str] = field(default_factory=list)


def _years_to_reach_goal(
    *,
    goal: float,
    monthly_sip: float,
    lump_sum: float,
    annual_return_pct: float,
    max_years: int = 40,
) -> float | None:
    if monthly_sip <= 0 and lump_sum < goal:
        return None
    for y in range(1, max_years + 1):
        fv = future_value_sip(
            monthly_sip,
            annual_return_pct,
            y * 12,
            lump_sum=lump_sum,
        )
        if fv >= goal:
            return float(y)
    return None


def _build_phases(
    *,
    trading_capital: float,
    monthly_sip: float,
    goal_inr: float,
) -> list[WealthPhase]:
    sip_early = max(monthly_sip, 3000.0)
    sip_mid = max(monthly_sip * 1.5, 15000.0)
    sip_late = max(monthly_sip * 2.5, 35000.0)

    return [
        WealthPhase(
            id="phase1",
            title="Survive & build base",
            year_range="Years 1–2",
            target_net_worth_inr=200_000,
            monthly_sip_inr=sip_early,
            trading_capital_inr=max(trading_capital, 20_000),
            focus="No options · equity MIS tiny · SIP on Coin",
            checklist=[
                "Emergency fund ₹50k in bank (separate from trading)",
                "6 months continuous SIP — never pause",
                "Console P&L only — coach screen is not profit",
                "1 trade max until 2 green journal days",
            ],
        ),
        WealthPhase(
            id="phase2",
            title="Compound seriously",
            year_range="Years 3–6",
            target_net_worth_inr=2_500_000,
            monthly_sip_inr=sip_mid,
            trading_capital_inr=max(trading_capital * 2, 50_000),
            focus="3–5 CNC stocks + index MF · MIS pool ≤ 5% net worth",
            checklist=[
                "Raise SIP with every salary hike",
                "No F&O until net worth > ₹5L and 12 months discipline",
                "Max 2 stock rotations per year",
            ],
        ),
        WealthPhase(
            id="phase3",
            title="Accelerate",
            year_range="Years 7–12",
            target_net_worth_inr=10_000_000,
            monthly_sip_inr=sip_late,
            trading_capital_inr=250_000,
            focus="50% index MF · 25% stocks · 15% debt · 10% US ETF",
            checklist=[
                "Invest 30–40% of each raise — not lifestyle upgrades",
                "Trading pool still capped at 5% of net worth",
            ],
        ),
        WealthPhase(
            id="phase4",
            title="Scale to goal",
            year_range="Years 13–20",
            target_net_worth_inr=goal_inr,
            monthly_sip_inr=max(sip_late, 50_000),
            trading_capital_inr=500_000,
            focus="₹50k–1L/month invested · compounding does heavy lifting",
            checklist=[
                "SIP never stops — even in bear markets",
                "Review allocation yearly — not daily",
            ],
        ),
    ]


def build_wealth_plan(
    *,
    prefs: IntradayPrefs | None = None,
    monthly_sip_inr: float | None = None,
    monthly_income_inr: float | None = None,
    horizon_years: int = DEFAULT_HORIZON_YEARS,
    annual_return_pct: float = DEFAULT_ANNUAL_RETURN_PCT,
    now: datetime | None = None,
) -> WealthPlan:
    """Personal ₹10 Cr (or custom) path from trading prefs + SIP inputs."""
    _ = now or datetime.now(IST)
    prefs = prefs or load_intraday_prefs()
    goal = prefs.wealth_goal_inr
    trading_capital = prefs.capital
    sip = monthly_sip_inr if monthly_sip_inr is not None else max(
        getattr(prefs, "monthly_sip_inr", 0.0) or 0.0,
        3000.0,
    )

    months = horizon_years * 12
    required = required_monthly_sip(
        goal,
        annual_return_pct,
        months,
        lump_sum=trading_capital,
    )
    projected = future_value_sip(
        sip,
        annual_return_pct,
        months,
        lump_sum=trading_capital,
    )
    progress = min(100.0, (projected / goal * 100) if goal > 0 else 0.0)
    years_hit = _years_to_reach_goal(
        goal=goal,
        monthly_sip=sip,
        lump_sum=trading_capital,
        annual_return_pct=annual_return_pct,
    )

    milestones: list[WealthMilestone] = []
    for y in (2, 5, 10, 15, horizon_years):
        if y > horizon_years:
            continue
        corp = future_value_sip(sip, annual_return_pct, y * 12, lump_sum=trading_capital)
        label = f"₹{corp/1e7:.2f} Cr" if corp >= 1_00_00_000 else f"₹{corp/1e5:.1f}L"
        milestones.append(WealthMilestone(year=y, projected_corpus_inr=corp, label=label))

    daily_target = round(trading_capital * prefs.min_daily_profit_pct / 100, 0)
    max_loss = round(trading_capital * prefs.max_risk_pct / 100, 0)

    rules = [
        f"Main engine: SIP ₹{sip:,.0f}/month — trading pool ₹{trading_capital:,.0f} stays small.",
        f"Need ~₹{required:,.0f}/month SIP for ₹{goal/1e7:.0f} Cr in {horizon_years} years @ {annual_return_pct:.0f}% (illustrative).",
        "Never fund trading losses by stopping SIP.",
        "Profit proof = Zerodha Console only.",
    ]
    if prefs.equity_only:
        rules.append("Equity-only mode — skip index CE/PE until Phase 2 net-worth gate.")

    trading_track = [
        f"Daily MIS goal +₹{daily_target:,.0f} · max loss ₹{max_loss:,.0f} (process, not guaranteed).",
        "1 trade max in beginner mode.",
        "ENTER only when coach says ENTER.",
        "Square off all MIS by 3:20 PM.",
    ]

    income_note = ""
    if monthly_income_inr and monthly_income_inr > 0:
        save_pct = sip / monthly_income_inr * 100
        income_note = f"Save rate {save_pct:.0f}% of ₹{monthly_income_inr:,.0f} income."

    this_week = [
        f"Start or confirm Coin SIP — ₹{sip:,.0f}/month minimum.",
        f"Trading capital on Kite: ₹{trading_capital:,.0f} — update in settings if wrong.",
        "Export Console P&L — equity + F&O — log one lesson in Track Record.",
        "Star 1 stock tonight in prep for tomorrow.",
    ]
    if income_note:
        this_week.insert(1, income_note)

    return WealthPlan(
        goal_inr=goal,
        trading_capital_inr=trading_capital,
        monthly_sip_inr=sip,
        monthly_income_inr=monthly_income_inr,
        horizon_years=horizon_years,
        annual_return_pct=annual_return_pct,
        required_sip_inr=required,
        projected_corpus_inr=projected,
        progress_pct=progress,
        years_to_goal_at_current_sip=years_hit,
        phases=_build_phases(
            trading_capital=trading_capital,
            monthly_sip=sip,
            goal_inr=goal,
        ),
        milestones=milestones,
        rules=rules,
        this_week=this_week,
        trading_track_rules=trading_track,
    )


def format_wealth_plan_text(plan: WealthPlan) -> str:
    lines = [
        f"₹{plan.goal_inr/1e7:.0f} Cr wealth plan",
        f"Trading pool: ₹{plan.trading_capital_inr:,.0f} · SIP: ₹{plan.monthly_sip_inr:,.0f}/mo",
        f"Projected in {plan.horizon_years}y @ {plan.annual_return_pct:.0f}%: ₹{plan.projected_corpus_inr:,.0f}",
        f"Required SIP for goal: ₹{plan.required_sip_inr:,.0f}/mo",
        "",
        "Phases:",
    ]
    for p in plan.phases:
        lines.append(f"  [{p.year_range}] {p.title} → ₹{p.target_net_worth_inr:,.0f}")
        for c in p.checklist:
            lines.append(f"      • {c}")
    lines.append("")
    lines.append("This week:")
    for w in plan.this_week:
        lines.append(f"  • {w}")
    return "\n".join(lines)
