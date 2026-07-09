"""Autopilot — schedule install status and today's loop progress."""

from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path

from analyzer.market_session import market_session_status
from analyzer.mis_eod_summary import mis_eod_trade_date, was_eod_summary_sent
from analyzer.morning_suggestions_scheduler import (
    morning_suggestions_meta,
    was_morning_suggestions_sent,
)
from analyzer.morning_options_rescan import was_morning_options_rescan_sent
from analyzer.nightly_prep_scheduler import prep_session_key, was_nightly_prep_sent
from analyzer.post_close_scan_scheduler import post_close_scan_meta, was_post_close_scan_sent
from analyzer.prep_morning_nag import was_prep_nag_sent
from analyzer.prep_status import is_nightly_prep_complete, prep_status_for
from analyzer.trade_selection import load_selected_symbols
from analyzer.trade_selection_scheduler import was_auto_select_run
from analyzer.watchlist_history import (
    fetch_outcomes_for_date,
    fetch_snapshots_for_date,
    session_target_date,
)

ROOT = Path(__file__).resolve().parent.parent
LAUNCH_AGENTS = Path.home() / "Library" / "LaunchAgents"

AUTOPILOT_JOBS: list[tuple[str, str, str]] = [
    ("post_close_scan", "com.stockanalyzer.postclosescan.plist", "3:45 PM — Quick scan"),
    ("eod_score", "com.stockanalyzer.miseod.plist", "3:50 PM — score + hit summary"),
    ("autopilot_health", "com.stockanalyzer.autopilothealth.plist", "4:30 PM — gap alert"),
    ("prep_morning_nag", "com.stockanalyzer.prepmorning.plist", "8:45 AM — prep nag"),
    ("morning_list", "com.stockanalyzer.morning.plist", "8:50 AM — pick list"),
    ("session_open", "com.stockanalyzer.sessionreminders.plist", "9:15 AM — session open"),
    ("morning_options", "com.stockanalyzer.morning_options.plist", "9:46 AM — options re-scan"),
    ("live_alerts", "com.stockanalyzer.livealerts.plist", "Every 5 min — live alerts"),
    ("auto_star_2", "com.stockanalyzer.autoselect.plist", "9:10 PM — auto star top 2"),
    ("nightly_prep", "com.stockanalyzer.nightlyprep.plist", "9:00 PM — options prep"),
]


@dataclass
class AutopilotStep:
    key: str
    label: str
    schedule: str
    installed: bool
    done_today: bool
    detail: str


@dataclass
class AutopilotStatus:
    trade_date: str
    prep_for: str
    is_macos: bool
    schedules_installed: int
    schedules_total: int
    steps: list[AutopilotStep]
    timezone_hint: str


def is_macos() -> bool:
    return platform.system() == "Darwin"


def launchd_plist_installed(plist_name: str) -> bool:
    return (LAUNCH_AGENTS / plist_name).is_file()


def count_installed_schedules() -> tuple[int, int]:
    total = len(AUTOPILOT_JOBS)
    installed = sum(1 for _, plist, _ in AUTOPILOT_JOBS if launchd_plist_installed(plist))
    return installed, total


def build_autopilot_status() -> AutopilotStatus:
    trade_date = session_target_date()
    prep_for = prep_session_key()
    prep = prep_status_for(prep_for)
    eod_date = mis_eod_trade_date() or trade_date

    post_meta = post_close_scan_meta(prep_for)
    morning_meta = morning_suggestions_meta(trade_date)
    selected = load_selected_symbols(trade_date)
    eod_outcomes = fetch_outcomes_for_date(eod_date)
    eod_scored = sum(1 for o in eod_outcomes if o.outcome not in ("no_data",))
    has_snapshots = bool(fetch_snapshots_for_date(prep_for))

    steps = [
        AutopilotStep(
            key="post_close_scan",
            label="Quick scan (top 5)",
            schedule="3:45 PM",
            installed=launchd_plist_installed("com.stockanalyzer.postclosescan.plist"),
            done_today=was_post_close_scan_sent(prep_for) or prep.get("equity") or has_snapshots,
            detail=post_meta.get("at", "") or (
                f"{len(fetch_snapshots_for_date(prep_for))} picks saved"
                if has_snapshots
                else "Waiting for after-close scan"
            ),
        ),
        AutopilotStep(
            key="auto_star_2",
            label="Star 2 picks",
            schedule="9:10 PM",
            installed=launchd_plist_installed("com.stockanalyzer.autoselect.plist"),
            done_today=bool(selected) or was_auto_select_run(prep_for),
            detail=", ".join(selected) if selected else "Star manually or wait for auto top 2",
        ),
        AutopilotStep(
            key="morning_list",
            label="Morning Telegram",
            schedule="8:50 AM",
            installed=launchd_plist_installed("com.stockanalyzer.morning.plist"),
            done_today=was_morning_suggestions_sent(trade_date),
            detail=morning_meta.get("at", "Not sent yet"),
        ),
        AutopilotStep(
            key="eod_score",
            label="EOD hit summary",
            schedule="3:50 PM",
            installed=launchd_plist_installed("com.stockanalyzer.miseod.plist"),
            done_today=was_eod_summary_sent(eod_date) or eod_scored > 0,
            detail=(
                f"{eod_scored} picks scored"
                if eod_scored
                else "Scores after 3:30 PM IST"
            ),
        ),
        AutopilotStep(
            key="nightly_prep",
            label="Nightly options prep",
            schedule="9:00 PM",
            installed=launchd_plist_installed("com.stockanalyzer.nightlyprep.plist"),
            done_today=was_nightly_prep_sent(prep_for) or prep.get("options"),
            detail="Optional CE/PE" if not prep.get("options") else "Options saved",
        ),
        AutopilotStep(
            key="prep_morning_nag",
            label="Prep incomplete nag",
            schedule="8:45 AM",
            installed=launchd_plist_installed("com.stockanalyzer.prepmorning.plist"),
            done_today=was_prep_nag_sent(trade_date) or is_nightly_prep_complete(prep),
            detail="Telegram if prep missing",
        ),
        AutopilotStep(
            key="morning_options",
            label="Options re-scan (post-OR)",
            schedule="9:46 AM",
            installed=launchd_plist_installed("com.stockanalyzer.morning_options.plist"),
            done_today=was_morning_options_rescan_sent(trade_date) or prep.get("options"),
            detail="Fresh CE/PE after opening range",
        ),
        AutopilotStep(
            key="live_alerts",
            label="Live watchlist alerts",
            schedule="Every 5 min",
            installed=launchd_plist_installed("com.stockanalyzer.livealerts.plist"),
            done_today=launchd_plist_installed("com.stockanalyzer.livealerts.plist"),
            detail="Stop / T1 / reversal Telegram during session",
        ),
    ]

    installed, total = count_installed_schedules()
    session = market_session_status()
    tz_hint = (
        "Set Mac timezone to **Asia/Kolkata** so launchd times match IST."
        if is_macos()
        else "Autopilot schedules run on your Mac only — cloud is view-only."
    )

    return AutopilotStatus(
        trade_date=trade_date,
        prep_for=prep_for,
        is_macos=is_macos(),
        schedules_installed=installed,
        schedules_total=total,
        steps=steps,
        timezone_hint=tz_hint,
    )


def install_autopilot_schedules() -> tuple[bool, str]:
    """Run install_all_schedules.sh on macOS."""
    if not is_macos():
        return False, "Autopilot install requires macOS (launchd)."

    script = ROOT / "scripts" / "install_all_schedules.sh"
    if not script.is_file():
        return False, f"Missing installer: {script}"

    try:
        proc = subprocess.run(
            ["bash", str(script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, "Install timed out after 120s"
    except OSError as exc:
        return False, str(exc)

    output = (proc.stdout or "") + (proc.stderr or "")
    tail = "\n".join(line for line in output.strip().splitlines()[-6:])
    if proc.returncode == 0:
        return True, tail or "All schedules installed."
    return False, tail or f"Install failed (exit {proc.returncode})"
