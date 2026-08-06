"""Portfolio Command Center — render-only presentation (V3-101)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

import streamlit as st

from ui.components.broker_connect import render_broker_sign_in_button
from ui.components.canvas_utils import _esc
from ui.components.portfolio_overview_ui import (
    PortfolioAttentionItem,
    PortfolioOverviewContract,
    portfolio_overview_from_inputs,
    portfolio_understand_contract,
)
from ui.components.understand_popover import render_understand_popover
from ui.navigation import request_nav_tab

PORTFOLIO_SUBTAB_KEY = "portfolio_subtab"
PORTFOLIO_OVERVIEW = "overview"
PORTFOLIO_REVIEW = "review"
PORTFOLIO_HOLDINGS = "holdings"
_VALID_SUBTABS = (PORTFOLIO_OVERVIEW, PORTFOLIO_REVIEW, PORTFOLIO_HOLDINGS)


def get_portfolio_subtab() -> str:
    tab = str(st.session_state.get(PORTFOLIO_SUBTAB_KEY, PORTFOLIO_OVERVIEW))
    return tab if tab in _VALID_SUBTABS else PORTFOLIO_OVERVIEW


def set_portfolio_subtab(tab: str) -> None:
    if tab not in _VALID_SUBTABS:
        tab = PORTFOLIO_OVERVIEW
    st.session_state[PORTFOLIO_SUBTAB_KEY] = tab
    st.rerun()


def render_portfolio_subnav(*, active: str) -> None:
    st.markdown(
        '<nav class="apex-portfolio-subnav" aria-label="Portfolio sections">',
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4, c5 = st.columns(5)
    tabs = (
        (PORTFOLIO_OVERVIEW, "Overview", c1),
        (PORTFOLIO_REVIEW, "Review", c2),
        (PORTFOLIO_HOLDINGS, "Holdings", c3),
    )
    placeholders = (("wealth", "Wealth", c4), ("doctor", "Doctor", c5))
    for tab_id, label, col in tabs:
        with col:
            kind = "primary" if active == tab_id else "secondary"
            if st.button(label, key=f"portfolio_sub_{tab_id}", type=kind, use_container_width=True):
                if active != tab_id:
                    set_portfolio_subtab(tab_id)
    for tab_id, label, col in placeholders:
        with col:
            st.button(
                label,
                key=f"portfolio_sub_{tab_id}",
                disabled=True,
                use_container_width=True,
            )
    st.markdown("</nav>", unsafe_allow_html=True)


def render_portfolio_health_hero(*, contract: PortfolioOverviewContract) -> None:
    hero = contract.hero
    stale_html = ""
    if hero.stale_qualified and hero.stale_label:
        stale_html = f'<p class="apex-portfolio-stale" role="status">{_esc(hero.stale_label)}</p>'
    supporting = (
        f'<p class="apex-portfolio-support">{_esc(hero.supporting_reason)}</p>'
        if hero.supporting_reason
        else ""
    )
    st.markdown(
        '<section class="apex-section apex-portfolio-hero" aria-label="Portfolio health">'
        f'<span class="apex-portfolio-badge" data-badge="{_esc(hero.badge_key)}" '
        f'aria-label="Portfolio status: {_esc(hero.badge_label)}">{_esc(hero.badge_label)}</span>'
        f'<h2 class="apex-portfolio-headline" id="apex-portfolio-title">{_esc(hero.headline)}</h2>'
        f"{supporting}{stale_html}"
        "</section>",
        unsafe_allow_html=True,
    )


def _dispatch_primary_action(action: str) -> None:
    if action == "connect":
        return
    if action == "holdings":
        set_portfolio_subtab(PORTFOLIO_HOLDINGS)
    elif action == "review":
        set_portfolio_subtab(PORTFOLIO_REVIEW)
    elif action == "sync":
        st.session_state["_portfolio_sync_requested"] = True


def render_portfolio_action_row(*, contract: PortfolioOverviewContract) -> None:
    action = contract.action
    st.markdown(
        '<div class="apex-action-row" role="group" aria-label="Portfolio actions">',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if action.primary_action == "connect":
            render_broker_sign_in_button(
                key="portfolio_cmd_connect",
                label=action.primary_label,
            )
        elif st.button(
            action.primary_label,
            key="portfolio_cmd_primary",
            type="primary",
            use_container_width=True,
        ):
            _dispatch_primary_action(action.primary_action)
    with c2:
        if action.show_secondary:
            render_portfolio_depth_popover(contract=contract)
    st.markdown("</div>", unsafe_allow_html=True)


def render_portfolio_depth_popover(*, contract: PortfolioOverviewContract) -> None:
    render_understand_popover(portfolio_understand_contract(contract))


def render_portfolio_status_strip(*, contract: PortfolioOverviewContract) -> None:
    status = contract.status
    st.markdown(
        '<section class="apex-section apex-status-strip" aria-label="Portfolio status">'
        '<div class="apex-status-strip-row">'
        f'<div class="apex-status-item"><span class="apex-status-k">Value</span>'
        f'<span class="apex-status-v">{_esc(status.total_value_label)}</span></div>'
        f'<div class="apex-status-item"><span class="apex-status-k">Today</span>'
        f'<span class="apex-status-v apex-status-muted">{_esc(status.day_change_label)}</span></div>'
        f'<div class="apex-status-item"><span class="apex-status-k">Holdings</span>'
        f'<span class="apex-status-v">{_esc(status.holdings_count_label)}</span></div>'
        f'<div class="apex-status-item"><span class="apex-status-k">Cash</span>'
        f'<span class="apex-status-v">{_esc(status.cash_label)}</span></div>'
        f'<div class="apex-status-item"><span class="apex-status-k">Sync</span>'
        f'<span class="apex-status-v">{_esc(status.sync_label)}</span></div>'
        "</div></section>",
        unsafe_allow_html=True,
    )


def _research_handoff(symbol: str, *, back_subtab: str | None = None) -> None:
    clean = symbol.upper().replace(".NS", "").replace(".BO", "").replace("NSE:", "")
    from ui.components.research_workspace_experience import set_research_back_context

    set_research_back_context(tab="My Portfolio", subtab=back_subtab or PORTFOLIO_OVERVIEW)
    request_nav_tab("Single Stock", single_ticker=clean)


def render_attention_list_card(*, contract: PortfolioOverviewContract) -> None:
    attention = contract.attention
    focus = bool(st.session_state.pop("portfolio_focus_attention", False))
    st.markdown(
        '<section class="apex-section apex-portfolio-card apex-portfolio-attention" '
        f'{"apex-portfolio-focus" if focus else ""} '
        'aria-label="Attention items">'
        '<p class="apex-section-label">Attention</p>',
        unsafe_allow_html=True,
    )
    if not attention.items:
        st.markdown(
            f'<p class="apex-portfolio-empty">{_esc(attention.empty_message)}</p>',
            unsafe_allow_html=True,
        )
    else:
        for index, item in enumerate(attention.items, start=1):
            _render_attention_row(index=index, item=item)
    st.markdown("</section>", unsafe_allow_html=True)


def _render_attention_row(*, index: int, item: PortfolioAttentionItem) -> None:
    st.markdown(
        '<div class="apex-portfolio-attention-row">'
        f'<span class="apex-portfolio-attention-index">{index}.</span>'
        f'<span class="apex-portfolio-attention-symbol">{_esc(item.symbol)}</span>'
        f'<span class="apex-portfolio-attention-flag">{_esc(item.flag_type)}</span>'
        f'<span class="apex-portfolio-attention-reason">{_esc(item.reason)}</span>'
        "</div>",
        unsafe_allow_html=True,
    )
    if item.symbol not in ("—", ""):
        if st.button(
            f"Research {item.symbol} →",
            key=f"portfolio_attention_research_{item.symbol}_{index}",
            use_container_width=True,
        ):
            _research_handoff(item.symbol)


def render_allocation_snapshot_card(*, contract: PortfolioOverviewContract) -> None:
    alloc = contract.allocation
    st.markdown(
        '<section class="apex-section apex-portfolio-card apex-portfolio-allocation" '
        'aria-label="Allocation snapshot">'
        '<p class="apex-section-label">Allocation</p>'
        '<div class="apex-portfolio-alloc-bar" role="img" '
        f'aria-label="Core {alloc.core_pct:.0f} percent, Tactical {alloc.tactical_pct:.0f} percent, Cash {alloc.cash_pct:.0f} percent">'
        f'<span class="apex-portfolio-alloc-core" style="width:{alloc.core_pct:.1f}%"></span>'
        f'<span class="apex-portfolio-alloc-tactical" style="width:{alloc.tactical_pct:.1f}%"></span>'
        f'<span class="apex-portfolio-alloc-cash" style="width:{alloc.cash_pct:.1f}%"></span>'
        "</div>"
        '<div class="apex-portfolio-alloc-legend">'
        f'<span>Core {alloc.core_pct:.0f}%</span>'
        f'<span>Tactical {alloc.tactical_pct:.0f}%</span>'
        f'<span>Cash {alloc.cash_pct:.0f}%</span>'
        "</div>"
        f'<p class="apex-portfolio-policy">{_esc(alloc.policy_line)}</p>'
        "</section>",
        unsafe_allow_html=True,
    )


def render_standouts_card(*, contract: PortfolioOverviewContract) -> None:
    standouts = contract.standouts
    st.markdown(
        '<section class="apex-section apex-portfolio-card apex-portfolio-standouts" '
        'aria-label="Standouts">'
        '<p class="apex-section-label">Standouts</p>'
        f'<p class="apex-portfolio-standout-line">'
        f'<strong>Strongest</strong> {_esc(standouts.strongest_symbol)} '
        f'{_esc(standouts.strongest_pct)} total · '
        f'<strong>Weakest</strong> {_esc(standouts.weakest_symbol)} '
        f'{_esc(standouts.weakest_pct)} total'
        f"</p></section>",
        unsafe_allow_html=True,
    )


def render_holdings_preview_card(*, contract: PortfolioOverviewContract) -> None:
    preview = contract.preview
    st.markdown(
        '<section class="apex-section apex-portfolio-card apex-portfolio-preview" '
        'aria-label="Top holdings preview">'
        '<p class="apex-section-label">Top holdings</p>',
        unsafe_allow_html=True,
    )
    if not preview.rows:
        st.markdown(
            '<p class="apex-portfolio-empty">No holdings to preview yet.</p>',
            unsafe_allow_html=True,
        )
    else:
        for row in preview.rows:
            st.markdown(
                '<div class="apex-portfolio-preview-row">'
                f'<span class="apex-portfolio-preview-symbol">{_esc(row.symbol)}</span>'
                f'<span class="apex-portfolio-preview-weight">{row.weight_pct:.0f}%</span>'
                f'<span class="apex-portfolio-preview-health" data-health="{_esc(row.health_key)}">'
                f'{_esc(row.health_label)}</span>'
                "</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                f"Open {row.symbol}",
                key=f"portfolio_preview_{row.symbol}",
                use_container_width=True,
            ):
                set_portfolio_subtab(PORTFOLIO_HOLDINGS)
    if preview.more_count > 0:
        st.markdown(
            f'<p class="apex-portfolio-more">+{preview.more_count} more</p>',
            unsafe_allow_html=True,
        )
        if st.button("View all holdings", key="portfolio_preview_all", use_container_width=True):
            set_portfolio_subtab(PORTFOLIO_HOLDINGS)
    st.markdown("</section>", unsafe_allow_html=True)


def render_broker_truth_footer(*, contract: PortfolioOverviewContract) -> None:
    st.markdown(
        f'<p class="apex-foot apex-portfolio-footer">{_esc(contract.broker_footer)}</p>',
        unsafe_allow_html=True,
    )


def render_portfolio_command_center(*, contract: PortfolioOverviewContract) -> None:
    st.markdown(
        '<main class="apex-brief-page apex-portfolio-command-center" role="main" '
        'aria-labelledby="apex-portfolio-title">',
        unsafe_allow_html=True,
    )
    render_portfolio_health_hero(contract=contract)
    render_portfolio_action_row(contract=contract)
    render_portfolio_status_strip(contract=contract)
    st.markdown('<div class="apex-portfolio-below-fold">', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        render_allocation_snapshot_card(contract=contract)
        render_standouts_card(contract=contract)
    with right:
        render_attention_list_card(contract=contract)
    render_holdings_preview_card(contract=contract)
    render_broker_truth_footer(contract=contract)
    st.markdown("</div></main>", unsafe_allow_html=True)


def render_portfolio_overview_surface(
    *,
    broker,
    portfolio,
    prefs,
    portfolio_section=None,
    journal_today_pnl=None,
) -> None:
    contract = portfolio_overview_from_inputs(
        broker=broker,
        portfolio=portfolio,
        prefs=prefs,
        portfolio_section=portfolio_section,
        journal_today_pnl=journal_today_pnl,
    )
    render_portfolio_command_center(contract=contract)
