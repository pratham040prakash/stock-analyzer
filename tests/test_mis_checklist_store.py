"""Tests for persisted MIS checklist."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.mis_checklist_store import (
    is_checklist_complete,
    load_checklist_done,
    reset_checklist,
    save_checklist_item,
)


class TestMisChecklistStore(unittest.TestCase):
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mis_checklist.json"
            with patch("analyzer.mis_checklist_store.STORE_PATH", path):
                with patch("analyzer.mis_checklist_store.session_target_date", return_value="2026-07-07"):
                    save_checklist_item("night_pulse", True)
                    done = load_checklist_done("2026-07-07")
                    self.assertTrue(done.get("night_pulse"))
                    self.assertFalse(is_checklist_complete("2026-07-07"))
                    reset_checklist("2026-07-07")
                    self.assertEqual(load_checklist_done("2026-07-07"), {})


if __name__ == "__main__":
    unittest.main()
