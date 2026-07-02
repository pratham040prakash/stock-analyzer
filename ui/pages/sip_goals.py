"""SIP & financial goals planner UI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.markets import is_india_market
from analyzer.sip_export import plan_to_csv, plan_to_markdown
from analyzer.sip_planner import (
    DEFAULT_GOAL_AMOUNTS_INR,
    DEFAULT_GOAL_AMOUNTS_USD,
    DEFAULT_GOAL_YEARS,
    GOAL_PRESETS,
    SipPlannerInput,
    build_sip_plan,
    future_value_sip,
    total_invested,
)
from analyzer.sip_reminders import format_sip_plan_telegram, run_sip_reminders
from analyzer.sip_storage import delete_goal, list_saved_goals, save_goal, update_reminder
from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured


def _currency_label(market: str) -> str:
    return "₹" if is_india_market(market) else "$"


def _render_plan_form(market: str) -> SipPlannerInput | None:
    sym = _currency_label(market)
    defaults = DEFAULT_GOAL_AMOUNTS_INR if is_india_market(market) else DEFAULT_GOAL_AMOUNTS_USD

    g1, g2, g3 = st.columns(3)
    with g1:
        goal_preset = st.selectbox("Goal", list(GOAL_PRESETS.keys()), key="sip_goal_preset")
    with g2:
        experience = st.selectbox(
            "Experience",
            ["new", "some"],
            format_func=lambda x: "Very new (< 6 months)" if x == "new" else "Some experience (6M+)",
            key="sip_experience",
        )
    with g3:
        risk_profile = st.selectbox(
            "Risk profile",
            ["conservative", "balanced", "growth"],
            index=1,
            key="sip_risk",
        )

    st.caption(GOAL_PRESETS[goal_preset])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        target = st.number_input(
            f"Target corpus ({sym})",
            min_value=10000.0,
            value=float(defaults.get(goal_preset, 25_00_000 if is_india_market(market) else 75_000)),
            step=50000.0 if is_india_market(market) else 5000.0,
            key="sip_target",
        )
    with c2:
        years = st.number_input(
            "Years to goal",
            min_value=1.0,
            max_value=40.0,
            value=float(DEFAULT_GOAL_YEARS.get(goal_preset, 10.0)),
            step=1.0,
            key="sip_years",
        )
    with c3:
        current = st.number_input(
            f"Already saved ({sym})",
            min_value=0.0,
            value=0.0,
            step=10000.0 if is_india_market(market) else 1000.0,
            key="sip_current",
        )
    with c4:
        annual_return = st.slider(
            "Assumed annual return %",
            min_value=6.0,
            max_value=16.0,
            value=12.0,
            step=0.5,
            key="sip_return",
        )

    mode = st.radio(
        "Plan mode",
        ["Calculate required monthly SIP", "I have a fixed monthly budget"],
        horizontal=True,
        key="sip_mode",
    )
    monthly_budget = None
    if mode == "I have a fixed monthly budget":
        monthly_budget = st.number_input(
            f"Monthly budget ({sym})",
            min_value=500.0,
            value=15000.0 if is_india_market(market) else 500.0,
            step=1000.0 if is_india_market(market) else 100.0,
            key="sip_budget",
        )

    step_up = st.slider(
        "Annual SIP step-up % (0 = flat)",
        min_value=0.0,
        max_value=20.0,
        value=5.0 if experience == "some" else 0.0,
        step=1.0,
        key="sip_step_up",
    )

    if st.button("Build SIP plan", type="primary", key="sip_build"):
        return SipPlannerInput(
            goal_name=goal_preset,
            target_amount=target,
            years=years,
            current_corpus=current,
            monthly_budget=monthly_budget,
            annual_return_pct=annual_return,
            step_up_annual_pct=step_up,
            risk_profile=risk_profile,
            experience=experience,
            market=market,
        )
    return None


def _render_plan_results(plan, market: str, experience: str) -> None:
    sym = _currency_label(market)

    progress = min(1.0, plan.projected_corpus / plan.target_amount) if plan.target_amount > 0 else 0
    st.progress(progress, text=f"Projected {progress * 100:.0f}% of target")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Monthly SIP", f"{sym}{plan.monthly_sip:,.0f}")
    m2.metric("Projected corpus", f"{sym}{plan.projected_corpus:,.0f}")
    m3.metric("Target", f"{sym}{plan.target_amount:,.0f}")
    gap_pct = (
        round((plan.projected_corpus / plan.target_amount - 1) * 100, 1)
        if plan.target_amount > 0
        else 0
    )
    m4.metric("vs Target", f"{gap_pct:+.1f}%")

    if plan.monthly_budget:
        if plan.surplus_or_gap >= 0:
            st.success(
                f"Budget **{sym}{plan.monthly_budget:,.0f}/mo** covers the goal "
                f"(surplus **{sym}{plan.surplus_or_gap:,.0f}/mo** vs minimum required)."
            )
        else:
            st.warning(
                f"Budget short by **{sym}{abs(plan.surplus_or_gap):,.0f}/mo** — "
                "extend timeline, lower target, or raise step-up."
            )
    elif plan.projected_corpus < plan.target_amount * 0.98:
        st.warning("Projected corpus is below target — increase monthly SIP or years.")

    st.info(plan.guidance)

    st.markdown("#### Monthly allocation")
    alloc_rows = [{
        "Instrument": line.name,
        "Ticker": line.ticker.replace(".NS", ""),
        "Sleeve": line.sleeve.replace("_", " ").title(),
        "Weight %": f"{line.weight_pct:.0f}",
        f"Monthly ({sym})": f"{line.monthly_amount:,.0f}",
        "Note": line.note,
    } for line in plan.allocation]
    st.dataframe(pd.DataFrame(alloc_rows), use_container_width=True, hide_index=True)

    st.markdown("#### Growth milestones")
    ms_df = pd.DataFrame([
        {"Year": m.year, "Invested": m.invested, "Projected corpus": m.projected_corpus}
        for m in plan.milestones
    ])
    if not ms_df.empty:
        st.line_chart(ms_df.set_index("Year")[["Invested", "Projected corpus"]])
        st.dataframe(
            ms_df.assign(
                **{
                    "Invested": ms_df["Invested"].map(lambda x: f"{sym}{x:,.0f}"),
                    "Projected corpus": ms_df["Projected corpus"].map(lambda x: f"{sym}{x:,.0f}"),
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("#### What-if")
    w1, w2 = st.columns(2)
    with w1:
        extra = st.number_input(
            f"Extra one-time lump sum today ({sym})",
            min_value=0.0,
            value=0.0,
            step=10000.0,
            key="sip_whatif_lump",
        )
    with w2:
        bump = st.number_input(
            "Extra monthly SIP",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            key="sip_whatif_bump",
        )
    if extra > 0 or bump > 0:
        months = plan.months
        new_corpus = future_value_sip(
            plan.monthly_sip + bump,
            plan.annual_return_pct,
            months,
            lump_sum=plan.current_corpus + extra,
            step_up_annual_pct=plan.step_up_annual_pct,
        )
        st.caption(
            f"With changes: projected **{sym}{new_corpus:,.0f}** · "
            f"invested **{sym}{total_invested(plan.monthly_sip + bump, months, lump_sum=plan.current_corpus + extra, step_up_annual_pct=plan.step_up_annual_pct):,.0f}**"
        )

    with st.expander("Discipline tips", expanded=experience == "new"):
        for tip in plan.tips:
            st.markdown(f"- {tip}")


def _render_export_share(plan, market: str, inp: SipPlannerInput | None) -> None:
    sym = _currency_label(market)
    md = plan_to_markdown(plan, currency=sym)
    csv_text = plan_to_csv(plan, currency=sym)

    st.download_button(
        "Download plan (Markdown)",
        md,
        file_name=f"sip_plan_{plan.goal_name.replace(' ', '_').lower()}.md",
        mime="text/markdown",
        key="sip_dl_md",
    )
    st.download_button(
        "Download allocation (CSV)",
        csv_text,
        file_name=f"sip_plan_{plan.goal_name.replace(' ', '_').lower()}.csv",
        mime="text/csv",
        key="sip_dl_csv",
    )
    st.caption("Open the Markdown file in a browser and **Print → Save as PDF** for a PDF copy.")

    with st.expander("Preview Markdown"):
        st.markdown(md)

    if telegram_configured():
        if st.button("Send plan to Telegram", key="sip_tg_plan"):
            ok, msg = send_telegram_broadcast(
                format_sip_plan_telegram(plan, currency=sym),
                alert_type="sip",
            )
            if ok:
                st.success(msg)
            else:
                st.error(msg)
    else:
        st.caption("Subscribe to Telegram in the sidebar to send plans and monthly reminders.")

    if inp:
        st.markdown("#### Save goal & reminders")
        r1, r2, r3 = st.columns(3)
        with r1:
            reminder_day = st.number_input(
                "Reminder day of month",
                min_value=1,
                max_value=28,
                value=1,
                key="sip_reminder_day",
            )
        with r2:
            enable_rem = st.checkbox("Monthly Telegram reminder", value=False, key="sip_rem_enable")
        with r3:
            notes = st.text_input("Note (optional)", key="sip_notes", placeholder="e.g. Nifty SIP on 1st")
        if st.button("Save goal", type="primary", key="sip_save_goal"):
            saved = save_goal(
                inp,
                plan,
                currency=sym,
                reminder_day=int(reminder_day),
                reminders_enabled=enable_rem,
                notes=notes,
            )
            st.session_state["sip_saved_id"] = saved.goal_id
            st.success(f"Saved **{saved.planner_input.get('goal_name')}** — reminders on day {saved.reminder_day}.")
            if enable_rem and not telegram_configured():
                st.warning("Enable Telegram in sidebar to receive reminders.")


def _render_saved_goals(market: str) -> None:
    sym = _currency_label(market)
    goals = list_saved_goals()
    if not goals:
        st.info("No saved goals yet. Build a plan and use **Export & share → Save goal**.")
        return

    for g in goals:
        name = g.planner_input.get("goal_name", "Goal")
        with st.expander(f"{name} — {sym}{g.monthly_sip:,.0f}/mo", expanded=False):
            st.caption(f"Target {sym}{g.target_amount:,.0f} · projected {sym}{g.projected_corpus:,.0f}")
            c1, c2, c3 = st.columns(3)
            with c1:
                new_day = st.number_input(
                    "Reminder day",
                    1,
                    28,
                    value=g.reminder_day,
                    key=f"sip_rd_{g.goal_id}",
                )
            with c2:
                rem_on = st.checkbox(
                    "Reminders on",
                    value=g.reminders_enabled,
                    key=f"sip_re_{g.goal_id}",
                )
            with c3:
                if st.button("Update", key=f"sip_up_{g.goal_id}"):
                    update_reminder(g.goal_id, reminder_day=int(new_day), enabled=rem_on)
                    st.success("Updated.")
                    st.rerun()
            if st.button("Delete goal", key=f"sip_del_{g.goal_id}"):
                delete_goal(g.goal_id)
                st.rerun()

    if telegram_configured():
        if st.button("Send today's SIP reminders now", key="sip_force_reminder"):
            n, msg = run_sip_reminders(force=True)
            if n:
                st.success(msg)
            else:
                st.warning(msg)


def render_sip_goals(market: str, period: str) -> None:
    st.subheader("SIP & Goals Planner")
    st.markdown(
        "Plan **monthly SIP**, export your plan, and get **Telegram reminders** on your chosen day each month."
    )

    tab_plan, tab_saved, tab_export = st.tabs(["Plan", "Saved goals", "Export & share"])

    with tab_plan:
        inp = _render_plan_form(market)
        if inp:
            st.session_state["sip_plan"] = build_sip_plan(inp)
            st.session_state["sip_plan_input"] = inp

        plan = st.session_state.get("sip_plan")
        inp_stored = st.session_state.get("sip_plan_input")
        if not plan:
            sym = _currency_label(market)
            st.info(
                f"Example: **{sym}30 lakh** house goal in **7 years** at **12%** needs roughly "
                f"**{sym}22,000/month** SIP. Click **Build SIP plan** to customize."
            )
        else:
            st.markdown(f"### {plan.goal_name}")
            _render_plan_results(plan, market, plan.experience)

    with tab_saved:
        _render_saved_goals(market)

    with tab_export:
        plan = st.session_state.get("sip_plan")
        inp_stored = st.session_state.get("sip_plan_input")
        if plan:
            _render_export_share(plan, market, inp_stored)
        else:
            st.caption("Build a plan first on the **Plan** tab.")

    st.divider()
    st.markdown("#### Quick links")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Open Nifty ETF in Single Stock", key="sip_open_nifty"):
            ticker = "NIFTYBEES" if is_india_market(market) else "VOO"
            st.session_state["single_ticker"] = ticker
            st.session_state["nav_tab"] = "Single Stock"
            st.rerun()
    with c2:
        if st.button("Run quality screener", key="sip_open_screen"):
            st.session_state["nav_tab"] = "Screener"
            st.session_state["scr_preset"] = "Quality compounders"
            st.rerun()
