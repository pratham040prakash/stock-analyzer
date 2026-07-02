"""Tests for in-app Telegram subscription."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from analyzer.telegram_subscriptions import (
    create_subscribe_token,
    get_or_create_subscribe_token,
    get_subscriber_by_token,
    list_active_subscribers,
    process_bot_updates,
    subscribe_deep_link,
)


class TestTelegramSubscriptions(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "subscribers.db"
        self.state = Path(self.tmp.name) / "bot_state.json"
        self.patcher_db = patch(
            "analyzer.telegram_subscriptions.db_path",
            return_value=self.db,
        )
        self.patcher_state = patch(
            "analyzer.telegram_subscriptions.bot_state_path",
            return_value=self.state,
        )
        self.patcher_token = patch(
            "analyzer.telegram_subscriptions.bot_token",
            return_value="test-token",
        )
        self.patcher_db.start()
        self.patcher_state.start()
        self.patcher_token.start()

    def tearDown(self) -> None:
        self.patcher_token.stop()
        self.patcher_state.stop()
        self.patcher_db.stop()
        self.tmp.cleanup()

    def test_create_token_and_deep_link(self) -> None:
        token = get_or_create_subscribe_token(force_new=True)
        self.assertTrue(token.startswith("sa_"))
        self.assertIn(token, subscribe_deep_link(token, "MyStockBot"))

    @patch("analyzer.telegram_subscriptions.ensure_webhook_cleared", return_value=(True, "OK"))
    @patch("analyzer.telegram_subscriptions.requests.post")
    @patch("analyzer.telegram_subscriptions.requests.get")
    def test_process_start_subscribes(self, mock_get, mock_post, _mock_wh) -> None:
        token = get_or_create_subscribe_token(force_new=True)
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "ok": True,
                "result": [
                    {
                        "update_id": 100,
                        "message": {
                            "text": f"/start {token}",
                            "chat": {"id": 12345, "username": "trader", "first_name": "T"},
                        },
                    }
                ]
            },
        )
        mock_post.return_value = MagicMock(status_code=200)

        n = process_bot_updates()
        self.assertEqual(n, 1)
        sub = get_subscriber_by_token(token)
        self.assertIsNotNone(sub)
        assert sub is not None
        self.assertEqual(sub.chat_id, "12345")
        self.assertEqual(sub.username, "trader")
        self.assertIn(sub, list_active_subscribers("morning"))

    def test_list_includes_legacy_env_chat(self) -> None:
        with patch.dict("os.environ", {"TELEGRAM_CHAT_ID": "999"}):
            subs = list_active_subscribers()
        self.assertTrue(any(s.chat_id == "999" for s in subs))


if __name__ == "__main__":
    unittest.main()
