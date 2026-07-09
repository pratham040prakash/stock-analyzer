"""UI — options entry gate banner and checklist."""

from __future__ import annotations

import streamlit as st

from analyzer.options_entry_gate import OptionsEntryGate, assess_pick_entry_gate, gate_label_short
from analyzer.options_trade_selection import load_selected_option


def render_options_entry_gate_banner(pick, *, market: str = "india") -> OptionsEntryGate | None:
    """Prominent gate for starred / recommended option leg."""
    gate = assess_pick_entry_gate(pick, market=market)
    if gate is None:
        return None

    if gate.phase == "do_not_enter":
        st.error(f"**{gate.emoji} {gate.headline}** — {gate.detail}")
        st.warning(f"**Action:** {gate.action}")
    elif gate.phase == "enter_ok":
        st.success(f"**{gate.emoji} {gate.headline}** — {gate.detail}")
    elif gate.phase == "observe":
        st.info(f"**{gate.emoji} {gate.headline}** — {gate.detail}")
    else:
        st.warning(f"**{gate.emoji} {gate.headline}** — {gate.detail}")

    with st.expander("Entry checklist", expanded=gate.phase in ("do_not_enter", "observe")):
        for line in gate.checks:
            st.markdown(f"- {line}")
        st.caption(f"**Next step:** {gate.action}")

    return gate


def render_starred_option_gate(market: str = "india") -> OptionsEntryGate | None:
    """Show gate for user's starred option leg if any."""
    pick = load_selected_option()
    if not pick:
        return None
    st.markdown("#### 🚦 Entry gate — your starred option")
    class _P:
        fno_symbol = pick["fno_symbol"]
        option_type = pick["option_type"]
        strike = pick["strike"]
    return render_options_entry_gate_banner(_P(), market=market)


def gate_table_cell(pick, *, market: str = "india") -> str:
    gate = assess_pick_entry_gate(pick, market=market)
    if not gate:
        return "—"
    return gate_label_short(gate)
