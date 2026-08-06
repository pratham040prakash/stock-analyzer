"""Portfolio Review Experience — render-only presentation (V3-103)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

import streamlit as st

from ui.components.broker_connect import render_broker_sign_in_button
from ui.components.canvas_utils import _esc
from ui.components.portfolio_command_center import (
    PORTFOLIO_HOLDINGS,
    PORTFOLIO_OVERVIEW,
    PORTFOLIO_REVIEW,
    _research_handoff,
    set_portfolio_subtab,
)
from ui.components.portfolio_review_ui import (
    PortfolioReviewContract,
    ThemeReviewItemContract,
    affected_holdings_display,
    portfolio_review_from_inputs,
    theme_understand_contract,
)
from ui.components.understand_popover import render_understand_popover

_REVIEWED_THEMES_KEY = "portfolio_review_reviewed_theme_keys"
_REVIEW_EXPANDED_KEY = "portfolio_review_expanded_theme"


def _reviewed_keys() -> set[str]:
    raw = st.session_state.get(_REVIEWED_THEMES_KEY, set())
    return set(raw) if isinstance(raw, set) else set(raw or [])


def _mark_theme_reviewed(theme_key: str) -> None:
    reviewed = _reviewed_keys()
    reviewed.add(theme_key)
    st.session_state[_REVIEWED_THEMES_KEY] = reviewed


def render_review_context_header(*, contract: PortfolioReviewContract) -> None:
    st.markdown(
        '<div class="apex-review-context-header">',
        unsafe_allow_html=True,
    )
    if st.button("← Back to Overview", key="portfolio_review_back"):
        set_portfolio_subtab(PORTFOLIO_OVERVIEW)
    st.markdown("</div>", unsafe_allow_html=True)


def render_portfolio_explanation_block(*, contract: PortfolioReviewContract) -> None:
    expl = contract.explanation
    qualifier_html = ""
    if expl.qualifier:
        qualifier_html = (
            f'<p class="apex-review-qualifier" role="status">{_esc(expl.qualifier)}</p>'
        )
    st.markdown(
        '<section class="apex-section apex-review-explanation" '
        'aria-label="Portfolio explanation">'
        f'<p class="apex-review-headline">{_esc(expl.headline)}</p>'
        f"{qualifier_html}"
        "</section>",
        unsafe_allow_html=True,
    )
    if expl.show_connect_cta:
        render_broker_sign_in_button(key="portfolio_review_connect", label="Connect Zerodha")
        if expl.connect_message:
            st.caption(expl.connect_message)


def render_review_progress_strip(*, contract: PortfolioReviewContract) -> None:
    if not contract.show_progress:
        return
    reviewed = _reviewed_keys()
    total = len(contract.themes)
    done = sum(1 for theme in contract.themes if theme.theme_key in reviewed)
    st.markdown(
        '<p class="apex-review-progress" role="status" '
        f'aria-valuenow="{done}" aria-valuemax="{total}">'
        f"Review progress · {done} of {total} themes reviewed"
        "</p>",
        unsafe_allow_html=True,
    )


def render_research_handoff_menu(
    *,
    theme: ThemeReviewItemContract,
    index: int,
) -> None:
    symbols = theme.research_symbols
    if not symbols:
        st.caption("Open Holdings to inspect affected positions.")
        return
    if len(symbols) == 1:
        if st.button(
            f"Open Research → {symbols[0]}",
            key=f"review_research_{theme.theme_key}_{index}",
            use_container_width=True,
        ):
            _research_handoff(symbols[0], back_subtab=PORTFOLIO_REVIEW)
        return
    with st.popover("Open Research ▾"):
        for sym_index, symbol in enumerate(symbols[:5]):
            if st.button(
                symbol,
                key=f"review_research_pick_{theme.theme_key}_{index}_{sym_index}",
                use_container_width=True,
            ):
                _research_handoff(symbol, back_subtab=PORTFOLIO_REVIEW)


def render_theme_understand_popover(
    *,
    theme: ThemeReviewItemContract,
    index: int,
) -> None:
    with st.popover(f"Understand {theme.theme_title}"):
        render_understand_popover(
            theme_understand_contract(theme),
            wrap_popover=False,
        )
        render_research_handoff_menu(theme=theme, index=index)


def render_theme_review_item(
    *,
    theme: ThemeReviewItemContract,
    index: int,
    expanded: bool,
    reviewed: bool,
) -> None:
    marker = "✓" if reviewed else ("●" if expanded else "○")
    state_class = " apex-review-theme-reviewed" if reviewed else ""
    expand_class = " apex-review-theme-expanded" if expanded else ""
    holdings_line = affected_holdings_display(theme)
    body = ""
    if expanded and not reviewed:
        body = (
            f'<p class="apex-review-theme-explanation">{_esc(theme.explanation)}</p>'
            f'<p class="apex-review-theme-holdings"><strong>Affected holdings:</strong> '
            f"{_esc(holdings_line)}</p>"
            f'<p class="apex-review-theme-guidance"><strong>Investigate:</strong> '
            f"{_esc(theme.investigation_guidance)}</p>"
        )
    st.markdown(
        '<article class="apex-review-theme-item'
        f'{state_class}{expand_class}" data-theme="{_esc(theme.theme_key)}">'
        f'<p class="apex-review-theme-title">{marker} {index + 1}. '
        f"{_esc(theme.theme_title)}</p>"
        f"{body}"
        "</article>",
        unsafe_allow_html=True,
    )
    if expanded and not reviewed:
        c1, c2, c3 = st.columns(3)
        with c1:
            render_theme_understand_popover(theme=theme, index=index)
        with c2:
            render_research_handoff_menu(theme=theme, index=index)
        with c3:
            if st.button(
                "Mark reviewed ✓",
                key=f"review_mark_{theme.theme_key}_{index}",
                use_container_width=True,
            ):
                _mark_theme_reviewed(theme.theme_key)
                st.rerun()
    elif not expanded and not reviewed:
        if st.button(
            "Expand",
            key=f"review_expand_{theme.theme_key}_{index}",
            use_container_width=True,
        ):
            st.session_state[_REVIEW_EXPANDED_KEY] = theme.theme_key
            st.rerun()


def render_theme_review_queue(*, contract: PortfolioReviewContract) -> None:
    if not contract.themes:
        return
    reviewed = _reviewed_keys()
    expanded_key = str(st.session_state.get(_REVIEW_EXPANDED_KEY, ""))
    if expanded_key not in {theme.theme_key for theme in contract.themes}:
        for theme in contract.themes:
            if theme.theme_key not in reviewed:
                expanded_key = theme.theme_key
                break
    st.markdown(
        '<section class="apex-section apex-review-theme-queue" '
        'aria-label="Theme review queue">'
        '<p class="apex-section-label">Review queue</p>',
        unsafe_allow_html=True,
    )
    for index, theme in enumerate(contract.themes):
        render_theme_review_item(
            theme=theme,
            index=index,
            expanded=theme.theme_key == expanded_key,
            reviewed=theme.theme_key in reviewed,
        )
    st.markdown("</section>", unsafe_allow_html=True)


def render_healthy_reassurance_block(*, contract: PortfolioReviewContract) -> None:
    if contract.themes:
        return
    st.markdown(
        '<section class="apex-section apex-review-reassurance" '
        'aria-label="Portfolio reassurance">',
        unsafe_allow_html=True,
    )
    for item in contract.reassurance_items:
        mark = "✓" if item.passed else "○"
        st.markdown(
            f'<p class="apex-review-reassurance-item">{mark} {_esc(item.label)}</p>',
            unsafe_allow_html=True,
        )
    st.markdown(
        '<p class="apex-review-reassurance-empty">Nothing requires review today.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("</section>", unsafe_allow_html=True)


def render_allocation_policy_review_section(*, contract: PortfolioReviewContract) -> None:
    alloc = contract.allocation
    st.markdown(
        '<section class="apex-section apex-review-allocation" '
        'aria-label="Allocation and policy">'
        f'<p class="apex-review-allocation-summary">{_esc(alloc.summary_line)}</p>',
        unsafe_allow_html=True,
    )
    if alloc.show_understand:
        render_understand_popover(contract.overview_understand)
    st.markdown("</section>", unsafe_allow_html=True)


def render_review_broker_truth_footer(*, contract: PortfolioReviewContract) -> None:
    st.markdown(
        f'<p class="apex-foot apex-portfolio-footer">{_esc(contract.broker_footer)}</p>',
        unsafe_allow_html=True,
    )


def render_review_action_row(*, contract: PortfolioReviewContract) -> None:
    st.markdown(
        '<div class="apex-action-row" role="group" aria-label="Review actions">',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if contract.primary_action == "connect":
            render_broker_sign_in_button(
                key="portfolio_review_primary_connect",
                label=contract.primary_label,
            )
        elif st.button(
            contract.primary_label,
            key="portfolio_review_primary",
            type="primary",
            use_container_width=True,
        ):
            if contract.primary_action == "holdings":
                set_portfolio_subtab(PORTFOLIO_HOLDINGS)
            elif contract.primary_action == "review_next":
                reviewed = _reviewed_keys()
                for theme in contract.themes:
                    if theme.theme_key not in reviewed:
                        st.session_state[_REVIEW_EXPANDED_KEY] = theme.theme_key
                        break
                st.rerun()
    with c2:
        if not contract.themes:
            render_understand_popover(contract.overview_understand)
    st.markdown("</div>", unsafe_allow_html=True)


def render_portfolio_review_experience(*, contract: PortfolioReviewContract) -> None:
    st.markdown(
        '<main class="apex-brief-page apex-portfolio-review" role="main" '
        'aria-labelledby="apex-review-title">'
        '<h2 id="apex-review-title" class="visually-hidden">Portfolio Review</h2>',
        unsafe_allow_html=True,
    )
    render_review_context_header(contract=contract)
    render_portfolio_explanation_block(contract=contract)
    render_review_progress_strip(contract=contract)
    render_review_action_row(contract=contract)
    render_theme_review_queue(contract=contract)
    render_healthy_reassurance_block(contract=contract)
    render_allocation_policy_review_section(contract=contract)
    render_review_broker_truth_footer(contract=contract)
    st.markdown("</main>", unsafe_allow_html=True)


def render_portfolio_review_surface(
    *,
    broker,
    portfolio,
    prefs,
    portfolio_section=None,
    journal_today_pnl=None,
) -> None:
    contract = portfolio_review_from_inputs(
        broker=broker,
        portfolio=portfolio,
        prefs=prefs,
        portfolio_section=portfolio_section,
        journal_today_pnl=journal_today_pnl,
    )
    render_portfolio_review_experience(contract=contract)
