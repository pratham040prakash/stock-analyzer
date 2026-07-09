"""Tests for MIS trade journal store."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.trade_journal import (
    delete_journal_entry,
    load_journal_entries,
    save_journal_entry,
)


class TestTradeJournal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Path(self.tmp.name) / "trade_journal.json"
        self.p_path = patch("analyzer.trade_journal.STORE_PATH", self.store)
        self.p_path.start()
        self.p_date = patch(
            "analyzer.trade_journal.session_target_date",
            return_value="2026-07-09",
        )
        self.p_date.start()

    def tearDown(self):
        self.p_date.stop()
        self.p_path.stop()
        self.tmp.cleanup()

    def test_save_and_load(self):
        entry = save_journal_entry(
            symbol="BANKNIFTY PE 55000",
            leg="options",
            entry=248.0,
            exit=190.0,
            pnl_inr=-1740.0,
            mistake="Entered before OR confirm",
            fix="Wait for OR low on PE",
        )
        self.assertEqual(entry.symbol, "BANKNIFTY PE 55000")
        rows = load_journal_entries()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].pnl_inr, -1740.0)
        self.assertIn("OR", rows[0].mistake)

    def test_delete_entry(self):
        save_journal_entry(symbol="TEST", mistake="x", fix="y")
        rows = load_journal_entries()
        ok = delete_journal_entry(rows[0].trade_date, rows[0].symbol, rows[0].saved_at)
        self.assertTrue(ok)
        self.assertEqual(load_journal_entries(), [])


if __name__ == "__main__":
    unittest.main()
