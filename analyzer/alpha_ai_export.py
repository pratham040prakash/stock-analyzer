"""Export Alpha AI reports as Markdown and PDF."""

from __future__ import annotations

import re
from io import BytesIO

from analyzer.alpha_ai_report import AlphaAIReport


def _strip_md(text: str) -> str:
    return re.sub(r"\*+", "", text).replace("_", "")


def report_to_markdown(report: AlphaAIReport) -> str:
    lines = [
        f"# Alpha AI Report — {report.name} ({report.symbol})",
        f"_Generated {report.generated_at}_",
        "",
        "## Executive Summary",
        f"- **Score:** {report.overall_score}/100",
        f"- **Recommendation:** {report.recommendation}",
        f"- **Buy decision:** {report.buy_decision}",
        f"- **Confidence:** {report.confidence_pct}%",
        f"- **Risk:** {report.risk_level}",
        f"- **Mode:** {getattr(report, 'report_mode', 'equity')}",
        "",
    ]
    if getattr(report, "section_sources", None):
        lines.append("## Data sources by section")
        for sec, srcs in report.section_sources.items():
            lines.append(f"- **{sec}:** {', '.join(srcs)}")
        lines.append("")

    lines.extend(["## Buy Decision", _strip_md(report.buy_decision_why), ""])
    lines.extend(["## Business", report.business_overview, ""])
    lines.extend(["## Financial Analysis", report.financial_analysis, ""])
    lines.extend(["## Valuation", f"**{report.valuation_verdict}**", report.valuation_detail, ""])
    lines.extend(["## Technical", report.technical_analysis, ""])
    lines.extend(["## News", report.news_sentiment, ""])
    if report.red_flags:
        lines.append("## Red Flags")
        for f in report.red_flags:
            lines.append(f"- {f}")
        lines.append("")
    lines.extend(["## Scenarios"])
    for s in report.scenarios:
        lines.append(f"- **{s.name}** ({s.probability_pct}%): target {s.target_price}, CAGR {s.expected_cagr}")
    lines.extend(["", "## Portfolio impact", report.portfolio_impact, ""])
    lines.extend(["## Final Verdict", report.final_verdict_detail, ""])
    if getattr(report, "llm_narrative", None):
        lines.extend(["## AI Narrative (optional LLM)", report.llm_narrative, ""])
    if report.data_gaps:
        lines.extend(["## Data gaps"])
        for g in report.data_gaps:
            lines.append(f"- {g}")
    lines.append("\n---\n_Not financial advice. Verify in annual reports._")
    return "\n".join(lines)


def report_to_pdf_bytes(report: AlphaAIReport) -> bytes:
    """Plain-text PDF via fpdf2."""
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise RuntimeError("Install fpdf2: pip install fpdf2") from exc

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    def writeln(text: str) -> None:
        for para in text.split("\n"):
            line = _strip_md(para.strip())[:110]
            if line:
                pdf.multi_cell(0, 6, line)

    writeln(f"Alpha AI — {report.name} ({report.symbol})")
    writeln(f"Score {report.overall_score}/100 · {report.recommendation} · Buy: {report.buy_decision}")
    writeln(report.final_verdict_detail[:2000])
    writeln(report.portfolio_impact)
    for s in report.scenarios:
        writeln(f"{s.name}: {s.target_price} ({s.probability_pct}%)")

    out = BytesIO()
    pdf.output(out)
    return out.getvalue()
