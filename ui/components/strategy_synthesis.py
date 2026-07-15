"""Strategy synthesis UI — all pillars in one verdict."""

from __future__ import annotations

import streamlit as st

from analyzer.strategy_synthesis import StrategySynthesis, synthesize_equity, synthesize_options


def render_strategy_synthesis_expander(
    syn: StrategySynthesis | None,
    *,
    key_prefix: str = "syn",
    expanded: bool = False,
) -> None:
    if syn is None:
        return
    title = f"🧠 Strategy synthesis — {syn.target} ({syn.verdict}, {syn.confidence_pct}/100)"
    with st.expander(title, expanded=expanded):
        st.caption(syn.summary)
        st.markdown(f"**{syn.headline}**")
        if syn.positives:
            st.markdown("**Supporting**")
            for p in syn.positives[:6]:
                st.success(p, icon="✅")
        if syn.negatives:
            st.markdown("**Conflicts**")
            for n in syn.negatives[:6]:
                st.warning(n, icon="⚠️")
        if syn.pillars:
            st.markdown("**All pillars**")
            for v in syn.pillars:
                bar = "🟢" if v.vote > 0.2 else ("🔴" if v.vote < -0.2 else "⚪")
                st.caption(f"{bar} {v.emoji} **{v.pillar}** — {v.detail}")
        packet = getattr(syn, "evidence_packet", None)
        decision = getattr(syn, "decision_artifact", None)
        if packet is not None:
            st.caption(
                f"Evidence packet `{packet.packet_id}` · "
                f"{packet.completeness_pct:.0f}% complete · "
                f"{packet.gap_count} gaps · {packet.conflict_count} conflicts"
            )
        if decision is not None:
            st.caption(
                f"Decision `{decision.decision_id}` · **{decision.verdict.value}** · "
                f"confidence {decision.confidence:.0f}% · uncertainty {decision.uncertainty.overall:.0f}%"
            )


def render_options_synthesis_for_leg(
    fno: str,
    option_type: str,
    strike: float,
    *,
    market: str = "india",
    budget: float = 0.0,
    key_prefix: str = "opt_syn",
) -> StrategySynthesis | None:
    try:
        syn = synthesize_options(
            fno, option_type, strike, market=market, budget=budget,
        )
    except Exception as exc:
        st.caption(f"Strategy synthesis unavailable: {exc}")
        return None
    render_strategy_synthesis_expander(syn, key_prefix=key_prefix)
    return syn


def render_equity_synthesis_for_symbol(
    symbol: str,
    *,
    market: str = "india",
    key_prefix: str = "eq_syn",
) -> StrategySynthesis | None:
    try:
        syn = synthesize_equity(symbol, market=market)
    except Exception as exc:
        st.caption(f"Strategy synthesis unavailable: {exc}")
        return None
    render_strategy_synthesis_expander(syn, key_prefix=key_prefix)
    return syn
