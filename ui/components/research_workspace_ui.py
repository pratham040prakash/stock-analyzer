"""Research Workspace — presentation contracts and question projection (V3-201)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from analyzer.decision_engine.models import DecisionArtifact
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.use_cases.morning_brief_models import MorningBriefViewModel, PortfolioSection
from analyzer.use_cases.portfolio_overview_assembly import assemble_portfolio_overview
from analyzer.zerodha import ZerodhaImportResult
from ui.broker.state import BrokerSnapshot
from ui.components.canvas_utils import _strip_md
from ui.components.morning_brief_ui import (
    BusinessHealthContract,
    InvestmentThesisContract,
    RecommendationContract,
    RiskMonitorContract,
    business_health_contract_from_brief,
    investment_thesis_contract_from_brief,
    load_brief_from_cache,
    recommendation_contract_from_brief,
    risk_monitor_contract_from_brief,
)
from ui.components.understand_popover import UnderstandContract, UnderstandSection

RESEARCH_QUESTIONS: tuple[str, ...] = (
    "What does this business do?",
    "What evidence supports investing?",
    "What could invalidate the thesis?",
    "How strong is my conviction?",
    "Is valuation attractive?",
    "What are the major risks?",
    "What investment decision have I reached?",
)

DISPOSITION_WATCH = "watch"
DISPOSITION_HOLD = "hold"
DISPOSITION_ACCUMULATE = "accumulate_later"
DISPOSITION_AVOID = "avoid"

DISPOSITION_LABELS: dict[str, str] = {
    DISPOSITION_WATCH: "Watch",
    DISPOSITION_HOLD: "Hold",
    DISPOSITION_ACCUMULATE: "Accumulate Later",
    DISPOSITION_AVOID: "Avoid",
}


@dataclass(frozen=True)
class LabeledLineContract:
    label: str
    text: str


@dataclass(frozen=True)
class ResearchQuestionContract:
    question_index: int
    question_text: str
    body_lines: tuple[str, ...]
    labeled_lines: tuple[LabeledLineContract, ...]


@dataclass(frozen=True)
class PortfolioResearchContextContract:
    symbol: str
    held: bool
    weight_label: str
    health_label: str
    flag_label: str
    portfolio_fit_line: str


@dataclass(frozen=True)
class InvestmentViewHeroContract:
    view_label: str
    summary: str
    disclaimer: str
    show_home_link: bool
    home_symbol: str


@dataclass(frozen=True)
class ValuationSliceContract:
    label: str
    narrative: str
    detail_lines: tuple[str, ...]


@dataclass(frozen=True)
class InvestmentDecisionContract:
    system_summary_lines: tuple[str, ...]
    default_disposition: str


@dataclass(frozen=True)
class ResearchWorkspaceContract:
    symbol: str
    context: PortfolioResearchContextContract
    hero: InvestmentViewHeroContract
    questions: tuple[ResearchQuestionContract, ...]
    valuation: ValuationSliceContract
    decision: InvestmentDecisionContract
    understand: UnderstandContract
    show_proof: bool
    evidence_packet_id: str
    broker_footer: str
    alpha_reports_tab: str


def _normalize_symbol(symbol: str) -> str:
    return symbol.upper().replace(".NS", "").replace(".BO", "").replace("NSE:", "").strip()


def _dedupe_lines(lines: list[str], *, limit: int = 6) -> tuple[str, ...]:
    out: list[str] = []
    for raw in lines:
        text = _strip_md(raw)
        if text and text not in out:
            out.append(text)
        if len(out) >= limit:
            break
    return tuple(out)


def _portfolio_context(
    *,
    symbol: str,
    broker: BrokerSnapshot,
    portfolio: ZerodhaImportResult | None,
    prefs: IntradayPrefs,
    portfolio_section: PortfolioSection | None,
    journal_today_pnl: float | None,
) -> PortfolioResearchContextContract:
    clean = _normalize_symbol(symbol)
    vm = assemble_portfolio_overview(
        broker=broker,
        portfolio=portfolio,
        prefs=prefs,
        portfolio_section=portfolio_section,
        journal_today_pnl=journal_today_pnl,
    )
    row = next((item for item in vm.holdings_rows if item.symbol.upper() == clean), None)
    held = row is not None
    weight = f"{row.weight_pct:.1f}%" if row else "—"
    health = row.health_label if row and row.health_label else "—"
    flag = ""
    for item in vm.attention_items:
        if item.symbol.upper() == clean:
            flag = item.flag_type
            break
    fit = ""
    if row:
        fit = f"Portfolio fit: {weight} weight"
        if row.health_label and row.health_label.lower() not in ("healthy", "—"):
            fit += f" · {row.health_label}"
    return PortfolioResearchContextContract(
        symbol=clean,
        held=held,
        weight_label=weight,
        health_label=health,
        flag_label=flag,
        portfolio_fit_line=fit,
    )


def _investment_view_hero(
    *,
    symbol: str,
    brief: MorningBriefViewModel,
    recommendation: RecommendationContract,
    portfolio_ctx: PortfolioResearchContextContract,
) -> InvestmentViewHeroContract:
    clean = _normalize_symbol(symbol)
    opp_symbol = _normalize_symbol(brief.opportunity.symbol) if brief.opportunity.visible else ""
    same_as_home = bool(opp_symbol and opp_symbol == clean)

    if brief.failure_message or not recommendation.why:
        view = "Insufficient data"
        summary = (
            brief.failure_message
            or brief.evidence.gap_note
            or "Not enough verified data to form a research view for this symbol yet."
        )
    elif portfolio_ctx.flag_label:
        view = "Cautious"
        summary = (
            f"{clean} needs investigation — {portfolio_ctx.flag_label} flagged in your portfolio. "
            f"{recommendation.why[0] if recommendation.why else brief.decision.reason}"
        )
    elif recommendation.risks and len(recommendation.risks) >= 2:
        view = "Cautious"
        summary = (
            f"{clean} shows mixed signals. "
            f"{recommendation.why[0] if recommendation.why else brief.trust.why_this_is_recommended}"
        )
    else:
        view = "Promising"
        summary = (
            recommendation.why[0]
            if recommendation.why
            else brief.trust.why_this_is_recommended
            or "Worth completing the research questions before deciding."
        )

    disclaimer = (
        "This is research guidance — not today's trade verdict."
        if same_as_home
        else "Complete all research questions before acting. Home owns today's trade verdict when applicable."
    )
    return InvestmentViewHeroContract(
        view_label=view,
        summary=_strip_md(summary),
        disclaimer=disclaimer,
        show_home_link=same_as_home,
        home_symbol=clean if same_as_home else "",
    )


def _labeled_evidence(brief: MorningBriefViewModel) -> tuple[LabeledLineContract, ...]:
    lines: list[LabeledLineContract] = []
    for item in brief.evidence.supporting_signals:
        label = (item.type or "FACT").upper()
        if label not in ("FACT", "ASSUMPTION", "ESTIMATE", "OPINION"):
            label = "FACT"
        lines.append(LabeledLineContract(label=label, text=f"{item.label}: {item.value}"))
    for item in brief.evidence.conflicting_signals:
        lines.append(
            LabeledLineContract(
                label="ESTIMATE",
                text=f"Conflict — {item.label}: {item.value}",
            )
        )
    for line in brief.evidence.key_reasons[:3]:
        text = _strip_md(line)
        if text:
            lines.append(LabeledLineContract(label="FACT", text=text))
    return tuple(lines[:8])


def _valuation_slice(
    *,
    symbol: str,
    recommendation: RecommendationContract,
    brief: MorningBriefViewModel,
) -> ValuationSliceContract:
    details: list[str] = []
    for line in list(recommendation.trade_offs) + list(recommendation.risks):
        lower = line.lower()
        if any(token in lower for token in ("valuation", "multiple", "p/e", "pe ", "price", "expensive", "cheap")):
            details.append(line)
    for line in recommendation.help_business:
        lower = line.lower()
        if any(token in lower for token in ("valuation", "price", "multiple")):
            details.append(line)
    details = list(_dedupe_lines(details, limit=4))
    if details:
        label = "Review valuation carefully"
        if any("expensive" in d.lower() or "above" in d.lower() for d in details):
            label = "Valuation appears full"
        elif any("fair" in d.lower() or "attractive" in d.lower() for d in details):
            label = "Valuation appears reasonable"
        narrative = details[0]
    else:
        label = "Valuation data limited"
        narrative = (
            f"Use Question 2 evidence and the Alpha AI report for {symbol} valuation depth. "
            f"{brief.evidence.gap_note or ''} "
            "No standalone price target is implied."
        ).strip()
    return ValuationSliceContract(
        label=label,
        narrative=_strip_md(narrative),
        detail_lines=tuple(details[1:4]),
    )


def _build_questions(
    *,
    brief: MorningBriefViewModel,
    recommendation: RecommendationContract,
    thesis: InvestmentThesisContract,
    health: BusinessHealthContract,
    risk: RiskMonitorContract,
    valuation: ValuationSliceContract,
) -> tuple[ResearchQuestionContract, ...]:
    confidence = brief.decision.confidence_band or str(brief.decision.confidence_level)
    questions: list[ResearchQuestionContract] = []

    q1_lines = _dedupe_lines(
        [health.summary] + list(health.strengths[:2]) + list(health.weaknesses[:2]),
        limit=5,
    )
    questions.append(
        ResearchQuestionContract(
            question_index=1,
            question_text=RESEARCH_QUESTIONS[0],
            body_lines=q1_lines,
            labeled_lines=(),
        )
    )

    labeled = _labeled_evidence(brief)
    q2_lines = _dedupe_lines(list(recommendation.evidence) + list(recommendation.why[:2]), limit=6)
    questions.append(
        ResearchQuestionContract(
            question_index=2,
            question_text=RESEARCH_QUESTIONS[1],
            body_lines=q2_lines,
            labeled_lines=labeled,
        )
    )

    invalidation = _dedupe_lines(
        list(thesis.sell_conditions) + list(recommendation.what_could_change) + list(thesis.watch_closely[:2]),
        limit=6,
    )
    questions.append(
        ResearchQuestionContract(
            question_index=3,
            question_text=RESEARCH_QUESTIONS[2],
            body_lines=invalidation or ("No explicit invalidation conditions were recorded.",),
            labeled_lines=(),
        )
    )

    conviction = _dedupe_lines(
        [f"Confidence band: {confidence}"]
        + list(recommendation.why[:4])
        + [brief.trust.recommendation_confidence],
        limit=6,
    )
    questions.append(
        ResearchQuestionContract(
            question_index=4,
            question_text=RESEARCH_QUESTIONS[3],
            body_lines=conviction,
            labeled_lines=(),
        )
    )

    val_lines = _dedupe_lines([valuation.narrative] + list(valuation.detail_lines), limit=5)
    questions.append(
        ResearchQuestionContract(
            question_index=5,
            question_text=RESEARCH_QUESTIONS[4],
            body_lines=val_lines or (valuation.label,),
            labeled_lines=(),
        )
    )

    risk_lines = _dedupe_lines(
        [risk.summary] + list(risk.key_business_risks) + list(recommendation.risks),
        limit=6,
    )
    questions.append(
        ResearchQuestionContract(
            question_index=6,
            question_text=RESEARCH_QUESTIONS[5],
            body_lines=risk_lines or ("Review risks in Understand depth.",),
            labeled_lines=(),
        )
    )

    summary_lines = (
        f"Business: {health.summary or '—'}",
        f"Conviction: {confidence}",
        f"Valuation: {valuation.label}",
        f"Risks: {risk.summary or (risk.key_business_risks[0] if risk.key_business_risks else '—')}",
    )
    questions.append(
        ResearchQuestionContract(
            question_index=7,
            question_text=RESEARCH_QUESTIONS[6],
            body_lines=summary_lines,
            labeled_lines=(),
        )
    )
    return tuple(questions)


def _decision_contract(
    *,
    health: BusinessHealthContract,
    risk: RiskMonitorContract,
    valuation: ValuationSliceContract,
    recommendation: RecommendationContract,
) -> InvestmentDecisionContract:
    default = DISPOSITION_WATCH
    if recommendation.risks and len(recommendation.risks) >= 3:
        default = DISPOSITION_AVOID
    elif valuation.label.lower().startswith("valuation appears full"):
        default = DISPOSITION_HOLD
    return InvestmentDecisionContract(
        system_summary_lines=(
            f"Business quality: {health.summary or 'Review Q1'}",
            f"Risks: {risk.summary or 'Review Q6'}",
            f"Valuation: {valuation.label}",
        ),
        default_disposition=default,
    )


def research_question_understand_contract(
    question: ResearchQuestionContract,
    *,
    understand: UnderstandContract,
) -> UnderstandContract:
    if question.question_index == 1:
        sections = tuple(s for s in understand.sections if s.title in ("Why", "Evidence"))
    elif question.question_index == 2:
        sections = tuple(s for s in understand.sections if s.title in ("Evidence", "Trade-offs"))
    elif question.question_index == 3:
        sections = tuple(s for s in understand.sections if s.title == "What could change")
    elif question.question_index == 4:
        sections = tuple(s for s in understand.sections if s.title == "Why")
    elif question.question_index == 5:
        sections = tuple(s for s in understand.sections if s.title in ("Trade-offs", "Evidence"))
    elif question.question_index == 6:
        sections = tuple(s for s in understand.sections if s.title == "Risks")
    else:
        sections = understand.sections
    if not sections and question.body_lines:
        sections = (UnderstandSection(title=question.question_text, lines=question.body_lines),)
    return UnderstandContract(
        sections=sections,
        confidence_pct=understand.confidence_pct,
        depth_levels=understand.depth_levels,
    )


def research_workspace_from_view_model(
    *,
    symbol: str,
    brief: MorningBriefViewModel,
    recommendation: RecommendationContract,
    thesis: InvestmentThesisContract,
    health: BusinessHealthContract,
    risk: RiskMonitorContract,
    portfolio_ctx: PortfolioResearchContextContract,
    show_proof: bool = False,
    evidence_packet_id: str = "",
) -> ResearchWorkspaceContract:
    valuation = _valuation_slice(symbol=symbol, recommendation=recommendation, brief=brief)
    questions = _build_questions(
        brief=brief,
        recommendation=recommendation,
        thesis=thesis,
        health=health,
        risk=risk,
        valuation=valuation,
    )
    from ui.components.understand_popover import understand_contract_from_recommendation

    understand = understand_contract_from_recommendation(
        recommendation,
        confidence_pct=brief.decision.confidence_level,
    )
    hero = _investment_view_hero(
        symbol=symbol,
        brief=brief,
        recommendation=recommendation,
        portfolio_ctx=portfolio_ctx,
    )
    return ResearchWorkspaceContract(
        symbol=_normalize_symbol(symbol),
        context=portfolio_ctx,
        hero=hero,
        questions=questions,
        valuation=valuation,
        decision=_decision_contract(
            health=health,
            risk=risk,
            valuation=valuation,
            recommendation=recommendation,
        ),
        understand=understand,
        show_proof=show_proof,
        evidence_packet_id=evidence_packet_id,
        broker_footer="Market and filing data labeled in evidence. Broker Console is source of truth for holdings.",
        alpha_reports_tab="Alpha AI",
    )


def _decision_from_cache(cached: dict[str, Any]) -> DecisionArtifact | None:
    decision = cached.get("decision")
    if isinstance(decision, DecisionArtifact):
        return decision
    os_report = cached.get("os_report")
    if os_report is not None:
        artifact = getattr(os_report, "decision_artifact", None)
        if isinstance(artifact, DecisionArtifact):
            return artifact
    return None


def _fallback_workspace_contract(
    *,
    symbol: str,
    portfolio_ctx: PortfolioResearchContextContract,
) -> ResearchWorkspaceContract:
    gap = (
        f"Open Home to load decision context, then return to research {symbol}."
        if not portfolio_ctx.held
        else f"Researching {symbol} from your portfolio — decision context not loaded yet."
    )
    empty_questions = tuple(
        ResearchQuestionContract(
            question_index=index,
            question_text=text,
            body_lines=(gap,),
            labeled_lines=(),
        )
        for index, text in enumerate(RESEARCH_QUESTIONS, start=1)
    )
    understand = UnderstandContract(sections=(UnderstandSection(title="Status", lines=(gap,)),))
    return ResearchWorkspaceContract(
        symbol=symbol,
        context=portfolio_ctx,
        hero=InvestmentViewHeroContract(
            view_label="Insufficient data",
            summary=gap,
            disclaimer="Complete Home sync for full research depth.",
            show_home_link=False,
            home_symbol="",
        ),
        questions=empty_questions,
        valuation=ValuationSliceContract(
            label="Valuation data limited",
            narrative=gap,
            detail_lines=(),
        ),
        decision=InvestmentDecisionContract(
            system_summary_lines=("Decision context unavailable.",),
            default_disposition=DISPOSITION_WATCH,
        ),
        understand=understand,
        show_proof=False,
        evidence_packet_id="",
        broker_footer="Market and filing data labeled in evidence. Broker Console is source of truth for holdings.",
        alpha_reports_tab="Alpha AI",
    )


def research_workspace_from_inputs(
    *,
    symbol: str,
    cached: dict[str, Any] | None,
    broker: BrokerSnapshot,
    portfolio: ZerodhaImportResult | None,
    prefs: IntradayPrefs,
    portfolio_section: PortfolioSection | None = None,
    journal_today_pnl: float | None = None,
) -> ResearchWorkspaceContract:
    clean = _normalize_symbol(symbol)
    portfolio_ctx = _portfolio_context(
        symbol=clean,
        broker=broker,
        portfolio=portfolio,
        prefs=prefs,
        portfolio_section=portfolio_section,
        journal_today_pnl=journal_today_pnl,
    )
    if not cached:
        return _fallback_workspace_contract(symbol=clean, portfolio_ctx=portfolio_ctx)

    brief = load_brief_from_cache(cached, broker=broker)
    decision = _decision_from_cache(cached)
    mis = cached.get("mis")
    snapshot = cached.get("snapshot")
    pins = cached.get("pins")
    from analyzer.use_cases.snapshot_cache import snapshot_from_cache

    snap_obj = snapshot_from_cache(snapshot) if snapshot else None
    recommendation = recommendation_contract_from_brief(
        brief,
        decision=decision,
        mis=mis,
        snapshot=snap_obj,
        pins=pins if isinstance(pins, list) else None,
    )
    thesis = investment_thesis_contract_from_brief(brief, recommendation, mis=mis)
    health = business_health_contract_from_brief(brief, recommendation, thesis)
    risk = risk_monitor_contract_from_brief(brief, thesis, health)
    packet_id = decision.evidence_packet_id if decision else ""
    return research_workspace_from_view_model(
        symbol=clean,
        brief=brief,
        recommendation=recommendation,
        thesis=thesis,
        health=health,
        risk=risk,
        portfolio_ctx=portfolio_ctx,
        show_proof=bool(packet_id),
        evidence_packet_id=packet_id or "",
    )
