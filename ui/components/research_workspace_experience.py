"""Research Workspace Experience — render-only presentation (V3-201)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

import streamlit as st

from analyzer.intraday_prefs import IntradayPrefs
from analyzer.use_cases.morning_brief_models import PortfolioSection
from analyzer.zerodha import ZerodhaImportResult
from ui.broker.state import BrokerSnapshot
from ui.components.canvas_utils import _esc
from ui.components.portfolio_command_center import (
    PORTFOLIO_REVIEW,
    set_portfolio_subtab,
)
from ui.components.proof_state import open_proof_overlay
from ui.components.research_workspace_ui import (
    DISPOSITION_LABELS,
    ResearchQuestionContract,
    ResearchWorkspaceContract,
    research_question_understand_contract,
    research_workspace_from_inputs,
)
from ui.components.understand_popover import render_understand_popover
from ui.navigation import request_nav_tab

_REVIEWED_QUESTIONS_KEY = "research_reviewed_question_keys"
_ACTIVE_QUESTION_KEY = "research_active_question"
_DECISION_TEXT_KEY = "research_investment_decision_text"
_DISPOSITION_KEY = "research_disposition"
_BACK_TAB_KEY = "research_back_tab"
_BACK_SUBTAB_KEY = "research_back_subtab"


def _question_session_key(symbol: str, index: int) -> str:
    return f"{symbol.upper()}:{index}"


def _reviewed_keys(symbol: str) -> set[str]:
    raw = st.session_state.get(_REVIEWED_QUESTIONS_KEY, set())
    base = set(raw) if isinstance(raw, set) else set(raw or [])
    prefix = f"{symbol.upper()}:"
    return {item for item in base if item.startswith(prefix)}


def _mark_question_reviewed(symbol: str, index: int) -> None:
    reviewed = set(st.session_state.get(_REVIEWED_QUESTIONS_KEY, set()) or set())
    reviewed.add(_question_session_key(symbol, index))
    st.session_state[_REVIEWED_QUESTIONS_KEY] = reviewed


def _active_question(symbol: str, contract: ResearchWorkspaceContract) -> int:
    stored = st.session_state.get(_ACTIVE_QUESTION_KEY)
    if isinstance(stored, int) and 1 <= stored <= len(contract.questions):
        return stored
    reviewed = _reviewed_keys(symbol)
    for question in contract.questions:
        if _question_session_key(symbol, question.question_index) not in reviewed:
            return question.question_index
    return 1


def _set_active_question(index: int) -> None:
    st.session_state[_ACTIVE_QUESTION_KEY] = index


def render_research_context_header(*, contract: ResearchWorkspaceContract) -> None:
    ctx = contract.context
    chips: list[str] = [ctx.symbol]
    if ctx.held:
        chips.append(f"Held · {ctx.weight_label}")
    else:
        chips.append("Not in portfolio")
    if ctx.flag_label:
        chips.append(f"⚠ {ctx.flag_label}")
    elif ctx.health_label and ctx.health_label != "—":
        chips.append(ctx.health_label)

    back_tab = str(st.session_state.get(_BACK_TAB_KEY, "My Portfolio"))
    back_subtab = st.session_state.get(_BACK_SUBTAB_KEY)
    back_label = "← Back to Portfolio Review" if back_subtab == PORTFOLIO_REVIEW else f"← Back to {back_tab}"

    st.markdown(
        '<div class="apex-research-context-header">',
        unsafe_allow_html=True,
    )
    if st.button(back_label, key="research_back"):
        if back_tab == "My Portfolio" and back_subtab:
            set_portfolio_subtab(str(back_subtab))
            request_nav_tab("My Portfolio")
        else:
            request_nav_tab(back_tab)
    st.markdown(
        f'<p class="apex-research-context-chip" role="status">{" · ".join(_esc(c) for c in chips)}</p>',
        unsafe_allow_html=True,
    )
    if ctx.portfolio_fit_line:
        st.markdown(
            f'<p class="apex-research-fit">{_esc(ctx.portfolio_fit_line)}</p>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_investment_view_hero(*, contract: ResearchWorkspaceContract) -> None:
    hero = contract.hero
    home_link = ""
    if hero.show_home_link and hero.home_symbol:
        home_link = (
            f'<p class="apex-research-disclaimer">Today\'s trade verdict for '
            f"{_esc(hero.home_symbol)} is on Home — not duplicated here.</p>"
        )
    st.markdown(
        '<section class="apex-section apex-research-hero" aria-label="Investment view">'
        f'<p class="apex-research-view-label">{_esc(hero.view_label)}</p>'
        f'<p class="apex-research-summary">{_esc(hero.summary)}</p>'
        f'<p class="apex-research-disclaimer">{_esc(hero.disclaimer)}</p>'
        f"{home_link}"
        "</section>",
        unsafe_allow_html=True,
    )


def render_research_question_navigator(*, contract: ResearchWorkspaceContract, active: int) -> None:
    reviewed = _reviewed_keys(contract.symbol)
    st.markdown(
        '<nav class="apex-research-question-nav" aria-label="Research questions">',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(contract.questions))
    for col, question in zip(cols, contract.questions, strict=True):
        key = _question_session_key(contract.symbol, question.question_index)
        marker = "✓" if key in reviewed else ("●" if question.question_index == active else "○")
        with col:
            if st.button(
                f"{marker} Q{question.question_index}",
                key=f"research_qnav_{question.question_index}",
                use_container_width=True,
            ):
                _set_active_question(question.question_index)
                st.rerun()
    st.markdown(
        f'<p class="apex-research-progress" role="status">Question {active} of {len(contract.questions)} · '
        f"{_esc(contract.questions[active - 1].question_text)}</p>",
        unsafe_allow_html=True,
    )
    st.markdown("</nav>", unsafe_allow_html=True)


def render_understand_gateway(
    *,
    question: ResearchQuestionContract,
    contract: ResearchWorkspaceContract,
) -> None:
    with st.popover("Help me understand ▾"):
        render_understand_popover(
            research_question_understand_contract(
                question,
                understand=contract.understand,
            ),
            wrap_popover=False,
        )


def render_proof_overlay_link(*, contract: ResearchWorkspaceContract) -> None:
    if not contract.show_proof:
        return
    if st.button("View proof overlay", key="research_proof", use_container_width=True):
        open_proof_overlay(origin="research", proof_mode="decision", symbol=contract.symbol)


def render_research_question_panel(
    *,
    question: ResearchQuestionContract,
    contract: ResearchWorkspaceContract,
) -> None:
    st.markdown(
        '<section class="apex-section apex-research-question-panel" '
        f'aria-label="{_esc(question.question_text)}">'
        f'<h3 class="apex-research-question-title">Question {question.question_index} · '
        f"{_esc(question.question_text)}</h3>",
        unsafe_allow_html=True,
    )
    if question.labeled_lines:
        st.markdown('<p class="apex-research-labeled-heading">Supporting & conflicting</p>', unsafe_allow_html=True)
        for line in question.labeled_lines:
            st.markdown(
                f'<p class="apex-research-labeled-line">'
                f'<span class="apex-evidence-label">{_esc(line.label)}</span> · '
                f"{_esc(line.text)}</p>",
                unsafe_allow_html=True,
            )
    for line in question.body_lines:
        st.markdown(
            f'<p class="apex-research-body-line">{_esc(line)}</p>',
            unsafe_allow_html=True,
        )
    c1, c2 = st.columns(2)
    with c1:
        render_understand_gateway(question=question, contract=contract)
    with c2:
        if question.question_index == 2:
            render_proof_overlay_link(contract=contract)
    st.markdown("</section>", unsafe_allow_html=True)


def render_research_navigation_bar(
    *,
    contract: ResearchWorkspaceContract,
    active: int,
) -> None:
    st.markdown(
        '<div class="apex-research-nav-bar" role="group" aria-label="Research navigation">',
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if active > 1 and st.button("← Previous question", key="research_prev", use_container_width=True):
            _set_active_question(active - 1)
            st.rerun()
    with c2:
        if st.button("Mark reviewed ✓", key="research_mark_reviewed", use_container_width=True):
            _mark_question_reviewed(contract.symbol, active)
            st.rerun()
    with c3:
        if active < len(contract.questions) and st.button(
            "Next question →",
            key="research_next",
            use_container_width=True,
        ):
            _mark_question_reviewed(contract.symbol, active)
            _set_active_question(active + 1)
            st.rerun()
    with c4:
        if st.button("Investment Decision", key="research_open_decision", use_container_width=True):
            _set_active_question(7)
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_investment_decision_panel(*, contract: ResearchWorkspaceContract) -> None:
    decision = contract.decision
    symbol = contract.symbol
    text_key = f"{_DECISION_TEXT_KEY}_{symbol}"
    disposition_key = f"{_DISPOSITION_KEY}_{symbol}"
    if text_key not in st.session_state:
        st.session_state[text_key] = ""
    if disposition_key not in st.session_state:
        st.session_state[disposition_key] = decision.default_disposition

    st.markdown(
        '<section class="apex-section apex-research-decision" aria-label="Investment decision">'
        '<h3 class="apex-research-question-title">Question 7 · '
        "What investment decision have I reached?</h3>"
        '<p class="apex-research-decision-label">System summary (read-only)</p>',
        unsafe_allow_html=True,
    )
    for line in decision.system_summary_lines:
        st.markdown(f'<p class="apex-research-body-line">{_esc(line)}</p>', unsafe_allow_html=True)

    st.markdown('<p class="apex-research-decision-label">Your investment decision</p>', unsafe_allow_html=True)
    st.text_area(
        "Investment decision",
        key=text_key,
        label_visibility="collapsed",
        height=100,
    )
    options = list(DISPOSITION_LABELS.keys())
    labels = [DISPOSITION_LABELS[key] for key in options]
    current = st.session_state.get(disposition_key, decision.default_disposition)
    try:
        default_index = options.index(current)
    except ValueError:
        default_index = 0
    choice = st.radio(
        "Disposition",
        options=labels,
        index=default_index,
        horizontal=True,
        key=f"research_disposition_radio_{symbol}",
    )
    st.session_state[disposition_key] = options[labels.index(choice)]

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Save to Journal draft", key="research_save_journal", use_container_width=True):
            from ui.components.research_journal_experience import (
                create_journal_draft_from_research,
                navigate_to_journal_confirm,
            )

            if not str(st.session_state.get(text_key, "") or "").strip():
                st.warning("Write your investment decision before saving to Journal.")
            else:
                draft_id = create_journal_draft_from_research(contract=contract)
                navigate_to_journal_confirm(draft_id)
    with c2:
        with st.popover("Help me understand ▾"):
            render_understand_popover(contract.understand, wrap_popover=False)
    st.markdown("</section>", unsafe_allow_html=True)


def render_alpha_deep_report_link(*, contract: ResearchWorkspaceContract) -> None:
    st.markdown(
        '<section class="apex-section apex-research-alpha-link" aria-label="Deep report">',
        unsafe_allow_html=True,
    )
    if st.button(
        f"Open full report in {contract.alpha_reports_tab} →",
        key="research_alpha_link",
        use_container_width=True,
    ):
        request_nav_tab(contract.alpha_reports_tab)
    st.caption("Optional institutional depth (L5) — does not replace the guided question flow.")
    st.markdown("</section>", unsafe_allow_html=True)


def render_research_handoff_footer(*, contract: ResearchWorkspaceContract) -> None:
    st.markdown(
        f'<p class="apex-foot apex-research-footer">{_esc(contract.broker_footer)}</p>',
        unsafe_allow_html=True,
    )


def render_research_workbench_experience(*, contract: ResearchWorkspaceContract) -> None:
    active = _active_question(contract.symbol, contract)
    question = contract.questions[active - 1]

    st.markdown(
        '<main class="apex-brief-page apex-research-workbench" role="main" '
        'aria-labelledby="apex-research-title">'
        '<h2 id="apex-research-title" class="visually-hidden">Research Workbench</h2>',
        unsafe_allow_html=True,
    )
    render_research_context_header(contract=contract)
    render_investment_view_hero(contract=contract)
    render_research_question_navigator(contract=contract, active=active)
    if active == 7:
        render_investment_decision_panel(contract=contract)
    else:
        render_research_question_panel(question=question, contract=contract)
    render_research_navigation_bar(contract=contract, active=active)
    render_alpha_deep_report_link(contract=contract)
    render_research_handoff_footer(contract=contract)
    st.markdown("</main>", unsafe_allow_html=True)


def render_research_workbench_surface(
    *,
    symbol: str,
    cached: dict | None,
    broker: BrokerSnapshot,
    portfolio: ZerodhaImportResult | None,
    prefs: IntradayPrefs,
    portfolio_section: PortfolioSection | None = None,
    journal_today_pnl: float | None = None,
) -> None:
    contract = research_workspace_from_inputs(
        symbol=symbol,
        cached=cached,
        broker=broker,
        portfolio=portfolio,
        prefs=prefs,
        portfolio_section=portfolio_section,
        journal_today_pnl=journal_today_pnl,
    )
    render_research_workbench_experience(contract=contract)


def set_research_back_context(*, tab: str = "My Portfolio", subtab: str | None = None) -> None:
    st.session_state[_BACK_TAB_KEY] = tab
    if subtab:
        st.session_state[_BACK_SUBTAB_KEY] = subtab
