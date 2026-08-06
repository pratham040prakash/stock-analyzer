"""Holdings Experience — render-only presentation (V3-102)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

import streamlit as st

from ui.components.broker_connect import render_broker_sign_in_button
from ui.components.canvas_utils import _esc
from ui.components.holdings_experience_ui import (
    HoldingsExperienceContract,
    HoldingsRowContract,
    holdings_experience_from_inputs,
    holdings_row_understand_contract,
)
from ui.components.portfolio_command_center import PORTFOLIO_HOLDINGS, _research_handoff
from ui.components.understand_popover import render_understand_popover

_HOLDINGS_SEARCH_KEY = "holdings_search_query"
_HOLDINGS_FILTER_KEY = "holdings_filter_key"
_HOLDINGS_SORT_KEY = "holdings_sort_key"

_FILTER_ALL = "all"
_FILTER_ATTENTION = "attention"
_FILTER_OK = "ok"

_SORT_WEIGHT_DESC = "weight_desc"
_SORT_WEIGHT_ASC = "weight_asc"
_SORT_SYMBOL = "symbol"
_SORT_VALUE_DESC = "value_desc"
_SORT_QTY_DESC = "qty_desc"


def _apply_filters_and_sort(
    rows: tuple[HoldingsRowContract, ...],
    *,
    search: str,
    filter_key: str,
    sort_key: str,
) -> tuple[HoldingsRowContract, ...]:
    filtered = list(rows)
    query = search.strip().upper()
    if query:
        filtered = [
            row
            for row in filtered
            if query in row.symbol.upper() or query in row.name.upper()
        ]
    if filter_key == _FILTER_ATTENTION:
        filtered = [row for row in filtered if row.health_key == "attention"]
    elif filter_key == _FILTER_OK:
        filtered = [row for row in filtered if row.health_key == "ok"]
    if sort_key == _SORT_WEIGHT_ASC:
        filtered.sort(key=lambda row: (row.weight_pct, row.symbol))
    elif sort_key == _SORT_SYMBOL:
        filtered.sort(key=lambda row: row.symbol)
    elif sort_key == _SORT_VALUE_DESC:
        filtered.sort(key=lambda row: (-row.value_inr, row.symbol))
    elif sort_key == _SORT_QTY_DESC:
        filtered.sort(key=lambda row: (-row.quantity, row.symbol))
    else:
        filtered.sort(key=lambda row: (-row.weight_pct, row.symbol))
    return tuple(filtered)


def _holdings_row_html(row: HoldingsRowContract) -> str:
    stale_class = " apex-holdings-row-stale" if row.stale else ""
    return (
        '<tr class="apex-holdings-row'
        f'{stale_class}" data-health="{_esc(row.health_key)}">'
        f'<th scope="row" class="apex-holdings-symbol">{_esc(row.symbol)}</th>'
        f'<td class="apex-holdings-name">{_esc(row.name)}</td>'
        f'<td class="apex-holdings-num">{_esc(row.quantity_label)}</td>'
        f'<td class="apex-holdings-num">{_esc(row.average_cost_label)}</td>'
        f'<td class="apex-holdings-num">{_esc(row.ltp_label)}</td>'
        f'<td class="apex-holdings-num">{_esc(row.value_label)}</td>'
        f'<td class="apex-holdings-num">{_esc(row.weight_label)}</td>'
        f'<td class="apex-holdings-health" data-health="{_esc(row.health_key)}">'
        f'{_esc(row.health_label)}</td>'
        "</tr>"
    )


def render_holdings_context_bar(*, contract: HoldingsExperienceContract) -> None:
    ctx = contract.context
    message_html = ""
    if ctx.connect_message:
        message_html = (
            f'<p class="apex-holdings-connect-msg">{_esc(ctx.connect_message)}</p>'
        )
    st.markdown(
        '<section class="apex-section apex-holdings-context" aria-label="Holdings summary">'
        f'<p class="apex-holdings-summary" role="status">{_esc(ctx.summary_line)}</p>'
        f"{message_html}"
        "</section>",
        unsafe_allow_html=True,
    )
    if ctx.show_connect_cta:
        render_broker_sign_in_button(key="holdings_connect", label="Connect Zerodha")


def render_holdings_toolbar(*, contract: HoldingsExperienceContract) -> None:
    ctx = contract.context
    st.markdown(
        '<div class="apex-holdings-toolbar" role="search">',
        unsafe_allow_html=True,
    )
    search = st.text_input(
        "Search holdings",
        value=str(st.session_state.get(_HOLDINGS_SEARCH_KEY, "")),
        placeholder="Search symbol or name…",
        key="holdings_search_input",
        label_visibility="collapsed",
    )
    st.session_state[_HOLDINGS_SEARCH_KEY] = search
    c1, c2, c3 = st.columns([2, 2, 1])
    filter_key = str(st.session_state.get(_HOLDINGS_FILTER_KEY, _FILTER_ALL))
    sort_key = str(st.session_state.get(_HOLDINGS_SORT_KEY, _SORT_WEIGHT_DESC))
    with c1:
        selected_filter = st.radio(
            "Filter holdings",
            options=(_FILTER_ALL, _FILTER_ATTENTION, _FILTER_OK),
            format_func=lambda key: {
                _FILTER_ALL: "All",
                _FILTER_ATTENTION: "Needs attention",
                _FILTER_OK: "Healthy",
            }[key],
            horizontal=True,
            index=(_FILTER_ALL, _FILTER_ATTENTION, _FILTER_OK).index(filter_key)
            if filter_key in (_FILTER_ALL, _FILTER_ATTENTION, _FILTER_OK)
            else 0,
            key="holdings_filter_radio",
            label_visibility="collapsed",
        )
        st.session_state[_HOLDINGS_FILTER_KEY] = selected_filter
    with c2:
        selected_sort = st.selectbox(
            "Sort holdings",
            options=(
                _SORT_WEIGHT_DESC,
                _SORT_WEIGHT_ASC,
                _SORT_SYMBOL,
                _SORT_VALUE_DESC,
                _SORT_QTY_DESC,
            ),
            format_func=lambda key: {
                _SORT_WEIGHT_DESC: "Weight ↓",
                _SORT_WEIGHT_ASC: "Weight ↑",
                _SORT_SYMBOL: "Symbol A–Z",
                _SORT_VALUE_DESC: "Value ↓",
                _SORT_QTY_DESC: "Quantity ↓",
            }[key],
            index=(
                _SORT_WEIGHT_DESC,
                _SORT_WEIGHT_ASC,
                _SORT_SYMBOL,
                _SORT_VALUE_DESC,
                _SORT_QTY_DESC,
            ).index(sort_key)
            if sort_key
            in (
                _SORT_WEIGHT_DESC,
                _SORT_WEIGHT_ASC,
                _SORT_SYMBOL,
                _SORT_VALUE_DESC,
                _SORT_QTY_DESC,
            )
            else 0,
            key="holdings_sort_select",
            label_visibility="collapsed",
        )
        st.session_state[_HOLDINGS_SORT_KEY] = selected_sort
    with c3:
        if ctx.show_sync_cta:
            if st.button("Sync", key="holdings_sync", use_container_width=True):
                st.session_state["_portfolio_sync_requested"] = True
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_holdings_row_understand_popover(*, row: HoldingsRowContract, index: int) -> None:
    with st.popover(f"Understand {row.symbol}"):
        render_understand_popover(
            holdings_row_understand_contract(row),
            wrap_popover=False,
        )
        if st.button(
            f"Open Research →",
            key=f"holdings_understand_research_{row.symbol}_{index}",
            use_container_width=True,
        ):
            _research_handoff(row.symbol, back_subtab=PORTFOLIO_HOLDINGS)


def render_holdings_table_region(
    *,
    rows: tuple[HoldingsRowContract, ...],
    empty_message: str,
) -> None:
    body = (
        f'<tr><td colspan="8" class="apex-holdings-empty">{_esc(empty_message)}</td></tr>'
        if not rows
        else "".join(_holdings_row_html(row) for row in rows)
    )
    st.markdown(
        '<section class="apex-section apex-holdings-table-region" aria-label="Holdings table">'
        '<div class="apex-holdings-table-wrap">'
        '<table class="apex-holdings-table" role="grid">'
        "<thead><tr>"
        "<th scope=\"col\">Symbol</th>"
        "<th scope=\"col\">Name</th>"
        "<th scope=\"col\">Qty</th>"
        "<th scope=\"col\">Avg</th>"
        "<th scope=\"col\">LTP</th>"
        "<th scope=\"col\">Value</th>"
        "<th scope=\"col\">Weight</th>"
        "<th scope=\"col\">Health</th>"
        "</tr></thead><tbody>"
        f"{body}"
        "</tbody></table></div></section>",
        unsafe_allow_html=True,
    )
    if rows:
        st.markdown(
            '<div class="apex-holdings-row-actions" role="group" aria-label="Holdings row actions">',
            unsafe_allow_html=True,
        )
        for index, row in enumerate(rows):
            c1, c2 = st.columns(2)
            with c1:
                if st.button(
                    f"Research {row.symbol} →",
                    key=f"holdings_research_{row.symbol}_{index}",
                    use_container_width=True,
                ):
                    _research_handoff(row.symbol, back_subtab=PORTFOLIO_HOLDINGS)
            with c2:
                render_holdings_row_understand_popover(row=row, index=index)
        st.markdown("</div>", unsafe_allow_html=True)


def render_holdings_card(*, row: HoldingsRowContract, index: int) -> None:
    st.markdown(
        '<article class="apex-holdings-card" '
        f'data-health="{_esc(row.health_key)}">'
        f'<p class="apex-holdings-card-title">{_esc(row.symbol)}'
        f'<span>{_esc(row.weight_label)}</span></p>'
        f'<p class="apex-holdings-card-line">'
        f'{_esc(row.quantity_label)} qty · { _esc(row.value_label)}</p>'
        f'<p class="apex-holdings-card-line apex-holdings-card-muted">'
        f'P&L { _esc(row.pnl_label)}</p>'
        f'<p class="apex-holdings-card-health" data-health="{_esc(row.health_key)}">'
        f'{_esc(row.health_label)}</p>'
        "</article>",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button(f"→ {row.symbol}", key=f"holdings_card_go_{row.symbol}_{index}"):
            _research_handoff(row.symbol, back_subtab=PORTFOLIO_HOLDINGS)
    with c2:
        render_holdings_row_understand_popover(row=row, index=index)


def render_holdings_card_list(
    *,
    rows: tuple[HoldingsRowContract, ...],
    empty_message: str,
) -> None:
    st.markdown(
        '<section class="apex-section apex-holdings-card-list" aria-label="Holdings cards">',
        unsafe_allow_html=True,
    )
    if not rows:
        st.markdown(
            f'<p class="apex-holdings-empty">{_esc(empty_message)}</p>',
            unsafe_allow_html=True,
        )
    else:
        for index, row in enumerate(rows):
            render_holdings_card(row=row, index=index)
    st.markdown("</section>", unsafe_allow_html=True)


def render_watchlist_collapsible(*, contract: HoldingsExperienceContract) -> None:
    if not contract.watchlist:
        return
    label = f"Watchlist ({len(contract.watchlist)} symbols — not held)"
    with st.expander(label, expanded=False):
        for index, row in enumerate(contract.watchlist):
            st.markdown(
                '<div class="apex-holdings-watchlist-row">'
                f'<span class="apex-holdings-symbol">{_esc(row.symbol)}</span>'
                f'<span class="apex-holdings-name">{_esc(row.name)}</span>'
                f'<span class="apex-holdings-num">{_esc(row.ltp_label)}</span>'
                "</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                f"Research {row.symbol} →",
                key=f"holdings_watchlist_{row.symbol}_{index}",
                use_container_width=True,
            ):
                _research_handoff(row.symbol, back_subtab=PORTFOLIO_HOLDINGS)


def render_holdings_empty_state(*, contract: HoldingsExperienceContract) -> None:
    ctx = contract.context
    if ctx.has_holdings:
        return
    message = (
        "No equity holdings in your broker account."
        if not ctx.disconnected
        else "Connect Zerodha to see holdings, or import a saved portfolio in Settings."
    )
    st.markdown(
        f'<section class="apex-section apex-holdings-empty-state" '
        f'aria-label="No holdings"><p>{_esc(message)}</p></section>',
        unsafe_allow_html=True,
    )


def render_holdings_broker_truth_footer(*, contract: HoldingsExperienceContract) -> None:
    st.markdown(
        f'<p class="apex-foot apex-portfolio-footer">{_esc(contract.broker_footer)}</p>',
        unsafe_allow_html=True,
    )


def render_holdings_experience(*, contract: HoldingsExperienceContract) -> None:
    search = str(st.session_state.get(_HOLDINGS_SEARCH_KEY, ""))
    filter_key = str(st.session_state.get(_HOLDINGS_FILTER_KEY, _FILTER_ALL))
    sort_key = str(st.session_state.get(_HOLDINGS_SORT_KEY, _SORT_WEIGHT_DESC))
    visible_rows = _apply_filters_and_sort(
        contract.rows,
        search=search,
        filter_key=filter_key,
        sort_key=sort_key,
    )
    empty_message = (
        contract.filtered_empty_message
        if contract.rows
        else "No holdings to display yet."
    )
    st.markdown(
        '<main class="apex-brief-page apex-holdings-experience" role="main" '
        'aria-labelledby="apex-holdings-title">'
        '<h2 id="apex-holdings-title" class="visually-hidden">Holdings</h2>',
        unsafe_allow_html=True,
    )
    render_holdings_context_bar(contract=contract)
    if not contract.context.has_holdings:
        render_holdings_empty_state(contract=contract)
    else:
        render_holdings_toolbar(contract=contract)
        render_holdings_table_region(rows=visible_rows, empty_message=empty_message)
        render_holdings_card_list(rows=visible_rows, empty_message=empty_message)
        render_watchlist_collapsible(contract=contract)
    render_holdings_broker_truth_footer(contract=contract)
    st.markdown("</main>", unsafe_allow_html=True)


def render_holdings_surface(
    *,
    broker,
    portfolio,
    prefs,
    portfolio_section=None,
    journal_today_pnl=None,
) -> None:
    contract = holdings_experience_from_inputs(
        broker=broker,
        portfolio=portfolio,
        prefs=prefs,
        portfolio_section=portfolio_section,
        journal_today_pnl=journal_today_pnl,
    )
    render_holdings_experience(contract=contract)
