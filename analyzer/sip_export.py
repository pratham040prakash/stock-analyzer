"""Export SIP plans as Markdown / CSV for sharing or print-to-PDF."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.sip_planner import SipPlan

IST = ZoneInfo("Asia/Kolkata")


def plan_to_markdown(plan: SipPlan, *, currency: str = "₹") -> str:
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    lines = [
        f"# SIP Plan — {plan.goal_name}",
        f"_Generated {now}_",
        "",
        "## Summary",
        f"- **Monthly SIP:** {currency}{plan.monthly_sip:,.0f}",
        f"- **Target:** {currency}{plan.target_amount:,.0f} in {plan.years:.0f} years",
        f"- **Projected corpus:** {currency}{plan.projected_corpus:,.0f} "
        f"(@ {plan.annual_return_pct:.1f}% assumed)",
        f"- **Already saved:** {currency}{plan.current_corpus:,.0f}",
        f"- **Risk profile:** {plan.risk_profile.title()}",
    ]
    if plan.step_up_annual_pct:
        lines.append(f"- **Annual step-up:** {plan.step_up_annual_pct:.0f}%")
    lines.extend(["", plan.guidance, "", "## Monthly allocation", ""])
    lines.append("| Instrument | Ticker | Weight | Monthly | Note |")
    lines.append("|------------|--------|--------|---------|------|")
    for line in plan.allocation:
        ticker = line.ticker.replace(".NS", "")
        lines.append(
            f"| {line.name} | {ticker} | {line.weight_pct:.0f}% | "
            f"{currency}{line.monthly_amount:,.0f} | {line.note} |"
        )
    if plan.milestones:
        lines.extend(["", "## Milestones", ""])
        lines.append("| Year | Invested | Projected corpus |")
        lines.append("|------|----------|------------------|")
        for m in plan.milestones:
            lines.append(
                f"| {m.year} | {currency}{m.invested:,.0f} | "
                f"{currency}{m.projected_corpus:,.0f} |"
            )
    if plan.tips:
        lines.extend(["", "## Discipline tips", ""])
        for tip in plan.tips:
            lines.append(f"- {tip}")
    lines.extend([
        "",
        "_Not financial advice. Assumed returns are illustrative._",
    ])
    return "\n".join(lines)


def plan_to_csv(plan: SipPlan, *, currency: str = "₹") -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["SIP Plan", plan.goal_name])
    writer.writerow(["Monthly SIP", f"{currency}{plan.monthly_sip:,.0f}"])
    writer.writerow(["Target", f"{currency}{plan.target_amount:,.0f}"])
    writer.writerow(["Projected", f"{currency}{plan.projected_corpus:,.0f}"])
    writer.writerow([])
    writer.writerow(["Instrument", "Ticker", "Weight %", "Monthly", "Sleeve", "Note"])
    for line in plan.allocation:
        writer.writerow([
            line.name,
            line.ticker.replace(".NS", ""),
            f"{line.weight_pct:.0f}",
            f"{currency}{line.monthly_amount:,.0f}",
            line.sleeve,
            line.note,
        ])
    writer.writerow([])
    writer.writerow(["Year", "Invested", "Projected corpus"])
    for m in plan.milestones:
        writer.writerow([
            m.year,
            f"{currency}{m.invested:,.0f}",
            f"{currency}{m.projected_corpus:,.0f}",
        ])
    return buf.getvalue()
