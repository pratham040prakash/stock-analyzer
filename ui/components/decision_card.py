"""Decision Card — hero projection of MorningBriefViewModel (ETS-003b v0.2 / ETS-003c L0)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

import html
from dataclasses import dataclass

from analyzer.use_cases.morning_brief_models import MorningBriefViewModel


@dataclass(frozen=True)
class BestOpportunityView:
    symbol: str
    setup: str
    visible: bool


@dataclass(frozen=True)
class DecisionCardViewModel:
    """Hero slice — derived only from MorningBriefViewModel."""

    verdict_word: str
    verdict_key: str
    reason: str
    confidence_level: int
    confidence_band: str
    last_updated: str
    valid_until: str
    portfolio_ready: bool
    portfolio_status: str
    sync_label: str
    sync_state: str
    best_opportunity: BestOpportunityView | None
    risk_level: str
    coach_message: str
    cta_label: str
    cta_action: str
    scenario: str
    stale: bool
    stale_label: str
    trust_summary: str
    evidence_teaser: tuple[str, ...]
    broker_connected: bool
    cash_available_inr: float | None
    last_sync: str
    decision_verdict: str | None
    failure_message: str | None


def _coach_message(brief: MorningBriefViewModel) -> str:
    key = brief.decision.verdict_key
    if brief.meta.scenario == "weekend":
        return "Patience is part of your edge."
    if brief.meta.scenario == "market_closed":
        return "Protecting capital is also a winning decision."
    if key == "wait":
        return "The best trade today may be the one you don't make."
    if key == "trade":
        return "Size matters more than speed — review the plan before Kite."
    if key == "pause":
        return "Discipline compounds. So does inconsistency."
    return ""


def _sync_label(state: str) -> str:
    return {
        "synced": "Synced",
        "stale": "Stale",
        "offline": "Offline",
        "not_configured": "Offline",
    }.get(state, "Offline")


def _hero_evidence_teaser(brief: MorningBriefViewModel, reason_lc: str) -> tuple[str, ...]:
    for item in brief.evidence.key_reasons:
        text = str(item or "").strip()
        if text and text.lower() not in reason_lc:
            return (text,)
    for line in brief.evidence.supporting_signals:
        text = f"{line.type}: {line.value}".strip()
        if text and text.lower() not in reason_lc:
            return (text,)
    return ()


def project_decision_card(brief: MorningBriefViewModel) -> DecisionCardViewModel:
    """Project root view model → hero card. No business logic."""
    d = brief.decision
    t = brief.trust
    p = brief.portfolio
    o = brief.opportunity
    sync_state = t.data_freshness.broker_sync_state
    if sync_state == "synced":
        sync_css = "ok"
    elif sync_state == "stale":
        sync_css = "warn"
    else:
        sync_css = "off"

    best: BestOpportunityView | None = None
    if o.visible:
        best = BestOpportunityView(symbol=o.symbol, setup=o.setup, visible=True)

    reason_lc = d.reason.strip().lower()
    evidence_teaser = _hero_evidence_teaser(brief, reason_lc)

    return DecisionCardViewModel(
        verdict_word=d.verdict_display,
        verdict_key=d.verdict_key,
        reason=d.reason,
        confidence_level=d.confidence_level,
        confidence_band=d.confidence_band,
        last_updated=d.last_updated,
        valid_until=d.valid_until,
        portfolio_ready=p.ready,
        portfolio_status=p.summary,
        sync_label=_sync_label(sync_state),
        sync_state=sync_css,
        best_opportunity=best,
        risk_level=brief.risk.level,
        coach_message=_coach_message(brief),
        cta_label=d.cta_label,
        cta_action=d.cta_action,
        scenario=brief.meta.scenario,
        stale=t.stale,
        stale_label=t.stale_label,
        trust_summary=t.why_this_is_recommended,
        evidence_teaser=evidence_teaser,
        broker_connected=t.portfolio_sync_status.personalized,
        cash_available_inr=p.cash_available_inr,
        last_sync=t.data_freshness.broker_last_sync,
        decision_verdict=d.verdict,
        failure_message=brief.failure_message,
    )


def canvas_state_from_view_model(vm: DecisionCardViewModel) -> tuple[str, str, str, str]:
    return vm.verdict_key, vm.verdict_word, vm.cta_label, vm.cta_action


def _esc(text: str) -> str:
    return html.escape(str(text or ""))


def _sync_css(sync_state: str) -> tuple[str, str]:
    if sync_state == "ok":
        return "vc-sync-ok", "vc-sync-ok"
    if sync_state == "warn":
        return "vc-sync-warn", "vc-sync-warn"
    return "vc-sync-off", "vc-sync-off"


_HERO_INTEL_BLOCKED = frozenset({"connect", "rest", "pause"})


def hero_intel_sections(card: DecisionCardViewModel) -> tuple[str, ...]:
    """Hero intel only when brief verdict allows trade context (no contradictions)."""
    if card.failure_message:
        return ()
    if card.verdict_key in _HERO_INTEL_BLOCKED or card.verdict_key != "trade":
        return ()
    if not card.best_opportunity or not card.best_opportunity.visible:
        return ()
    return ("opportunity", "do_next", "risk")


def below_fold_intel_sections(card: DecisionCardViewModel) -> tuple[str, ...]:
    """Below-fold blocks — market-only when hero blocks trade intel."""
    if card.failure_message or card.verdict_key in ("connect", "rest"):
        return ("market",)
    if card.verdict_key in ("pause", "wait"):
        sections: list[str] = ["market"]
        if card.broker_connected:
            sections.append("portfolio")
        return tuple(sections)
    return ("market", "portfolio", "next_watch")


def today_intel_actions_allowed(card: DecisionCardViewModel) -> bool:
    return (
        not card.failure_message
        and card.verdict_key == "trade"
        and bool(card.best_opportunity and card.best_opportunity.visible)
    )


def hero_review_setup_symbol(card: DecisionCardViewModel) -> str | None:
    """Canonical Today hero symbol for navigation — must match displayed opportunity (APEX-012 Phase 2a)."""
    opp = card.best_opportunity
    if not opp or not opp.visible:
        return None
    sym = opp.symbol.strip()
    return sym or None


def resolve_hero_review_nav_symbol(*, review_symbol: str | None, legacy_best_ticker: str) -> str:
    """Navigation determinism: canonical review_symbol wins; legacy ranking never overrides when set."""
    if review_symbol is not None:
        return review_symbol.strip()
    return (legacy_best_ticker or "").strip()


def _intel_section_html(*, label: str, lines: tuple[str, ...], tone: str = "") -> str:
    filtered = [line for line in lines if line.strip()]
    if not filtered:
        return ""
    tone_cls = f" vc-intel-{tone}" if tone else ""
    body = "".join(f'<p class="vc-intel-line{tone_cls}">{_esc(line)}</p>' for line in filtered)
    return (
        f'<section class="vc-intel-block">'
        f'<p class="vc-intel-label">{_esc(label)}</p>'
        f"{body}"
        f"</section>"
    )


def project_opportunity_intel_html(card: DecisionCardViewModel) -> str:
    """Tier A — hero Opportunity block from MorningBriefViewModel only (APEX-012 Phase 1)."""
    if not card.best_opportunity or not card.best_opportunity.visible:
        return ""
    opp = card.best_opportunity
    name = f"{opp.symbol} — MIS setup"
    lines: list[str] = [name]
    if opp.setup:
        lines.append(opp.setup)
    tone = "high" if card.verdict_key == "trade" else ""
    return _intel_section_html(label="Opportunity", lines=tuple(lines), tone=tone)


def compose_hero_intel_html(
    *,
    card: DecisionCardViewModel,
    legacy_intel_html: str,
    sections: tuple[str, ...],
) -> str:
    """Merge MBVM opportunity projection with legacy intel blocks (do_next, risk)."""
    if not sections:
        return ""
    blocks: list[str] = []
    if "opportunity" in sections:
        opp_block = project_opportunity_intel_html(card)
        if opp_block:
            blocks.append(opp_block)
    legacy_sections = tuple(s for s in sections if s != "opportunity")
    if legacy_sections and legacy_intel_html:
        prefix = '<div class="vc-intel-stack vc-intel-stack-hero">'
        suffix = "</div>"
        if legacy_intel_html.startswith(prefix) and legacy_intel_html.endswith(suffix):
            inner = legacy_intel_html[len(prefix) : -len(suffix)]
            if inner:
                blocks.append(inner)
        else:
            blocks.append(legacy_intel_html)
    if not blocks:
        return ""
    return f'<div class="vc-intel-stack vc-intel-stack-hero">{"".join(blocks)}</div>'


def hero_stale_html(card: DecisionCardViewModel) -> str:
    if card.stale and card.stale_label:
        return f'<p class="vc-stale">{_esc(card.stale_label)}</p>'
    return ""


def hero_failure_html(card: DecisionCardViewModel) -> str:
    if not card.failure_message:
        return ""
    return f'<p class="vc-failure">{_esc(card.failure_message)}</p>'


def hero_l0_trust_html(card: DecisionCardViewModel) -> str:
    """ETS-003c — trust + evidence below mentor (projection only)."""
    parts: list[str] = []

    if card.evidence_teaser:
        teaser = _esc(card.evidence_teaser[0])
        reason_lc = card.reason.strip().lower()
        if teaser.lower() not in reason_lc and teaser:
            parts.append(
                f'<p class="vc-evidence-teaser">'
                f'<span class="vc-l0-label">Why</span> {teaser}</p>'
            )

    if card.trust_summary:
        trust = _esc(card.trust_summary)
        if trust.lower() not in card.reason.strip().lower():
            parts.append(
                f'<p class="vc-trust-line">'
                f'<span class="vc-l0-label">Trust</span> {trust}</p>'
            )

    if card.confidence_band and card.confidence_band != "unknown":
        parts.append(
            f'<p class="vc-confidence-band" data-band="{_esc(card.confidence_band)}">'
            f'{_esc(card.confidence_band.title())} confidence</p>'
        )

    if card.portfolio_status and card.broker_connected:
        parts.append(f'<p class="vc-portfolio-line">{_esc(card.portfolio_status)}</p>')

    return "".join(parts)


def hero_header_sync_html(card: DecisionCardViewModel) -> tuple[str, str, str]:
    """Sync row from brief trust projection (not broker re-derivation)."""
    sync_cls, dot_cls = _sync_css(card.sync_state)
    return sync_cls, dot_cls, card.sync_label


def hero_session_ribbon_html(session_ribbon: tuple[str, ...]) -> str:
    """L0.5 ambient session ribbon — projection only (ETS-003a §5.1)."""
    items = [str(item).strip() for item in session_ribbon if str(item).strip()]
    if not items:
        return ""
    chips = "".join(f'<span class="vc-ribbon-chip">{_esc(item)}</span>' for item in items[:4])
    return f'<div class="vc-session-ribbon" role="status">{chips}</div>'


def hero_refreshing_html() -> str:
    return '<p class="vc-refreshing" role="status">Updating today\'s brief…</p>'


# Legacy alias
build_decision_card_view = project_decision_card
