"""Streamlit app — Interaction Investigator (vendor-agnostic)."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from investigator.parser import merge_log_sources, parse_logs
from investigator.rca import generate_rca
from investigator.report import build_markdown_report
from investigator.timeline import Timeline, build_timeline

load_dotenv()

APP_TITLE = "Interaction Investigator"
TAGLINE = "Upload logs → unified timeline → evidence-backed RCA"

_STATUS_COLORS = {
    "healthy": "#22c55e",
    "warning": "#f59e0b",
    "failed": "#ef4444",
    "unknown": "#94a3b8",
}


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        .stage-card {
            border-left: 4px solid #6366f1;
            padding: 0.6rem 0.9rem;
            margin: 0.35rem 0;
            background: #0f172a08;
            border-radius: 0.35rem;
        }
        .hero { color: #64748b; margin-bottom: 1rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_journey(timeline: Timeline) -> None:
    st.subheader("Interaction journey")
    for stage in timeline.stages:
        color = _STATUS_COLORS.get(stage.status, "#94a3b8")
        icon = {"healthy": "✓", "warning": "!", "failed": "✗", "unknown": "·"}.get(stage.status, "·")
        st.markdown(
            f"""
            <div class="stage-card" style="border-left-color:{color}">
              <strong>{icon} {stage.label}</strong>
              &nbsp;·&nbsp; {stage.event_count} events
              &nbsp;·&nbsp; {stage.error_count} errors
            </div>
            """,
            unsafe_allow_html=True,
        )
        if stage.status in {"failed", "warning"} and stage.highlights:
            with st.expander(f"Details — {stage.label}"):
                for line in stage.highlights:
                    st.code(line, language=None)


def _render_rca(rca) -> None:
    st.subheader("Root cause analysis")
    if rca.primary_cause:
        p = rca.primary_cause
        st.error(f"**{p.label}** — {p.confidence} confidence") if p.stage in {
            "desktop",
            "recording",
            "crm",
        } else st.warning(f"**{p.label}** — {p.confidence} confidence")
        st.write(p.summary)
        if p.evidence:
            st.caption("Evidence")
            for ev in p.evidence:
                st.code(ev, language=None)

    st.markdown("**Recommended actions**")
    for action in rca.recommended_actions:
        st.markdown(f"- {action}")

    with st.expander("Customer update draft"):
        st.write(rca.customer_update_draft)


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🔍", layout="wide")
    _inject_css()

    st.title(f"🔍 {APP_TITLE}")
    st.markdown(f'<p class="hero">{TAGLINE}</p>', unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1])

    with col_left:
        interaction_id = st.text_input("Interaction / call ID", placeholder="e.g. 9876543210-abcd-...")
        symptom = st.text_area(
            "What went wrong?",
            placeholder="e.g. Agent desktop failed to load after queue answer; CRM screen pop timed out",
            height=100,
        )
        uploaded = st.file_uploader(
            "Upload log files (.log, .txt)",
            type=["log", "txt"],
            accept_multiple_files=True,
        )
        pasted = st.text_area("Or paste logs here", height=220)

        sample_path = Path(__file__).parent / "samples" / "demo_interaction.log"
        if st.button("Load demo sample"):
            st.session_state["demo_logs"] = sample_path.read_text(encoding="utf-8")
            st.rerun()

        use_ai = st.checkbox(
            "Use AI analysis (needs OPENAI_API_KEY in .env)",
            value=bool(os.getenv("OPENAI_API_KEY")),
        )

    with col_right:
        st.subheader("How it works")
        st.markdown(
            """
            1. **Upload** exported logs from any contact center platform  
            2. **Timeline** maps events to a standard journey (IVR → Queue → Agent → …)  
            3. **RCA** ranks likely root cause with evidence lines  
            4. **Export** a professional report for Jira or customer email  

            Works with **generic logs** — no vendor lock-in, no live system access required.
            """
        )
        if not os.getenv("OPENAI_API_KEY"):
            st.info("Running rule-based RCA. Add `OPENAI_API_KEY` to `.env` for AI reasoning.")

    run = st.button("Investigate", type="primary", use_container_width=True)

    log_chunks: list[str] = []
    if uploaded:
        for f in uploaded:
            log_chunks.append(f.read().decode("utf-8", errors="replace"))
    if pasted.strip():
        log_chunks.append(pasted)
    if st.session_state.get("demo_logs"):
        log_chunks.append(st.session_state["demo_logs"])

    if not run:
        return

    merged = merge_log_sources(log_chunks)
    if not merged.strip():
        st.warning("Add logs via upload, paste, or demo sample.")
        return

    with st.spinner("Correlating events and building timeline..."):
        parsed = parse_logs(merged)
        timeline = build_timeline(parsed)
        rca = generate_rca(timeline, symptom=symptom, use_ai=use_ai)
        report_md = build_markdown_report(
            interaction_id=interaction_id or ", ".join(timeline.interaction_ids) or "unknown",
            symptom=symptom,
            timeline=timeline,
            rca=rca,
        )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Log lines", timeline.total_events)
    m2.metric("Errors / warnings", timeline.total_errors)
    m3.metric("Stages with data", sum(1 for s in timeline.stages if s.event_count > 0))
    m4.metric("RCA method", rca.method.upper())

    tab_journey, tab_chrono, tab_report = st.tabs(["Journey", "Chronology", "Report"])

    with tab_journey:
        _render_journey(timeline)
        _render_rca(rca)

    with tab_chrono:
        for event in timeline.chronology[:100]:
            prefix = f"[{event.timestamp.strftime('%H:%M:%S')}] " if event.timestamp else ""
            st.text(f"L{event.line_no} {prefix}{event.message}")

    with tab_report:
        st.markdown(report_md)
        st.download_button(
            "Download RCA report (.md)",
            data=report_md,
            file_name=f"rca-{interaction_id or 'interaction'}.md",
            mime="text/markdown",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
