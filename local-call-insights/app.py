"""Local Call Insights — simple CSV call report for Indian SMB / BPO teams."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Flexible column aliases (Exotel, Ozonetel, Knowlarity, manual Excel exports)
COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "agent": ("agent", "agent_name", "executive", "user", "extension"),
    "status": ("status", "disposition", "call_status", "final_status"),
    "reason": ("hangup_reason", "reason", "disconnect_reason", "failure_reason", "cause"),
    "duration": ("duration_sec", "duration", "talk_time", "bill_sec", "call_duration"),
    "phone": ("customer_phone", "phone", "caller", "mobile", "customer_number"),
    "date": ("date", "call_date", "day"),
    "time": ("time", "call_time", "start_time"),
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping: dict[str, str] = {}
    lower_cols = {c.lower().strip(): c for c in df.columns}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_cols:
                mapping[lower_cols[alias]] = canonical
                break
    out = df.rename(columns=mapping).copy()
    if "duration" in out.columns:
        out["duration"] = pd.to_numeric(out["duration"], errors="coerce").fillna(0)
    else:
        out["duration"] = 0
    if "status" not in out.columns:
        out["status"] = "unknown"
    out["status"] = out["status"].astype(str).str.lower().str.strip()
    if "reason" not in out.columns:
        out["reason"] = out["status"]
    out["reason"] = out["reason"].astype(str).str.lower().str.strip()
    if "agent" not in out.columns:
        out["agent"] = "Unassigned"
    out["agent"] = out["agent"].astype(str).str.strip()
    return out


def _is_success(status: str) -> bool:
    return status in {"answered", "connected", "completed", "success", "ok"}


def _is_missed(status: str) -> bool:
    return status in {"missed", "no_answer", "no answer", "abandoned", "busy"}


def _is_failed(status: str) -> bool:
    return status in {"failed", "fail", "error", "dropped", "drop"}


def analyze(df: pd.DataFrame) -> dict:
    total = len(df)
    answered = int(df["status"].apply(_is_success).sum())
    missed = int(df["status"].apply(_is_missed).sum())
    failed = int(df["status"].apply(_is_failed).sum())
    avg_dur = int(df.loc[df["duration"] > 0, "duration"].mean() or 0)

    reason_counts = (
        df.loc[df["status"].apply(lambda s: _is_failed(s) or _is_missed(s)), "reason"]
        .value_counts()
        .head(5)
    )
    agent_stats = (
        df.groupby("agent", dropna=False)
        .agg(calls=("agent", "count"), answered=("status", lambda s: s.apply(_is_success).sum()))
        .assign(answer_rate=lambda x: (x["answered"] / x["calls"] * 100).round(1))
        .sort_values("calls", ascending=False)
    )

    problems = []
    if total and answered / total < 0.6:
        problems.append("Answer rate below 60% — check agent availability and dialer timing.")
    if "network_error" in reason_counts.index or "call_drop" in reason_counts.index:
        problems.append("Network drops detected — ask telecom/dialer provider to check trunk quality.")
    if missed > failed and missed > total * 0.2:
        problems.append("High missed-call volume — increase agents or fix retry rules.")
    if not problems:
        problems.append("No major red flags. Focus on agent coaching for low answer-rate rows.")

    return {
        "total": total,
        "answered": answered,
        "missed": missed,
        "failed": failed,
        "avg_duration": avg_dur,
        "answer_rate": round(answered / total * 100, 1) if total else 0,
        "reason_counts": reason_counts,
        "agent_stats": agent_stats,
        "problems": problems,
    }


def whatsapp_summary(stats: dict, business: str) -> str:
    lines = [
        f"📞 *{business} — Daily Call Report*",
        f"📅 {datetime.now().strftime('%d %b %Y')}",
        "",
        f"Total calls: *{stats['total']}*",
        f"Answered: *{stats['answered']}* ({stats['answer_rate']}%)",
        f"Missed: *{stats['missed']}*",
        f"Failed: *{stats['failed']}*",
        f"Avg talk time: *{stats['avg_duration']} sec*",
        "",
        "*Top issues:*",
    ]
    if stats["reason_counts"].empty:
        lines.append("- None")
    else:
        for reason, count in stats["reason_counts"].items():
            lines.append(f"- {reason}: {count}")
    lines.extend(["", "*Action:*", f"- {stats['problems'][0]}"])
    return "\n".join(lines)


def main() -> None:
    st.set_page_config(page_title="Local Call Insights", page_icon="📞", layout="centered")
    st.title("📞 Local Call Insights")
    st.caption("CSV upload → instant report → WhatsApp summary. For small teams & local BPOs.")

    business = st.text_input("Business name", value="My Call Center")
    uploaded = st.file_uploader("Upload call CSV", type=["csv"])
    use_sample = st.button("Use sample data")

    raw_df: pd.DataFrame | None = None
    if uploaded:
        raw_df = pd.read_csv(uploaded)
    elif use_sample:
        sample = Path(__file__).parent / "samples" / "sample_calls.csv"
        raw_df = pd.read_csv(sample)

    if raw_df is None:
        st.info("Export CSV from your dialer (Exotel, Ozonetel, Knowlarity, Excel) and upload here.")
        st.markdown(
            """
            **Minimum columns (any names):**
            - Agent name
            - Call status (answered / missed / failed)
            - Duration (seconds)
            - Hangup reason (optional)
            """
        )
        return

    df = _normalize_columns(raw_df)
    stats = analyze(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", stats["total"])
    c2.metric("Answered", f"{stats['answered']} ({stats['answer_rate']}%)")
    c3.metric("Missed", stats["missed"])
    c4.metric("Failed", stats["failed"])

    st.subheader("What needs attention")
    for p in stats["problems"]:
        st.warning(p)

    st.subheader("Top failure reasons")
    if stats["reason_counts"].empty:
        st.success("No failures in this file.")
    else:
        st.bar_chart(stats["reason_counts"])

    st.subheader("Agent summary")
    st.dataframe(stats["agent_stats"], use_container_width=True)

    summary = whatsapp_summary(stats, business)
    st.subheader("WhatsApp summary (copy & send)")
    st.text_area("Copy this", value=summary, height=260)

    st.download_button(
        "Download summary (.txt)",
        data=summary,
        file_name=f"call-report-{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain",
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
