"""SIP and financial-goals planner — projections, allocation, and milestones."""

from __future__ import annotations

from dataclasses import dataclass, field

GOAL_PRESETS: dict[str, str] = {
    "Wealth building": "Grow long-term corpus via disciplined monthly investing.",
    "Retirement": "Build a retirement nest egg over 15–25 years.",
    "House down payment": "Save for a home goal in 5–10 years.",
    "Child education": "Fund education expenses in 8–15 years.",
    "Emergency + invest": "Keep buffer, invest the rest systematically.",
    "Custom goal": "Define your own target and timeline.",
}

DEFAULT_GOAL_YEARS: dict[str, float] = {
    "Wealth building": 10.0,
    "Retirement": 20.0,
    "House down payment": 7.0,
    "Child education": 12.0,
    "Emergency + invest": 3.0,
    "Custom goal": 10.0,
}

DEFAULT_GOAL_AMOUNTS_INR: dict[str, float] = {
    "Wealth building": 50_00_000,
    "Retirement": 2_00_00_000,
    "House down payment": 30_00_000,
    "Child education": 40_00_000,
    "Emergency + invest": 10_00_000,
    "Custom goal": 25_00_000,
}

DEFAULT_GOAL_AMOUNTS_USD: dict[str, float] = {
    "Wealth building": 100_000,
    "Retirement": 1_000_000,
    "House down payment": 80_000,
    "Child education": 120_000,
    "Emergency + invest": 25_000,
    "Custom goal": 75_000,
}


@dataclass
class SipAllocationLine:
    ticker: str
    name: str
    weight_pct: float
    monthly_amount: float
    sleeve: str  # index | large_cap | sector | hedge | liquid
    note: str = ""


@dataclass
class SipMilestone:
    year: int
    months: int
    invested: float
    projected_corpus: float


@dataclass
class SipPlan:
    goal_name: str
    target_amount: float
    years: float
    months: int
    current_corpus: float
    monthly_sip: float
    monthly_budget: float | None
    annual_return_pct: float
    step_up_annual_pct: float
    risk_profile: str
    experience: str
    projected_corpus: float
    surplus_or_gap: float  # + surplus if budget > required, - gap if short
    allocation: list[SipAllocationLine] = field(default_factory=list)
    milestones: list[SipMilestone] = field(default_factory=list)
    tips: list[str] = field(default_factory=list)
    guidance: str = ""


@dataclass
class SipPlannerInput:
    goal_name: str
    target_amount: float
    years: float
    current_corpus: float = 0.0
    monthly_budget: float | None = None
    annual_return_pct: float = 12.0
    step_up_annual_pct: float = 0.0
    risk_profile: str = "balanced"
    experience: str = "new"
    market: str = "india"


def sip_input_to_dict(inp: SipPlannerInput) -> dict:
    return {
        "goal_name": inp.goal_name,
        "target_amount": inp.target_amount,
        "years": inp.years,
        "current_corpus": inp.current_corpus,
        "monthly_budget": inp.monthly_budget,
        "annual_return_pct": inp.annual_return_pct,
        "step_up_annual_pct": inp.step_up_annual_pct,
        "risk_profile": inp.risk_profile,
        "experience": inp.experience,
        "market": inp.market,
    }


def sip_input_from_dict(d: dict) -> SipPlannerInput:
    return SipPlannerInput(
        goal_name=d.get("goal_name", "Custom goal"),
        target_amount=float(d.get("target_amount", 0)),
        years=float(d.get("years", 10)),
        current_corpus=float(d.get("current_corpus", 0)),
        monthly_budget=d.get("monthly_budget"),
        annual_return_pct=float(d.get("annual_return_pct", 12)),
        step_up_annual_pct=float(d.get("step_up_annual_pct", 0)),
        risk_profile=d.get("risk_profile", "balanced"),
        experience=d.get("experience", "new"),
        market=d.get("market", "india"),
    )


def _months(years: float) -> int:
    return max(1, int(round(years * 12)))


def future_value_sip(
    monthly: float,
    annual_return_pct: float,
    months: int,
    *,
    lump_sum: float = 0.0,
    step_up_annual_pct: float = 0.0,
) -> float:
    """Project corpus with monthly SIP, optional lump sum, optional annual step-up."""
    if months <= 0:
        return lump_sum
    r = annual_return_pct / 100.0 / 12.0
    fv = float(lump_sum)
    payment = float(monthly)
    for m in range(months):
        if r == 0:
            fv += payment
        else:
            fv = fv * (1 + r) + payment
        if step_up_annual_pct and (m + 1) % 12 == 0:
            payment *= 1 + step_up_annual_pct / 100.0
    return round(fv, 2)


def total_invested(
    monthly: float,
    months: int,
    *,
    lump_sum: float = 0.0,
    step_up_annual_pct: float = 0.0,
) -> float:
    total = lump_sum
    payment = monthly
    for m in range(months):
        total += payment
        if step_up_annual_pct and (m + 1) % 12 == 0:
            payment *= 1 + step_up_annual_pct / 100.0
    return round(total, 2)


def required_monthly_sip(
    target: float,
    annual_return_pct: float,
    months: int,
    *,
    lump_sum: float = 0.0,
    step_up_annual_pct: float = 0.0,
) -> float:
    """Solve monthly SIP needed to reach target."""
    if target <= 0 or months <= 0:
        return 0.0
    if lump_sum >= target:
        return 0.0
    lo, hi = 0.0, max(target, 10_000.0)
    while future_value_sip(hi, annual_return_pct, months, lump_sum=lump_sum, step_up_annual_pct=step_up_annual_pct) < target:
        hi *= 2
        if hi > 10_000_000:
            break
    for _ in range(64):
        mid = (lo + hi) / 2
        fv = future_value_sip(mid, annual_return_pct, months, lump_sum=lump_sum, step_up_annual_pct=step_up_annual_pct)
        if fv < target:
            lo = mid
        else:
            hi = mid
    return round(hi, 0)


def _india_allocation(risk_profile: str, experience: str) -> list[tuple[str, str, float, str, str]]:
    """ticker, name, weight%, sleeve, note."""
    if risk_profile == "conservative":
        rows = [
            ("NIFTYBEES.NS", "Nifty Bees (Nifty 50 ETF)", 75.0, "index", "Core index SIP — diversify in one fund"),
            ("LIQUIDBEES.NS", "Liquid Bees ETF", 15.0, "liquid", "Park 1–2 months SIP here if markets are extended"),
            ("GOLDBEES.NS", "Gold Bees ETF", 5.0, "hedge", "Small hedge vs inflation / rupee shock"),
            ("RELIANCE.NS", "Reliance (large cap example)", 5.0, "large_cap", "Optional single-name sleeve — research first"),
        ]
    elif risk_profile == "growth":
        rows = [
            ("NIFTYBEES.NS", "Nifty Bees (Nifty 50 ETF)", 40.0, "index", "Core index base"),
            ("JUNIORBEES.NS", "Junior Bees (midcap ETF)", 15.0, "sector", "Higher risk / return midcap exposure"),
            ("ITBEES.NS", "IT Bees ETF", 10.0, "sector", "Sector tilt — only if you understand cyclicality"),
            ("TCS.NS", "TCS", 10.0, "large_cap", "Quality large cap — stagger entries"),
            ("HDFCBANK.NS", "HDFC Bank", 10.0, "large_cap", "Financials exposure"),
            ("RELIANCE.NS", "Reliance", 10.0, "large_cap", "Conglomerate large cap"),
            ("LIQUIDBEES.NS", "Liquid Bees ETF", 5.0, "liquid", "Dry powder for dips"),
        ]
    else:  # balanced
        rows = [
            ("NIFTYBEES.NS", "Nifty Bees (Nifty 50 ETF)", 55.0, "index", "Primary SIP vehicle for beginners"),
            ("TCS.NS", "TCS", 12.0, "large_cap", "Quality IT compounder"),
            ("HDFCBANK.NS", "HDFC Bank", 12.0, "large_cap", "Banking leader"),
            ("RELIANCE.NS", "Reliance", 11.0, "large_cap", "Energy/retail conglomerate"),
            ("LIQUIDBEES.NS", "Liquid Bees ETF", 10.0, "liquid", "Emergency / stagger buffer"),
        ]
    if experience == "new" and risk_profile != "conservative":
        # Tilt new investors more to index
        return [
            ("NIFTYBEES.NS", "Nifty Bees (Nifty 50 ETF)", 70.0, "index", "Start here — learn before stock picking"),
            ("LIQUIDBEES.NS", "Liquid Bees ETF", 20.0, "liquid", "Keep 2 months SIP liquid while learning"),
            ("TCS.NS", "TCS (starter large cap)", 10.0, "large_cap", "One quality name to study in Single Stock tab"),
        ]
    return rows


def _us_allocation(risk_profile: str, experience: str) -> list[tuple[str, str, float, str, str]]:
    if risk_profile == "conservative":
        rows = [
            ("VOO", "Vanguard S&P 500 ETF", 80.0, "index", "Broad US market exposure"),
            ("VTI", "Vanguard Total Stock Market", 10.0, "index", "Broader US market"),
            ("AAPL", "Apple (large cap example)", 10.0, "large_cap", "Optional single-name sleeve"),
        ]
    elif risk_profile == "growth":
        rows = [
            ("VOO", "Vanguard S&P 500 ETF", 45.0, "index", "Core US equity"),
            ("QQQ", "Nasdaq 100 ETF", 25.0, "sector", "Tech-heavy — higher volatility"),
            ("MSFT", "Microsoft", 10.0, "large_cap", "Quality large cap"),
            ("NVDA", "NVIDIA", 10.0, "large_cap", "High-beta growth — size small"),
            ("AAPL", "Apple", 10.0, "large_cap", "Mega-cap anchor"),
        ]
    else:
        rows = [
            ("VOO", "Vanguard S&P 500 ETF", 60.0, "index", "Primary SIP for US investors"),
            ("MSFT", "Microsoft", 15.0, "large_cap", "Quality compounder"),
            ("AAPL", "Apple", 15.0, "large_cap", "Consumer tech anchor"),
            ("VTI", "Vanguard Total Stock Market", 10.0, "index", "Broader diversification"),
        ]
    if experience == "new":
        return [
            ("VOO", "Vanguard S&P 500 ETF", 85.0, "index", "Start with one broad ETF"),
            ("VTI", "Vanguard Total Stock Market", 15.0, "index", "Optional broader slice"),
        ]
    return rows


def allocation_template(
    risk_profile: str,
    experience: str,
    market: str,
) -> list[tuple[str, str, float, str, str]]:
    if market in ("india", "nse", "bse"):
        return _india_allocation(risk_profile, experience)
    return _us_allocation(risk_profile, experience)


def build_allocation_lines(
    monthly_sip: float,
    risk_profile: str,
    experience: str,
    market: str,
) -> list[SipAllocationLine]:
    template = allocation_template(risk_profile, experience, market)
    lines: list[SipAllocationLine] = []
    for ticker, name, weight, sleeve, note in template:
        amt = round(monthly_sip * weight / 100.0, 0)
        lines.append(SipAllocationLine(
            ticker=ticker,
            name=name,
            weight_pct=weight,
            monthly_amount=amt,
            sleeve=sleeve,
            note=note,
        ))
    # Fix rounding drift on last line
    drift = monthly_sip - sum(l.monthly_amount for l in lines)
    if lines and abs(drift) >= 1:
        lines[0].monthly_amount = round(lines[0].monthly_amount + drift, 0)
    return lines


def build_milestones(
    monthly_sip: float,
    annual_return_pct: float,
    years: float,
    *,
    lump_sum: float = 0.0,
    step_up_annual_pct: float = 0.0,
) -> list[SipMilestone]:
    months_total = _months(years)
    marks: list[SipMilestone] = []
    year_caps = sorted({y for y in range(1, int(years) + 1)} | {int(years)})
    for yr in year_caps:
        m = min(months_total, yr * 12)
        marks.append(SipMilestone(
            year=yr,
            months=m,
            invested=total_invested(monthly_sip, m, lump_sum=lump_sum, step_up_annual_pct=step_up_annual_pct),
            projected_corpus=future_value_sip(
                monthly_sip, annual_return_pct, m,
                lump_sum=lump_sum, step_up_annual_pct=step_up_annual_pct,
            ),
        ))
    return marks


def planner_tips(inp: SipPlannerInput, monthly_sip: float) -> list[str]:
    tips = [
        "SIP works best when automated on a fixed date — treat it like a bill.",
        "Do not stop SIP in corrections; volatility is normal over 5+ year horizons.",
        "Keep 6 months expenses in bank FD / liquid fund before aggressive equity SIP.",
    ]
    if inp.experience == "new":
        tips.append("Paper-track this plan for 3 months in Track Record before going live.")
        tips.append("Complete Varsity modules on risk and diversification before picking stocks.")
    if inp.risk_profile == "growth":
        tips.append("Growth sleeve has deeper drawdowns — only use money you won't need for 7+ years.")
    if inp.step_up_annual_pct > 0:
        tips.append(f"Step-up {inp.step_up_annual_pct:.0f}%/yr helps fight inflation — increase only when income rises.")
    if inp.goal_name == "Emergency + invest":
        tips.append("Build 6-month emergency fund first; route only surplus into equity SIP.")
    if monthly_sip > 0 and inp.monthly_budget and monthly_sip > inp.monthly_budget:
        tips.append("Required SIP exceeds budget — extend timeline or lower target.")
    return tips


def planner_guidance(inp: SipPlannerInput, plan: SipPlan) -> str:
    if inp.experience == "new" and plan.monthly_sip > 0:
        return (
            f"Start with **{plan.monthly_sip:,.0f}/month** into mostly **index ETFs** — "
            "add stock sleeves only after reading charts in Single Stock."
        )
    if plan.surplus_or_gap >= 0 and plan.monthly_budget:
        return (
            f"On track — projected **{plan.projected_corpus:,.0f}** vs target "
            f"**{plan.target_amount:,.0f}** at {inp.annual_return_pct:.0f}% assumed return."
        )
    if plan.projected_corpus >= plan.target_amount * 0.98:
        return (
            f"Plan reaches **{plan.projected_corpus:,.0f}** vs target "
            f"**{plan.target_amount:,.0f}** at {inp.annual_return_pct:.0f}% assumed return."
        )
    return (
        f"Gap of **{abs(plan.surplus_or_gap):,.0f}/month** — increase SIP, extend "
        f"{inp.years:.0f} years, or expect lower returns than {inp.annual_return_pct:.0f}%."
    )


def build_sip_plan(inp: SipPlannerInput) -> SipPlan:
    months = _months(inp.years)
    if inp.monthly_budget and inp.monthly_budget > 0:
        monthly_sip = inp.monthly_budget
        required = required_monthly_sip(
            inp.target_amount, inp.annual_return_pct, months,
            lump_sum=inp.current_corpus, step_up_annual_pct=inp.step_up_annual_pct,
        )
        surplus_or_gap = monthly_sip - required
    else:
        monthly_sip = required_monthly_sip(
            inp.target_amount, inp.annual_return_pct, months,
            lump_sum=inp.current_corpus, step_up_annual_pct=inp.step_up_annual_pct,
        )
        surplus_or_gap = 0.0

    projected = future_value_sip(
        monthly_sip, inp.annual_return_pct, months,
        lump_sum=inp.current_corpus, step_up_annual_pct=inp.step_up_annual_pct,
    )

    allocation = build_allocation_lines(
        monthly_sip, inp.risk_profile, inp.experience, inp.market,
    )
    milestones = build_milestones(
        monthly_sip, inp.annual_return_pct, inp.years,
        lump_sum=inp.current_corpus, step_up_annual_pct=inp.step_up_annual_pct,
    )

    plan = SipPlan(
        goal_name=inp.goal_name,
        target_amount=inp.target_amount,
        years=inp.years,
        months=months,
        current_corpus=inp.current_corpus,
        monthly_sip=monthly_sip,
        monthly_budget=inp.monthly_budget,
        annual_return_pct=inp.annual_return_pct,
        step_up_annual_pct=inp.step_up_annual_pct,
        risk_profile=inp.risk_profile,
        experience=inp.experience,
        projected_corpus=projected,
        surplus_or_gap=surplus_or_gap,
        allocation=allocation,
        milestones=milestones,
        tips=planner_tips(inp, monthly_sip),
    )
    plan.guidance = planner_guidance(inp, plan)
    return plan
