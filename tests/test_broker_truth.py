"""Tests for Broker Truth subsystem (Migration Step 1)."""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from analyzer.broker_truth.learning import (
    LearningOutcomeSource,
    normalize_outcome_from_pnl,
    resolve_learning_outcomes,
)
from analyzer.broker_truth.models import BrokerTradeFill, PlannedTrade, TradeRecord
from analyzer.broker_truth.planned import load_planned_trades
from analyzer.broker_truth.reconciliation import ReconciliationService
from analyzer.broker_truth.service import BrokerTruthService
from analyzer.broker_truth.store import (
    fetch_trade_records,
    init_broker_truth_store,
    replace_trade_records_for_date,
    upsert_fills,
    upsert_trade_records,
)


class TestNormalizeOutcome(unittest.TestCase):
    def test_profit_is_win(self):
        self.assertEqual(normalize_outcome_from_pnl(150.0), "target_hit")

    def test_loss_is_stop(self):
        self.assertEqual(normalize_outcome_from_pnl(-80.0), "stop_hit")

    def test_flat_band(self):
        self.assertEqual(normalize_outcome_from_pnl(0.5), "flat")


class TestBrokerTruthService(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "broker_truth.db"
        self.bp = patch(
            "analyzer.broker_truth.store.broker_truth_db_path",
            return_value=self.db,
        )
        self.bp.start()
        init_broker_truth_store()

    def tearDown(self):
        self.bp.stop()
        self.tmp.cleanup()

    def test_build_trade_records_long_round_trip(self):
        trade_date = "2026-07-15"
        upsert_fills([
            BrokerTradeFill(
                trade_id="t1",
                order_id="o1",
                exchange="NSE",
                tradingsymbol="RELIANCE-EQ",
                product="MIS",
                transaction_type="BUY",
                quantity=10,
                average_price=100.0,
                fill_timestamp="2026-07-15 10:00:00",
                trade_date=trade_date,
            ),
            BrokerTradeFill(
                trade_id="t2",
                order_id="o2",
                exchange="NSE",
                tradingsymbol="RELIANCE-EQ",
                product="MIS",
                transaction_type="SELL",
                quantity=10,
                average_price=110.0,
                fill_timestamp="2026-07-15 14:00:00",
                trade_date=trade_date,
            ),
        ])
        svc = BrokerTruthService(kite=None)
        records = svc.build_trade_records(trade_date)
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec.symbol, "RELIANCE")
        self.assertEqual(rec.quantity, 10)
        self.assertEqual(rec.realized_pnl, 100.0)
        self.assertEqual(rec.execution_status, "COMPLETE")
        upsert_trade_records(records)
        stored = fetch_trade_records(trade_date=trade_date)
        self.assertEqual(len(stored), 1)

    def test_sync_skips_invalid_fills(self):
        kite = MagicMock()
        kite.orders.return_value = []
        kite.trades.return_value = [
            {"trade_id": "", "order_id": "1", "exchange": "NSE", "tradingsymbol": "SBIN-EQ",
             "product": "MIS", "transaction_type": "BUY", "quantity": 5, "average_price": 800.0,
             "fill_timestamp": "2026-07-15 09:30:00"},
        ]
        kite.positions.return_value = {"net": [], "day": []}
        kite.holdings.return_value = []
        result = BrokerTruthService(kite=kite).sync_session("2026-07-15")
        self.assertEqual(result.fills_imported, 0)
        self.assertEqual(result.records_built, 0)

    def test_replace_records_on_resync(self):
        trade_date = "2026-07-15"
        upsert_fills([
            BrokerTradeFill(
                trade_id="t1", order_id="o1", exchange="NSE", tradingsymbol="TCS-EQ",
                product="MIS", transaction_type="BUY", quantity=10, average_price=100.0,
                fill_timestamp="2026-07-15 10:00:00", trade_date=trade_date,
            ),
            BrokerTradeFill(
                trade_id="t2", order_id="o2", exchange="NSE", tradingsymbol="TCS-EQ",
                product="MIS", transaction_type="SELL", quantity=10, average_price=105.0,
                fill_timestamp="2026-07-15 14:00:00", trade_date=trade_date,
            ),
        ])
        svc = BrokerTruthService(kite=None)
        first = svc.build_trade_records(trade_date)
        replace_trade_records_for_date(trade_date, first)
        upsert_fills([
            BrokerTradeFill(
                trade_id="t3", order_id="o3", exchange="NSE", tradingsymbol="TCS-EQ",
                product="MIS", transaction_type="BUY", quantity=5, average_price=100.0,
                fill_timestamp="2026-07-15 11:00:00", trade_date=trade_date,
            ),
            BrokerTradeFill(
                trade_id="t4", order_id="o4", exchange="NSE", tradingsymbol="TCS-EQ",
                product="MIS", transaction_type="SELL", quantity=5, average_price=108.0,
                fill_timestamp="2026-07-15 15:00:00", trade_date=trade_date,
            ),
        ])
        second = svc.build_trade_records(trade_date)
        replace_trade_records_for_date(trade_date, second)
        stored = fetch_trade_records(trade_date=trade_date)
        self.assertEqual(len(stored), 2)

    def test_sync_session_from_mock_kite(self):
        kite = MagicMock()
        kite.orders.return_value = [{
            "order_id": "1",
            "exchange": "NSE",
            "tradingsymbol": "SBIN-EQ",
            "product": "MIS",
            "transaction_type": "BUY",
            "quantity": 5,
            "filled_quantity": 5,
            "average_price": 800.0,
            "status": "COMPLETE",
            "order_timestamp": "2026-07-15 09:30:00",
            "exchange_timestamp": "2026-07-15 09:30:00",
            "tag": "",
        }]
        kite.trades.return_value = [
            {
                "trade_id": "tr1",
                "order_id": "1",
                "exchange": "NSE",
                "tradingsymbol": "SBIN-EQ",
                "product": "MIS",
                "transaction_type": "BUY",
                "quantity": 5,
                "average_price": 800.0,
                "fill_timestamp": "2026-07-15 09:30:00",
            },
            {
                "trade_id": "tr2",
                "order_id": "2",
                "exchange": "NSE",
                "tradingsymbol": "SBIN-EQ",
                "product": "MIS",
                "transaction_type": "SELL",
                "quantity": 5,
                "average_price": 810.0,
                "fill_timestamp": "2026-07-15 15:00:00",
            },
        ]
        kite.positions.return_value = {"net": [], "day": []}
        kite.holdings.return_value = []

        svc = BrokerTruthService(kite=kite)
        result = svc.sync_session("2026-07-15")
        self.assertTrue(result.connected)
        self.assertEqual(result.fills_imported, 2)
        self.assertEqual(result.records_built, 1)
        trades = fetch_trade_records(trade_date="2026-07-15", symbol="SBIN")
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].realized_pnl, 50.0)


class TestReconciliation(unittest.TestCase):
    def test_missed_entry(self):
        planned = PlannedTrade(
            planned_id="plan:2026-07-15:AXISBANK",
            symbol="AXISBANK",
            exchange="NSE",
            strategy="MIS",
            trade_date="2026-07-15",
            planned_entry=100.0,
            planned_stop=95.0,
            planned_target=110.0,
            planned_quantity=None,
            side="LONG",
            source="test",
            created_at="now",
        )
        svc = ReconciliationService()
        result = svc.reconcile_one(planned, None)
        self.assertFalse(result.matched)
        self.assertTrue(result.missed_entry)
        self.assertEqual(result.execution_quality, "missed")

    def test_best_match_by_entry_proximity(self):
        planned = PlannedTrade(
            planned_id="plan:2026-07-15:AXISBANK",
            symbol="AXISBANK",
            exchange="NSE",
            strategy="MIS",
            trade_date="2026-07-15",
            planned_entry=100.0,
            planned_stop=95.0,
            planned_target=110.0,
            planned_quantity=None,
            side="LONG",
            source="test",
            created_at="now",
        )
        far = TradeRecord(
            trade_id="far", symbol="AXISBANK", exchange="NSE", strategy="MIS",
            entry_time="t1", exit_time="t2", entry_price=120.0, exit_price=115.0,
            quantity=10, broker_charges=0, realized_pnl=-50.0, holding_period_minutes=60,
            order_ids=["o1"], execution_status="COMPLETE", tags=[], notes="",
            product="MIS", side="LONG", trade_date="2026-07-15", planned_id=None,
            source="kite_api", synced_at="now",
        )
        near = TradeRecord(
            trade_id="near", symbol="AXISBANK", exchange="NSE", strategy="MIS",
            entry_time="t1", exit_time="t2", entry_price=101.0, exit_price=108.0,
            quantity=10, broker_charges=0, realized_pnl=70.0, holding_period_minutes=60,
            order_ids=["o2"], execution_status="COMPLETE", tags=[], notes="",
            product="MIS", side="LONG", trade_date="2026-07-15", planned_id=None,
            source="kite_api", synced_at="now",
        )
        from analyzer.broker_truth.reconciliation import _best_match

        match = _best_match(planned, [far, near], set())
        self.assertEqual(match.trade_id, "near")

    def test_slippage_on_match(self):
        planned = PlannedTrade(
            planned_id="plan:2026-07-15:AXISBANK",
            symbol="AXISBANK",
            exchange="NSE",
            strategy="MIS",
            trade_date="2026-07-15",
            planned_entry=100.0,
            planned_stop=95.0,
            planned_target=110.0,
            planned_quantity=None,
            side="LONG",
            source="test",
            created_at="now",
        )
        executed = TradeRecord(
            trade_id="x",
            symbol="AXISBANK",
            exchange="NSE",
            strategy="MIS",
            entry_time="t1",
            exit_time="t2",
            entry_price=101.0,
            exit_price=108.0,
            quantity=10,
            broker_charges=0,
            realized_pnl=70.0,
            holding_period_minutes=60,
            order_ids=["o1", "o2"],
            execution_status="COMPLETE",
            tags=[],
            notes="",
            product="MIS",
            side="LONG",
            trade_date="2026-07-15",
            planned_id=None,
            source="kite_api",
            synced_at="now",
        )
        result = ReconciliationService().reconcile_one(planned, executed)
        self.assertTrue(result.matched)
        self.assertEqual(result.slippage_entry, 1.0)
        self.assertEqual(result.realized_pnl, 70.0)


class TestLearningAdapter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.journal_db = Path(self.tmp.name) / "journal.db"
        self.broker_db = Path(self.tmp.name) / "broker_truth.db"
        self.jp = patch(
            "analyzer.suggestion_journal.journal_db_path",
            return_value=self.journal_db,
        )
        self.jh = patch(
            "analyzer.watchlist_history.journal_db_path",
            return_value=self.journal_db,
        )
        self.jl = patch(
            "analyzer.broker_truth.learning.journal_db_path",
            return_value=self.journal_db,
        )
        self.je = patch(
            "analyzer.watchlist_eod.journal_db_path",
            return_value=self.journal_db,
        )
        self.bp = patch(
            "analyzer.broker_truth.store.broker_truth_db_path",
            return_value=self.broker_db,
        )
        for p in (self.jp, self.jh, self.je, self.jl, self.bp):
            p.start()
        self._seed_coach_outcomes()
        self._seed_broker_record()

    def tearDown(self):
        for p in (self.bp, self.jl, self.jh, self.je, self.jp):
            p.stop()
        self.tmp.cleanup()

    def _seed_coach_outcomes(self):
        from analyzer.watchlist_eod import init_watchlist_outcomes
        from analyzer.watchlist_history import init_watchlist_history

        init_watchlist_outcomes()
        init_watchlist_history()
        with sqlite3.connect(self.journal_db) as conn:
            conn.execute(
                """
                INSERT INTO watchlist_outcomes (
                    id, trade_date, symbol, entry, stop_loss, target,
                    session_high, session_low, session_close, outcome, note, scored_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "wo1", "2026-07-15", "RELIANCE", 100, 95, 110,
                    112, 99, 108, "target_hit", "coach", "now",
                ),
            )
            conn.execute(
                """
                INSERT INTO watchlist_daily_snapshots (
                    id, trade_date, prep_date, symbol, rank, entry, stop_loss,
                    target, prep_score, market_bias, saved_at,
                    checklist_passed, atr_pct, rsi, volume_ratio,
                    sector_tailwind, macd_bullish
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "s1", "2026-07-15", "2026-07-14", "RELIANCE", 1,
                    100, 95, 110, 55, "BULLISH", "now",
                    4, 2.0, 58, 1.2, 1, 1,
                ),
            )

    def _seed_broker_record(self):
        init_broker_truth_store()
        upsert_trade_records([
            TradeRecord(
                trade_id="2026-07-15:RELIANCE:MIS:LONG:1",
                symbol="RELIANCE",
                exchange="NSE",
                strategy="MIS",
                entry_time="2026-07-15 10:00:00",
                exit_time="2026-07-15 15:00:00",
                entry_price=100.0,
                exit_price=99.0,
                quantity=10,
                broker_charges=0,
                realized_pnl=-10.0,
                holding_period_minutes=300,
                order_ids=["o1", "o2"],
                execution_status="COMPLETE",
                tags=["MIS"],
                notes="",
                product="MIS",
                side="LONG",
                trade_date="2026-07-15",
                planned_id=None,
                source="kite_api",
                synced_at="now",
            ),
        ])

    def test_broker_overrides_coach_outcome(self):
        rows = resolve_learning_outcomes(days=14)
        rel = [r for r in rows if r.symbol == "RELIANCE"][0]
        self.assertEqual(rel.source, LearningOutcomeSource.BROKER)
        self.assertEqual(rel.outcome, "stop_hit")
        self.assertEqual(rel.realized_pnl, -10.0)

    def test_fetch_pick_features_uses_broker(self):
        from analyzer.watchlist_learning import fetch_pick_features

        features = fetch_pick_features(days=14)
        rel = [f for f in features if f.symbol == "RELIANCE"][0]
        self.assertEqual(rel.outcome, "stop_hit")

    def test_broker_only_date_included(self):
        upsert_trade_records([
            TradeRecord(
                trade_id="2026-07-14:INFY:MIS:LONG:1",
                symbol="INFY",
                exchange="NSE",
                strategy="MIS",
                entry_time="2026-07-14 10:00:00",
                exit_time="2026-07-14 15:00:00",
                entry_price=1500.0,
                exit_price=1510.0,
                quantity=5,
                broker_charges=0,
                realized_pnl=50.0,
                holding_period_minutes=300,
                order_ids=["o1", "o2"],
                execution_status="COMPLETE",
                tags=["MIS"],
                notes="",
                product="MIS",
                side="LONG",
                trade_date="2026-07-14",
                planned_id=None,
                source="kite_api",
                synced_at="now",
            ),
        ])
        rows = resolve_learning_outcomes(days=14)
        infy = [r for r in rows if r.symbol == "INFY"]
        self.assertEqual(len(infy), 1)
        self.assertEqual(infy[0].source, LearningOutcomeSource.BROKER)


class TestPlannedTrades(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.journal_db = Path(self.tmp.name) / "journal.db"
        self.jp = patch(
            "analyzer.suggestion_journal.journal_db_path",
            return_value=self.journal_db,
        )
        self.jh = patch(
            "analyzer.watchlist_history.journal_db_path",
            return_value=self.journal_db,
        )
        self.je = patch(
            "analyzer.watchlist_eod.journal_db_path",
            return_value=self.journal_db,
        )
        self.jplanned = patch(
            "analyzer.broker_truth.planned.journal_db_path",
            return_value=self.journal_db,
        )
        for p in (self.jp, self.jh, self.je, self.jplanned):
            p.start()

    def tearDown(self):
        for p in (self.jplanned, self.je, self.jh, self.jp):
            p.stop()
        self.tmp.cleanup()

    def test_load_from_snapshots(self):
        from analyzer.watchlist_eod import init_watchlist_outcomes
        from analyzer.watchlist_history import init_watchlist_history

        init_watchlist_outcomes()
        init_watchlist_history()
        with sqlite3.connect(self.journal_db) as conn:
            conn.execute(
                """
                INSERT INTO watchlist_daily_snapshots (
                    id, trade_date, prep_date, symbol, rank, entry, stop_loss,
                    target, prep_score, market_bias, saved_at,
                    checklist_passed, atr_pct, rsi, volume_ratio,
                    sector_tailwind, macd_bullish, side
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "s1", "2026-07-16", "2026-07-15", "TCS", 1,
                    4000, 3950, 4100, 60, "BULLISH", "now",
                    4, 1.5, 55, 1.0, 0, 1, "LONG",
                ),
            )
        with patch("analyzer.broker_truth.planned.load_pinned_plans", return_value=[]):
            plans = load_planned_trades("2026-07-16")
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0].symbol, "TCS")
        self.assertEqual(plans[0].planned_entry, 4000.0)
        self.assertEqual(plans[0].planned_id, "plan:2026-07-16:TCS")


if __name__ == "__main__":
    unittest.main()
