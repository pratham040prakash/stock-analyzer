"""Research Journal Experience — render-only presentation (V3-202)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import streamlit as st

from ui.components.canvas_utils import _esc
from ui.components.partner_data import PARTNER_TODAY_LAST_BUNDLE
from ui.components.portfolio_command_center import (
    PORTFOLIO_REVIEW,
    set_portfolio_subtab,
)
from ui.components.proof_state import open_proof_overlay
from ui.components.research_journal_ui import (
    ResearchDecisionEntryContract,
    ResearchJournalDraftContract,
    draft_to_confirmed_entry,
    prior_confirmed_entry_id,
    research_journal_draft_from_workspace,
    symbol_entry_chain,
    understand_from_entry,
)
from ui.components.research_workspace_experience import set_research_back_context
from ui.components.research_workspace_ui import DISPOSITION_LABELS, ResearchWorkspaceContract
from ui.components.understand_popover import render_understand_popover
from ui.navigation import request_nav_tab

JOURNAL_DRAFTS_KEY = "research_journal_drafts"
JOURNAL_ENTRIES_KEY = "research_journal_entries"
JOURNAL_VIEW_KEY = "journal_view"
JOURNAL_DRAFT_ID_KEY = "journal_draft_id"
JOURNAL_ENTRY_ID_KEY = "journal_entry_id"

JOURNAL_TIMELINE = "timeline"
JOURNAL_DRAFTS = "drafts"
JOURNAL_CONFIRM = "confirm"
JOURNAL_DETAIL = "detail"


def _drafts_store() -> dict[str, ResearchJournalDraftContract]:
    raw = st.session_state.get(JOURNAL_DRAFTS_KEY, {})
    if not isinstance(raw, dict):
        raw = {}
    st.session_state[JOURNAL_DRAFTS_KEY] = raw
    return raw


def _entries_store() -> list[ResearchDecisionEntryContract]:
    raw = st.session_state.get(JOURNAL_ENTRIES_KEY, [])
    if not isinstance(raw, list):
        raw = []
    st.session_state[JOURNAL_ENTRIES_KEY] = raw
    return raw


def get_journal_view() -> str:
    view = str(st.session_state.get(JOURNAL_VIEW_KEY, JOURNAL_TIMELINE))
    return view if view in (JOURNAL_TIMELINE, JOURNAL_DRAFTS, JOURNAL_CONFIRM, JOURNAL_DETAIL) else JOURNAL_TIMELINE


def set_journal_view(view: str) -> None:
    st.session_state[JOURNAL_VIEW_KEY] = view
    st.rerun()


def list_journal_drafts() -> tuple[ResearchJournalDraftContract, ...]:
    drafts = _drafts_store()
    items = sorted(drafts.values(), key=lambda item: item.recorded_at, reverse=True)
    return tuple(items)


def list_journal_entries() -> tuple[ResearchDecisionEntryContract, ...]:
    entries = _entries_store()
    return tuple(sorted(entries, key=lambda item: item.recorded_at, reverse=True))


def get_journal_draft(draft_id: str) -> ResearchJournalDraftContract | None:
    return _drafts_store().get(draft_id)


def get_journal_entry(entry_id: str) -> ResearchDecisionEntryContract | None:
    for entry in _entries_store():
        if entry.entry_id == entry_id:
            return entry
    return None


def save_journal_draft(draft: ResearchJournalDraftContract) -> None:
    store = _drafts_store()
    store[draft.entry_id] = draft


def discard_journal_draft(draft_id: str) -> None:
    store = _drafts_store()
    store.pop(draft_id, None)


def confirm_journal_draft(
    draft_id: str,
    *,
    supersedes_entry_id: str = "",
) -> ResearchDecisionEntryContract | None:
    draft = get_journal_draft(draft_id)
    if draft is None:
        return None
    entry = draft_to_confirmed_entry(draft, supersedes_entry_id=supersedes_entry_id)
    _entries_store().append(entry)
    discard_journal_draft(draft_id)
    if draft.review_theme_key:
        reviewed = set(st.session_state.get("portfolio_review_reviewed_theme_keys", set()) or set())
        reviewed.add(draft.review_theme_key)
        st.session_state["portfolio_review_reviewed_theme_keys"] = reviewed
    return entry


def create_journal_draft_from_research(*, contract: ResearchWorkspaceContract) -> str:
    cached = st.session_state.get(PARTNER_TODAY_LAST_BUNDLE)
    prior = prior_confirmed_entry_id(symbol=contract.symbol, entries=list_journal_entries())
    draft = research_journal_draft_from_workspace(
        contract=contract,
        session=st.session_state,
        cached=cached if isinstance(cached, dict) else None,
        prior_entry_id=prior,
    )
    save_journal_draft(draft)
    return draft.entry_id


def navigate_to_journal_confirm(draft_id: str) -> None:
    request_nav_tab(
        "Journal",
        **{
            JOURNAL_VIEW_KEY: JOURNAL_CONFIRM,
            JOURNAL_DRAFT_ID_KEY: draft_id,
        },
    )


def _narrative_preview(text: str, *, limit: int = 120) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "…"


def _portfolio_chip(entry: ResearchDecisionEntryContract | ResearchJournalDraftContract) -> str:
    if not entry.portfolio_held:
        return "Not held"
    parts = [f"Held {entry.portfolio_weight_label}"]
    if entry.portfolio_flag_label:
        parts.append(f"⚠ {entry.portfolio_flag_label}")
    elif entry.portfolio_health_label and entry.portfolio_health_label != "—":
        parts.append(entry.portfolio_health_label)
    return " · ".join(parts)


def _timeline_group(recorded_at: str) -> str:
    try:
        dt = datetime.fromisoformat(recorded_at)
    except ValueError:
        return "Earlier"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    local = dt.astimezone()
    local_now = now.astimezone()
    if local.date() == local_now.date():
        return "Today"
    week_ago = local_now - timedelta(days=7)
    if local.date() >= week_ago.date():
        return "This week"
    month_ago = local_now - timedelta(days=31)
    if local.date() >= month_ago.date():
        return "This month"
    return "Earlier"


def render_journal_subnav(*, active: str) -> None:
    st.markdown(
        '<nav class="apex-journal-subnav" aria-label="Journal sections">',
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    tabs = (
        (JOURNAL_TIMELINE, "Timeline", c1),
        (JOURNAL_DRAFTS, "Drafts", c2),
    )
    for tab_id, label, col in tabs:
        with col:
            kind = "primary" if active == tab_id else "secondary"
            if st.button(label, key=f"journal_sub_{tab_id}", type=kind, use_container_width=True):
                if active != tab_id:
                    st.session_state[JOURNAL_VIEW_KEY] = tab_id
                    st.session_state.pop(JOURNAL_DRAFT_ID_KEY, None)
                    st.session_state.pop(JOURNAL_ENTRY_ID_KEY, None)
                    st.rerun()
    with c3:
        st.button("Receipts", key="journal_sub_receipts", disabled=True, use_container_width=True)
    with c4:
        st.button("Trades", key="journal_sub_trades", disabled=True, use_container_width=True)
    st.markdown("</nav>", unsafe_allow_html=True)


def render_editable_narrative_block(
    *,
    draft: ResearchJournalDraftContract,
    text_key: str,
) -> None:
    st.markdown(
        '<div class="apex-journal-editable-narrative" aria-label="Your decision">'
        '<p class="apex-journal-block-label">Your decision (editable)</p>',
        unsafe_allow_html=True,
    )
    if text_key not in st.session_state:
        st.session_state[text_key] = draft.user_narrative
    st.text_area(
        "Your decision",
        key=text_key,
        label_visibility="collapsed",
        height=100,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_disposition_selector(*, draft: ResearchJournalDraftContract, disposition_key: str) -> str:
    options = list(DISPOSITION_LABELS.keys())
    labels = [DISPOSITION_LABELS[key] for key in options]
    if disposition_key not in st.session_state:
        st.session_state[disposition_key] = draft.disposition
    current = st.session_state.get(disposition_key, draft.disposition)
    try:
        default_index = options.index(current)
    except ValueError:
        default_index = 0
    choice = st.radio(
        "Disposition",
        options=labels,
        index=default_index,
        horizontal=True,
        key=f"journal_disposition_radio_{draft.entry_id}",
    )
    disposition = options[labels.index(choice)]
    st.session_state[disposition_key] = disposition
    return disposition


def render_frozen_system_summary_block(
    *,
    entry: ResearchDecisionEntryContract | ResearchJournalDraftContract,
) -> None:
    st.markdown(
        '<section class="apex-journal-frozen-summary" aria-readonly="true" '
        'aria-label="System context at decision time">'
        '<p class="apex-journal-block-label">System context (read-only)</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="apex-journal-frozen-line">'
        f'<strong>View</strong> {_esc(entry.investment_view_label)} · '
        f"{_esc(entry.investment_view_summary)}</p>",
        unsafe_allow_html=True,
    )
    for line in entry.system_summary_lines:
        st.markdown(f'<p class="apex-journal-frozen-line">{_esc(line)}</p>', unsafe_allow_html=True)
    st.markdown("</section>", unsafe_allow_html=True)


def render_research_completion_strip(*, entry: ResearchDecisionEntryContract | ResearchJournalDraftContract) -> None:
    reviewed_count = sum(1 for flag in entry.questions_reviewed if flag)
    st.markdown(
        '<p class="apex-journal-completion" role="status">'
        f"{reviewed_count} of 7 research questions reviewed · Q7 decision recorded"
        "</p>",
        unsafe_allow_html=True,
    )


def render_portfolio_linkage_block(*, entry: ResearchDecisionEntryContract | ResearchJournalDraftContract) -> None:
    chip = _portfolio_chip(entry)
    st.markdown(
        '<section class="apex-journal-portfolio-linkage" aria-label="Portfolio at decision">'
        f'<p class="apex-journal-block-label">Portfolio at decision</p>'
        f'<p class="apex-journal-portfolio-chip">{_esc(chip)}</p>'
        "</section>",
        unsafe_allow_html=True,
    )


def render_understand_gateway(*, entry: ResearchDecisionEntryContract | ResearchJournalDraftContract) -> None:
    with st.popover("Help me understand ▾"):
        render_understand_popover(understand_from_entry(entry), wrap_popover=False)


def render_proof_link(*, entry: ResearchDecisionEntryContract | ResearchJournalDraftContract) -> None:
    if not entry.show_proof:
        st.caption("Proof unavailable for this entry.")
        return
    if st.button("View proof", key=f"journal_proof_{entry.entry_id}", use_container_width=True):
        open_proof_overlay(origin="journal", proof_mode="decision", symbol=entry.symbol)


def render_evolution_chain(
    *,
    entry: ResearchDecisionEntryContract,
    entries: tuple[ResearchDecisionEntryContract, ...],
) -> None:
    chain = symbol_entry_chain(symbol=entry.symbol, entries=entries)
    others = [item for item in chain if item.entry_id != entry.entry_id]
    if not others:
        return
    st.markdown(
        '<section class="apex-journal-evolution" aria-label="Decision history for symbol">'
        f'<p class="apex-journal-block-label">Decision history for { _esc(entry.symbol) }</p>',
        unsafe_allow_html=True,
    )
    for prior in others[:5]:
        st.markdown(
            '<div class="apex-journal-evolution-row">'
            f'<span class="apex-journal-evolution-date">{_esc(prior.recorded_at_label)}</span> '
            f'<span class="apex-journal-evolution-disposition">{_esc(prior.disposition_label)}</span> '
            f'<span class="apex-journal-evolution-preview">{_esc(_narrative_preview(prior.user_narrative))}</span>'
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button(
            f"Open {prior.recorded_at_label}",
            key=f"journal_open_prior_{prior.entry_id}",
            use_container_width=True,
        ):
            st.session_state[JOURNAL_VIEW_KEY] = JOURNAL_DETAIL
            st.session_state[JOURNAL_ENTRY_ID_KEY] = prior.entry_id
            st.rerun()
    st.markdown("</section>", unsafe_allow_html=True)


def render_outcome_review_placeholder(*, entry: ResearchDecisionEntryContract) -> None:
    st.markdown(
        '<section class="apex-journal-outcome-placeholder" aria-label="Outcome review future">'
        '<p class="apex-journal-block-label">Outcome review (future)</p>'
        '<p class="apex-journal-outcome-note">Outcome review: Not yet due · Scheduled after decision cadence</p>',
        unsafe_allow_html=True,
    )
    st.button(
        "Start Outcome Review",
        key=f"journal_outcome_review_{entry.entry_id}",
        disabled=True,
        use_container_width=True,
    )
    st.caption("Outcome Review compares what you believed with what happened — coming in a future release.")
    st.markdown("</section>", unsafe_allow_html=True)


def render_return_actions(*, entry: ResearchDecisionEntryContract | ResearchJournalDraftContract) -> None:
    st.markdown(
        '<div class="apex-journal-return-actions" role="group" aria-label="Continue workflow">',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Open Research", key=f"journal_open_research_{entry.entry_id}", use_container_width=True):
            set_research_back_context(
                tab=entry.research_back_tab,
                subtab=entry.research_back_subtab or None,
            )
            request_nav_tab("Single Stock", single_ticker=entry.symbol)
    with c2:
        if st.button("Open Portfolio", key=f"journal_open_portfolio_{entry.entry_id}", use_container_width=True):
            subtab = entry.research_back_subtab or None
            if subtab:
                set_portfolio_subtab(subtab)
            request_nav_tab("My Portfolio")
    st.markdown("</div>", unsafe_allow_html=True)


def render_journal_entry_card(
    *,
    entry: ResearchDecisionEntryContract,
    index: int,
) -> None:
    preview = _narrative_preview(entry.user_narrative)
    chip = _portfolio_chip(entry)
    proof_line = " · Proof available" if entry.show_proof else ""
    st.markdown(
        '<article class="apex-journal-entry-card" aria-label="Research decision entry">'
        '<span class="apex-journal-entry-type">Research Decision</span>'
        f'<p class="apex-journal-entry-headline">'
        f'{_esc(entry.symbol)} · {_esc(entry.disposition_label)} · {_esc(entry.recorded_at_label)}</p>'
        f'<p class="apex-journal-entry-preview">"{_esc(preview)}"</p>'
        f'<p class="apex-journal-entry-meta">From {_esc(entry.source_label)}{proof_line} · {_esc(chip)}</p>'
        "</article>",
        unsafe_allow_html=True,
    )
    if st.button(
        f"View {entry.symbol} entry",
        key=f"journal_timeline_open_{entry.entry_id}_{index}",
        use_container_width=True,
    ):
        st.session_state[JOURNAL_VIEW_KEY] = JOURNAL_DETAIL
        st.session_state[JOURNAL_ENTRY_ID_KEY] = entry.entry_id
        st.rerun()


def render_journal_timeline(*, entries: tuple[ResearchDecisionEntryContract, ...]) -> None:
    st.markdown(
        '<section class="apex-journal-timeline" aria-label="Decision timeline">',
        unsafe_allow_html=True,
    )
    if not entries:
        st.markdown(
            '<p class="apex-journal-empty">No confirmed research decisions yet. '
            "Save an Investment Decision from the Research Workbench.</p>",
            unsafe_allow_html=True,
        )
        st.markdown("</section>", unsafe_allow_html=True)
        return

    groups: dict[str, list[ResearchDecisionEntryContract]] = {}
    for entry in entries:
        groups.setdefault(_timeline_group(entry.recorded_at), []).append(entry)

    for group_name in ("Today", "This week", "This month", "Earlier"):
        group_entries = groups.get(group_name, [])
        if not group_entries:
            continue
        st.markdown(f'<p class="apex-journal-group-label">{_esc(group_name)}</p>', unsafe_allow_html=True)
        for index, entry in enumerate(group_entries):
            render_journal_entry_card(entry=entry, index=index)
    st.markdown("</section>", unsafe_allow_html=True)


def render_journal_drafts_inbox(*, drafts: tuple[ResearchJournalDraftContract, ...]) -> None:
    st.markdown(
        '<section class="apex-journal-drafts-inbox" aria-label="Journal drafts">',
        unsafe_allow_html=True,
    )
    if not drafts:
        st.markdown(
            '<p class="apex-journal-empty">No drafts waiting for confirmation.</p>',
            unsafe_allow_html=True,
        )
        st.markdown("</section>", unsafe_allow_html=True)
        return

    for index, draft in enumerate(drafts):
        preview = _narrative_preview(draft.user_narrative or "Draft without narrative yet")
        st.markdown(
            '<div class="apex-journal-draft-card">'
            f'<p class="apex-journal-entry-headline">{_esc(draft.symbol)} · '
            f'{_esc(draft.disposition_label)} · Draft</p>'
            f'<p class="apex-journal-entry-preview">"{_esc(preview)}"</p>'
            "</div>",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button(
                "Confirm draft",
                key=f"journal_draft_confirm_{draft.entry_id}_{index}",
                type="primary",
                use_container_width=True,
            ):
                st.session_state[JOURNAL_VIEW_KEY] = JOURNAL_CONFIRM
                st.session_state[JOURNAL_DRAFT_ID_KEY] = draft.entry_id
                st.rerun()
        with c2:
            if st.button(
                "Discard",
                key=f"journal_draft_discard_{draft.entry_id}_{index}",
                use_container_width=True,
            ):
                discard_journal_draft(draft.entry_id)
                st.rerun()
    st.markdown("</section>", unsafe_allow_html=True)


def _updated_draft_from_session(
    draft: ResearchJournalDraftContract,
    *,
    text_key: str,
    disposition_key: str,
) -> ResearchJournalDraftContract:
    narrative = str(st.session_state.get(text_key, draft.user_narrative) or "").strip()
    disposition = str(st.session_state.get(disposition_key, draft.disposition) or draft.disposition)
    if disposition not in DISPOSITION_LABELS:
        disposition = draft.disposition
    return ResearchJournalDraftContract(
        entry_id=draft.entry_id,
        entry_type=draft.entry_type,
        symbol=draft.symbol,
        recorded_at=draft.recorded_at,
        recorded_at_label=draft.recorded_at_label,
        user_narrative=narrative,
        disposition=disposition,
        disposition_label=DISPOSITION_LABELS[disposition],
        investment_view_label=draft.investment_view_label,
        investment_view_summary=draft.investment_view_summary,
        system_summary_lines=draft.system_summary_lines,
        questions_reviewed=draft.questions_reviewed,
        decision_id=draft.decision_id,
        evidence_packet_id=draft.evidence_packet_id,
        bundle_built_at=draft.bundle_built_at,
        bundle_version=draft.bundle_version,
        portfolio_held=draft.portfolio_held,
        portfolio_weight_label=draft.portfolio_weight_label,
        portfolio_health_label=draft.portfolio_health_label,
        portfolio_flag_label=draft.portfolio_flag_label,
        review_theme_key=draft.review_theme_key,
        research_back_tab=draft.research_back_tab,
        research_back_subtab=draft.research_back_subtab,
        show_proof=draft.show_proof,
        understand=draft.understand,
        prior_entry_id=draft.prior_entry_id,
        supersedes_entry_id=draft.supersedes_entry_id,
    )


def render_journal_confirm_draft(*, draft: ResearchJournalDraftContract) -> None:
    text_key = f"journal_draft_text_{draft.entry_id}"
    disposition_key = f"journal_draft_disposition_{draft.entry_id}"
    supersedes_key = f"journal_supersedes_{draft.entry_id}"

    st.markdown(
        '<section class="apex-journal-confirm" aria-label="Confirm journal entry">'
        f'<h2 class="apex-journal-title">Confirm Journal Entry</h2>'
        f'<p class="apex-journal-confirm-headline">Research Decision · {_esc(draft.symbol)}</p>'
        f'<p class="apex-journal-confirm-disposition">Disposition: {_esc(draft.disposition_label)}</p>'
        '<p class="apex-journal-immutability-note" role="note">'
        "Once confirmed, this entry becomes part of your decision history. It cannot be edited — only followed up."
        "</p>",
        unsafe_allow_html=True,
    )

    render_editable_narrative_block(draft=draft, text_key=text_key)
    disposition = render_disposition_selector(draft=draft, disposition_key=disposition_key)
    render_frozen_system_summary_block(entry=draft)
    render_research_completion_strip(entry=draft)
    render_portfolio_linkage_block(entry=draft)

    c1, c2 = st.columns(2)
    with c1:
        render_understand_gateway(entry=draft)
    with c2:
        render_proof_link(entry=draft)

    if draft.prior_entry_id:
        prior = get_journal_entry(draft.prior_entry_id)
        prior_label = prior.disposition_label if prior else "prior decision"
        st.checkbox(
            f"Replaces my prior {draft.symbol} decision ({prior_label})",
            key=supersedes_key,
        )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Discard", key=f"journal_confirm_discard_{draft.entry_id}", use_container_width=True):
            discard_journal_draft(draft.entry_id)
            st.session_state[JOURNAL_VIEW_KEY] = JOURNAL_DRAFTS
            st.session_state.pop(JOURNAL_DRAFT_ID_KEY, None)
            st.rerun()
    with c2:
        if st.button("Back to Research", key=f"journal_confirm_back_research_{draft.entry_id}", use_container_width=True):
            set_research_back_context(tab=draft.research_back_tab, subtab=draft.research_back_subtab or None)
            request_nav_tab("Single Stock", single_ticker=draft.symbol)
    with c3:
        if st.button("Confirm entry ✓", key=f"journal_confirm_save_{draft.entry_id}", type="primary", use_container_width=True):
            updated = _updated_draft_from_session(
                draft,
                text_key=text_key,
                disposition_key=disposition_key,
            )
            save_journal_draft(updated)
            supersedes = draft.prior_entry_id if st.session_state.get(supersedes_key) else ""
            entry = confirm_journal_draft(updated.entry_id, supersedes_entry_id=supersedes)
            if entry is None:
                st.error("Draft not found — it may have been discarded.")
                return
            st.session_state[JOURNAL_VIEW_KEY] = JOURNAL_DETAIL
            st.session_state[JOURNAL_ENTRY_ID_KEY] = entry.entry_id
            st.session_state.pop(JOURNAL_DRAFT_ID_KEY, None)
            if draft.research_back_subtab == PORTFOLIO_REVIEW:
                st.session_state["_journal_return_to_review"] = True
            st.rerun()

    st.markdown("</section>", unsafe_allow_html=True)


def render_journal_entry_detail(
    *,
    entry: ResearchDecisionEntryContract,
    entries: tuple[ResearchDecisionEntryContract, ...],
) -> None:
    st.markdown(
        '<section class="apex-journal-detail" aria-label="Research decision detail">'
        f'<h2 class="apex-journal-title">Research Decision · {_esc(entry.symbol)}</h2>'
        f'<p class="apex-journal-recorded-badge">Recorded · {_esc(entry.disposition_label)} · '
        f'{_esc(entry.recorded_at_label)}</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="apex-journal-readonly-narrative" aria-readonly="true" '
        'aria-label="Your decision">'
        '<p class="apex-journal-block-label">Your decision</p>'
        f'<p class="apex-journal-narrative">{_esc(entry.user_narrative)}</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    render_frozen_system_summary_block(entry=entry)
    render_research_completion_strip(entry=entry)
    render_portfolio_linkage_block(entry=entry)

    context_bits = []
    if entry.bundle_built_at:
        context_bits.append(f"bundle {entry.bundle_built_at}")
    if entry.decision_id:
        context_bits.append(f"decision_id {entry.decision_id[:8]}")
    if entry.show_proof:
        context_bits.append("proof linked")
    if context_bits:
        st.markdown(
            f'<p class="apex-journal-context-line">Context: {_esc(" · ".join(context_bits))}</p>',
            unsafe_allow_html=True,
        )

    c1, c2 = st.columns(2)
    with c1:
        render_proof_link(entry=entry)
    with c2:
        render_understand_gateway(entry=entry)

    render_evolution_chain(entry=entry, entries=entries)
    render_outcome_review_placeholder(entry=entry)
    render_return_actions(entry=entry)

    if st.session_state.pop("_journal_return_to_review", False):
        if st.button("Return to Portfolio Review", key=f"journal_return_review_{entry.entry_id}", use_container_width=True):
            set_portfolio_subtab(PORTFOLIO_REVIEW)
            request_nav_tab("My Portfolio")

    if st.button("← Back to Timeline", key=f"journal_detail_back_{entry.entry_id}", use_container_width=True):
        st.session_state[JOURNAL_VIEW_KEY] = JOURNAL_TIMELINE
        st.session_state.pop(JOURNAL_ENTRY_ID_KEY, None)
        st.rerun()

    st.markdown("</section>", unsafe_allow_html=True)


def render_research_journal_experience() -> None:
    view = get_journal_view()
    draft_id = str(st.session_state.get(JOURNAL_DRAFT_ID_KEY, "") or "")
    entry_id = str(st.session_state.get(JOURNAL_ENTRY_ID_KEY, "") or "")
    drafts = list_journal_drafts()
    entries = list_journal_entries()

    st.markdown(
        '<main class="apex-brief-page apex-research-journal" role="main" '
        'aria-labelledby="apex-journal-title">'
        '<h2 id="apex-journal-title" class="visually-hidden">Research Journal</h2>',
        unsafe_allow_html=True,
    )
    render_journal_subnav(active=view if view in (JOURNAL_TIMELINE, JOURNAL_DRAFTS) else JOURNAL_TIMELINE)

    if view == JOURNAL_CONFIRM and draft_id:
        draft = get_journal_draft(draft_id)
        if draft is None:
            st.warning("Draft not found — it may have been confirmed or discarded.")
            render_journal_drafts_inbox(drafts=drafts)
        else:
            render_journal_confirm_draft(draft=draft)
    elif view == JOURNAL_DETAIL and entry_id:
        entry = get_journal_entry(entry_id)
        if entry is None:
            st.warning("Entry not found.")
            render_journal_timeline(entries=entries)
        else:
            render_journal_entry_detail(entry=entry, entries=entries)
    elif view == JOURNAL_DRAFTS:
        render_journal_drafts_inbox(drafts=drafts)
    else:
        render_journal_timeline(entries=entries)

    st.markdown("</main>", unsafe_allow_html=True)
