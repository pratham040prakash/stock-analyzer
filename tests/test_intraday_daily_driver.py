"""Tests for intraday prefs, journal, and pulse source."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.intraday_journal import (
    count_trades_on_date,
    fetch_intraday_trades,
    init_intraday_journal,
    log_intraday_trade,
)
from analyzer.intraday_prefs import (
    IntradayPrefs,
    load_intraday_prefs,
    save_intraday_prefs,
    session_to_prefs,
)
from analyzer.intraday_pulse_source import load_pulse_for_watchlist


class TestIntradayPrefs(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prefs.json"
            with patch("analyzer.intraday_prefs.PREFS_PATH", path):
                save_intraday_prefs(IntradayPrefs(capital=75_000, max_trades=3))
                loaded = load_intraday_prefs()
                self.assertEqual(loaded.capital, 75_000)
                self.assertEqual(loaded.max_trades, 3)

    def test_session_to_prefs(self):
        p = session_to_prefs(50_000, 50, 1.0, 2)
        self.assertEqual(p.allocation_pct, 50)


class TestIntradayJournal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "journal.db"
        self.p1 = patch("analyzer.suggestion_journal.journal_db_path", return_value=self.db)
        self.p2 = patch("analyzer.intraday_journal.journal_db_path", return_value=self.db)
        self.p1.start()
        self.p2.start()
        init_intraday_journal()

    def tearDown(self):
        self.p1.stop()
        self.p2.stop()
        self.tmp.cleanup()

    def test_log_and_fetch(self):
        tid = log_intraday_trade(
            symbol="RELIANCE",
            action="BUY",
            entry=2500.0,
            stop_loss=2480.0,
            target=2540.0,
            trade_date="2026-07-01",
        )
        self.assertTrue(tid.startswith("it_"))
        rows = fetch_intraday_trades(trade_date="2026-07-01")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].symbol, "RELIANCE")
        self.assertEqual(count_trades_on_date("2026-07-01"), 1)


class TestIntradayPulseSource(unittest.TestCase):
    def test_missing_without_cache(self):
        with patch(
            "analyzer.intraday_pulse_source.load_pulse_cache_with_stale",
            return_value=(None, False),
        ):
            report, status = load_pulse_for_watchlist("india")
            self.assertIsNone(report)
            self.assertEqual(status, "missing")

    def test_session_report(self):
        class Fake:
            stock_map = {"RELIANCE": object()}

        fake = Fake()
        report, status = load_pulse_for_watchlist("india", session_report=fake)
        self.assertIs(report, fake)
        self.assertEqual(status, "session")


class TestChecklistLinks(unittest.TestCase):
    def test_items_have_links(self):
        from analyzer.intraday_beginner_tips import daily_mis_checklist_items

        items = daily_mis_checklist_items()
        linked = [i for i in items if i.link_tab]
        self.assertGreaterEqual(len(linked), 8)
        pulse = next(i for i in items if i.id == "night_pulse")
        self.assertEqual(pulse.link_tab, "Market Pulse")


if __name__ == "__main__":
    unittest.main()
