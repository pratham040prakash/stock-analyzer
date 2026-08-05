"""APEX-012 Phase 0 — Single Truth architecture guardrails.

Each test proves one architectural invariant. Failures explain which rule was violated.
"""

from __future__ import annotations

import ast
import inspect
import unittest
from pathlib import Path
from types import MappingProxyType
from unittest.mock import MagicMock, patch

from analyzer.architecture.legacy_lifecycle import (
    LEGACY_MODULE_REGISTRY,
    LIFECYCLE_MARKER_PREFIX,
    OPPORTUNITY_RANKING_FUNCTION_NAMES,
    TIER_A_DECISION_PROJECTION,
    TIER_A_IMPORT_BASELINE,
    TIER_B_REFLECTIVE_PROJECTION,
    UI_FORBIDDEN_DECISION_ENGINE_CALLS,
    UI_FORBIDDEN_DECISION_ENGINE_IMPORTS,
    UI_MIS_BUILD_ALLOWLIST,
    LegacyLifecycle,
)
from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict, UncertaintyVector
from analyzer.investment_os import InvestmentOS
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.use_cases.morning_brief import domain_from_cache_bundle, view_model_from_domain
from analyzer.use_cases.morning_brief_assembly import assemble_morning_brief_view_model
from analyzer.use_cases.morning_brief_helpers import MorningBriefScenario
from analyzer.use_cases.morning_brief_models import MorningBriefViewModel
from analyzer.watchlist_pins import PinnedPlan
from ui.broker.state import BrokerSnapshot
from ui.components.answer_canvas import build_ask_answer
from ui.components.decision_card import project_decision_card
from ui.components.morning_brief_ui import load_brief_from_cache, verdict_state_from_brief
from ui.components.plan_canvas import build_trade_plan_view
from ui.components.proof_mapper import build_structure_proof

REPO_ROOT = Path(__file__).resolve().parent.parent
UI_ROOT = REPO_ROOT / "ui"


def _registry_file_paths() -> list[str]:
    return [k for k in LEGACY_MODULE_REGISTRY if k.endswith(".py") and ":" not in k]


class TestLegacyLifecycleRegistry(unittest.TestCase):
    """Invariant: every registered legacy module declares APEX-012-LIFECYCLE marker."""

    def test_registry_modules_contain_lifecycle_marker(self):
        missing: list[str] = []
        for rel_path in _registry_file_paths():
            full = REPO_ROOT / rel_path
            if not full.is_file():
                missing.append(f"{rel_path} (file not found)")
                continue
            record = LEGACY_MODULE_REGISTRY[rel_path]
            expected = f"{LIFECYCLE_MARKER_PREFIX} {record['lifecycle'].value}"
            text = full.read_text(encoding="utf-8")
            if expected not in text:
                missing.append(f"{rel_path} missing marker {expected!r}")
        self.assertEqual(
            missing,
            [],
            "APEX-012 Amendment 1: legacy modules must declare lifecycle marker in source. "
            f"Violations: {missing}",
        )

    def test_no_delete_lifecycle_in_registry(self):
        for path, record in LEGACY_MODULE_REGISTRY.items():
            self.assertIn(
                record["lifecycle"],
                (LegacyLifecycle.ACTIVE, LegacyLifecycle.QUARANTINED, LegacyLifecycle.DORMANT),
                f"{path}: DELETE is not a valid Phase 0 lifecycle state",
            )


class TestDecisionEngineOwnership(unittest.TestCase):
    """Invariant: only decision_engine (+ use_cases assembly) owns DecisionVerdict assignment."""

    VERDICT_ASSIGN_PATTERNS = (
        "DecisionVerdict.ACT",
        "DecisionVerdict.WAIT",
        "DecisionVerdict.PASS",
        "DecisionVerdict.REDUCE",
        "DecisionVerdict.DEFENSIVE",
    )

    def test_decision_verdict_assignment_bounded(self):
        root = REPO_ROOT / "analyzer"
        offenders: list[str] = []
        allowed = (root / "decision_engine", root / "use_cases")
        for path in root.rglob("*.py"):
            if any(str(path).startswith(str(a)) for a in allowed):
                continue
            text = path.read_text(encoding="utf-8")
            for pat in self.VERDICT_ASSIGN_PATTERNS:
                if pat in text and "legacy_" not in path.name:
                    offenders.append(f"{path.relative_to(REPO_ROOT)}: {pat}")
        self.assertEqual(
            offenders,
            [],
            "Architectural rule: DecisionVerdict may only be assigned inside "
            "analyzer/decision_engine or analyzer/use_cases (assembly). "
            f"Violations: {offenders}",
        )


class TestEvidenceEngineOwnership(unittest.TestCase):
    """Invariant: UI must not build evidence packets or call EE verdict shortcuts."""

    def test_ui_does_not_import_evidence_engine_builders(self):
        forbidden = (
            "from analyzer.evidence_engine.engine import EvidenceEngine",
            "from analyzer.evidence_engine import EvidenceEngine",
            "EvidenceEngine(",
            "recommend_from_packet(",
            "build_packet(",
        )
        offenders: list[str] = []
        for path in UI_ROOT.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            rel = str(path.relative_to(REPO_ROOT))
            for token in forbidden:
                if token in text:
                    offenders.append(f"{rel}: {token}")
        self.assertEqual(
            offenders,
            [],
            "Architectural rule: Evidence Engine is not a UI concern. "
            "UI must consume MorningBriefViewModel evidence sections only. "
            f"Violations: {offenders}",
        )


class TestMorningBriefViewModelContract(unittest.TestCase):
    """Invariant: MorningBriefViewModel is the authoritative daily contract."""

    def test_assemble_returns_morning_brief_view_model(self):
        sig = inspect.signature(assemble_morning_brief_view_model)
        self.assertIsNotNone(sig.return_annotation)

    def test_project_decision_card_accepts_only_morning_brief(self):
        sig = inspect.signature(project_decision_card)
        params = list(sig.parameters.values())
        self.assertEqual(len(params), 1)
        ann = str(params[0].annotation)
        self.assertIn("MorningBriefViewModel", ann)

    def test_load_brief_from_cache_returns_view_model(self):
        snap = ContextSnapshot(
            timestamp="t",
            market_regime="n",
            market_phase="regular",
            market_breadth="m",
            volatility_state="n",
            liquidity_state="normal",
            market_session=MappingProxyType({"phase": "regular"}),
            sector_strength=MappingProxyType({}),
            industry_strength=MappingProxyType({}),
            macro_state=MappingProxyType({}),
            global_market_state=MappingProxyType({}),
            risk_mode="NEUTRAL",
            trading_restrictions=(),
            confidence=0.8,
            snapshot_id="x",
            context_hash="",
        )
        art = DecisionArtifact(
            decision_id="d1",
            timestamp="",
            verdict=DecisionVerdict.ACT,
            reason="RELIANCE lines up.",
            evidence_packet_id="ep1",
            confidence=0.85,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
            trade_allowed=True,
        )
        packet = MagicMock(items=[], conflicts=[], gaps=[])
        brief = assemble_morning_brief_view_model(
            market="NSE",
            context=snap,
            decision=art,
            decision_source="equity",
            broker=BrokerSnapshot(state="connected", holdings_count=2),
            mis=MisTradeAdvisory(verdict="TRADE_OK", emoji="", headline="", summary="", score=70),
            os_report=InvestmentOS(starred_symbol="RELIANCE"),
            pins=[PinnedPlan("RELIANCE", 2850, 2815, 2930, "2026-07-16")],
            prefs=MagicMock(capital=50000),
            built_at="09:12 IST",
            scenario=MorningBriefScenario.NORMAL,
            stale=False,
            stale_reason="",
            context_from_cache=False,
            context_cache_age=None,
            data_error="",
            evidence_packet=packet,
        )
        self.assertIsInstance(brief, MorningBriefViewModel)
        cached = {
            "snapshot": snap.as_dict(),
            "mis": MisTradeAdvisory(verdict="TRADE_OK", emoji="", headline="", summary="", score=70),
            "os_report": InvestmentOS(starred_symbol="RELIANCE"),
            "pins": [PinnedPlan("RELIANCE", 2850, 2815, 2930, "2026-07-16")],
            "prefs": IntradayPrefs(capital=100_000, max_risk_pct=1.8),
            "built_at": "09:12 IST",
            "market": "NSE",
        }
        setattr(cached["os_report"], "decision_artifact", art)
        loaded = load_brief_from_cache(cached, broker=BrokerSnapshot(state="connected"))
        self.assertIsInstance(loaded, MorningBriefViewModel)


class TestTierAProjectionGuards(unittest.TestCase):
    """Invariant: Tier A must not invoke Decision Engine or rank opportunities."""

    def test_tier_a_no_decision_engine_runtime_imports(self):
        offenders: list[str] = []
        for rel in TIER_A_DECISION_PROJECTION:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            for forbidden in UI_FORBIDDEN_DECISION_ENGINE_IMPORTS:
                if forbidden in text:
                    offenders.append(f"{rel}: imports {forbidden}")
            for call in UI_FORBIDDEN_DECISION_ENGINE_CALLS:
                if call in text:
                    offenders.append(f"{rel}: calls {call}")
        self.assertEqual(
            offenders,
            [],
            "Architectural rule (Tier A): Decision projections must not import or call "
            "Decision Engine runtime modules. Use MorningBriefViewModel only. "
            f"Violations: {offenders}",
        )

    def test_tier_a_no_opportunity_ranking_functions(self):
        offenders: list[str] = []
        for rel in TIER_A_DECISION_PROJECTION:
            tree = ast.parse((REPO_ROOT / rel).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name in OPPORTUNITY_RANKING_FUNCTION_NAMES:
                    offenders.append(f"{rel}: defines {node.name}()")
        self.assertEqual(
            offenders,
            [],
            "Architectural rule (Tier A): opportunity ranking belongs in Morning Brief "
            "assembly, not decision projections. "
            f"Violations: {offenders}",
        )

    def test_tier_a_baseline_imports_do_not_expand(self):
        """Known pre-Phase-3 imports must not spread to other Tier A files."""
        allowed_models_importers = set(TIER_A_IMPORT_BASELINE)
        extra: list[str] = []
        for rel in TIER_A_DECISION_PROJECTION:
            if rel in TIER_A_IMPORT_BASELINE:
                continue
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            if "from analyzer.decision_engine.models import" in text:
                extra.append(rel)
            if "from analyzer.investment_os import" in text and "morning_brief" not in rel:
                extra.append(f"{rel}: investment_os import")
        self.assertEqual(
            extra,
            [],
            "Architectural rule (Tier A): raw InvestmentOS / DecisionArtifact imports "
            "are baseline-allowed only in plan_canvas and answer_canvas until Phase 3. "
            f"New violations: {extra}",
        )


class TestUIGuardrails(unittest.TestCase):
    """Invariant: UI must not build MIS advisory or emit OS verdict strings."""

    def test_build_mis_trade_advisory_quarantined_to_allowlist(self):
        offenders: list[str] = []
        for path in UI_ROOT.rglob("*.py"):
            rel = str(path.relative_to(REPO_ROOT))
            if rel in UI_MIS_BUILD_ALLOWLIST:
                continue
            if "build_mis_trade_advisory" in path.read_text(encoding="utf-8"):
                offenders.append(rel)
        self.assertEqual(
            offenders,
            [],
            "Architectural rule: UI must not call build_mis_trade_advisory except "
            f"data-loader allowlist {sorted(UI_MIS_BUILD_ALLOWLIST)}. "
            f"Violations: {offenders}",
        )

    def test_tier_a_no_investment_os_verdict_reads(self):
        offenders: list[str] = []
        patterns = ("os_report.verdict", ".verdict =", '["verdict"]')
        for rel in TIER_A_DECISION_PROJECTION:
            if rel in TIER_A_IMPORT_BASELINE:
                continue
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            for pat in patterns:
                if pat in text and "verdict_key" not in pat:
                    offenders.append(f"{rel}: {pat}")
        self.assertEqual(
            offenders,
            [],
            "Architectural rule (Tier A): must not read InvestmentOS.verdict — "
            "use brief.decision.verdict_key. "
            f"Violations: {offenders}",
        )

    def test_ui_no_decision_engine_engine_anywhere(self):
        offenders: list[str] = []
        for path in UI_ROOT.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            rel = str(path.relative_to(REPO_ROOT))
            for forbidden in UI_FORBIDDEN_DECISION_ENGINE_IMPORTS:
                if forbidden in text:
                    offenders.append(f"{rel}: {forbidden}")
        self.assertEqual(
            offenders,
            [],
            "Architectural rule: UI must never import Decision Engine runtime. "
            f"Violations: {offenders}",
        )


class TestTierBReflectiveGuards(unittest.TestCase):
    """Invariant: Tier B may enrich but must load brief for verdict context."""

    def test_tier_b_loads_brief_or_morning_brief_ui(self):
        missing: list[str] = []
        phase4_exempt = {
            "ui/components/trust_canvas.py",
            "ui/components/reflection_canvas.py",
        }
        for rel in TIER_B_REFLECTIVE_PROJECTION:
            if rel in phase4_exempt:
                continue
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            if "morning_brief_ui" not in text and "MorningBriefViewModel" not in text:
                missing.append(rel)
        self.assertEqual(
            missing,
            [],
            "Architectural rule (Tier B): reflective projections must reference "
            "morning_brief_ui or MorningBriefViewModel "
            f"(exempt until Phase 4: {sorted(phase4_exempt)}). "
            f"Missing: {missing}",
        )


class TestProjectionDeterminism(unittest.TestCase):
    """Invariant: same MorningBriefViewModel → same verdict, reason, symbol, confidence."""

    _packet_patcher = None

    @classmethod
    def setUpClass(cls):
        cls.snap = ContextSnapshot(
            timestamp="2026-08-05T09:00:00+05:30",
            market_regime="Neutral",
            market_phase="regular",
            market_breadth="mixed",
            volatility_state="normal",
            liquidity_state="normal",
            market_session=MappingProxyType({"phase": "regular", "is_open": True}),
            sector_strength=MappingProxyType({}),
            industry_strength=MappingProxyType({}),
            macro_state=MappingProxyType({}),
            global_market_state=MappingProxyType({}),
            risk_mode="NEUTRAL",
            trading_restrictions=(),
            confidence=0.85,
            snapshot_id="ctx1",
            context_hash="",
        )
        cls.art = DecisionArtifact(
            decision_id="d1",
            timestamp="2026-08-05T09:00:00",
            verdict=DecisionVerdict.ACT,
            reason="RELIANCE lines up with structure and timing.",
            evidence_packet_id="ep1",
            confidence=0.85,
            uncertainty=UncertaintyVector(),
            capital_recommendation="",
            execution_recommendation="",
            trade_allowed=True,
        )
        cls.packet = MagicMock(
            items=[
                MagicMock(
                    label="Regime",
                    category=MagicMock(value="Market"),
                    type=MagicMock(value="FACT"),
                    source=MagicMock(value="internal_model"),
                    confidence=MagicMock(value="high"),
                    value="Trend",
                    explanation="",
                )
            ],
            conflicts=[],
            gaps=[],
        )
        cls.pin = PinnedPlan("RELIANCE", 2850, 2815, 2930, "2026-07-16", side="LONG")
        cls.broker = BrokerSnapshot(state="connected", holdings_count=2)
        cls.mis = MisTradeAdvisory(
            verdict="TRADE_OK", emoji="", headline="", summary="Balanced.", score=70, flags=()
        )
        cls.os_report = InvestmentOS(starred_symbol="RELIANCE", next_step="")
        setattr(cls.os_report, "decision_artifact", cls.art)
        cls.prefs = IntradayPrefs(capital=100_000, max_risk_pct=1.8)
        cls._packet_patcher = patch(
            "analyzer.use_cases.decision_context_bundle.fetch_evidence_packet_safe",
            return_value=cls.packet,
        )
        cls._packet_patcher.start()
        cls.cached = {
            "_context_bundle_version": "1",
            "snapshot": cls.snap.as_dict(),
            "mis": cls.mis,
            "os_report": cls.os_report,
            "decision": cls.art,
            "decision_source": "equity",
            "pins": [cls.pin],
            "prefs": cls.prefs,
            "built_at": "09:12 IST",
            "market": "NSE",
            "broker": cls.broker.to_dict(),
            "_broker_at_build": cls.broker.to_dict(),
            "scenario": "normal",
            "stale": False,
            "stale_reason": "",
            "context_from_cache": False,
            "context_cache_age": None,
            "data_error": "",
        }
        domain = domain_from_cache_bundle(cls.cached, broker=cls.broker)
        cls.brief = view_model_from_domain(domain, broker=cls.broker)

    @classmethod
    def tearDownClass(cls):
        if cls._packet_patcher is not None:
            cls._packet_patcher.stop()

    def test_today_hero_matches_brief_canonical_fields(self):
        card = project_decision_card(self.brief)
        self.assertEqual(
            card.verdict_key,
            self.brief.decision.verdict_key,
            "Tier A Today: verdict_key must match MorningBriefViewModel.decision",
        )
        self.assertEqual(
            card.reason,
            self.brief.decision.reason,
            "Tier A Today: reason must match MorningBriefViewModel.decision",
        )
        self.assertEqual(
            card.confidence_level,
            self.brief.decision.confidence_level,
            "Tier A Today: confidence must match MorningBriefViewModel.decision",
        )
        if self.brief.opportunity.visible:
            self.assertIsNotNone(card.best_opportunity)
            assert card.best_opportunity is not None
            self.assertEqual(
                card.best_opportunity.symbol,
                self.brief.opportunity.symbol,
                "Tier A Today: symbol must match MorningBriefViewModel.opportunity",
            )

    def test_trades_verdict_and_symbol_match_brief(self):
        state = verdict_state_from_brief(self.brief)
        self.assertEqual(
            state.key,
            self.brief.decision.verdict_key,
            "Tier A Trades: verdict_state must match MorningBriefViewModel",
        )
        plan = build_trade_plan_view(
            state=state,
            pin=self.pin,
            decision=self.art,
            mis=self.mis,
            snapshot=self.snap,
            prefs=self.prefs,
        )
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(
            plan.symbol,
            self.brief.opportunity.symbol,
            "Tier A Trades: plan symbol must match MorningBriefViewModel.opportunity",
        )
        # Plan reason trims artifact text; must share core decision copy (Phase 3: brief-only reason).
        core = self.art.reason.split(".")[0].strip()
        self.assertIn(
            core[:24],
            plan.reason,
            "Tier A Trades: plan reason must derive from DecisionArtifact.reason in brief",
        )

    def test_ask_starred_symbol_verdict_aligns_with_brief(self):
        answer = build_ask_answer(
            "buy RELIANCE",
            broker=self.broker,
            cached=self.cached,
        )
        from ui.components.answer_canvas import _verdict_key_to_answer

        expected_key, _ = _verdict_key_to_answer(self.brief.decision.verdict_key)
        self.assertEqual(
            answer.answer_key,
            expected_key,
            "Tier A Ask: starred-symbol answer must align with brief.decision.verdict_key",
        )

    @patch("ui.components.proof_mapper._fetch_candles", return_value=())
    @patch("ui.components.proof_mapper._current_price", return_value=2862.0)
    def test_proof_verdict_state_matches_brief(self, *_mocks):
        brief = load_brief_from_cache(self.cached, broker=self.broker)
        state = verdict_state_from_brief(brief)
        proof = build_structure_proof(
            market="NSE",
            cached=self.cached,
            proof_mode=state.key,
            origin="today",
        )
        self.assertEqual(
            proof.verdict_state,
            brief.decision.verdict_key,
            "Tier B Proof: verdict_state must not override MorningBriefViewModel",
        )
        self.assertEqual(
            proof.symbol.replace(".NS", "").replace(".BO", ""),
            self.brief.opportunity.symbol,
            "Tier B Proof: symbol must match brief opportunity when trade setup exists",
        )


class TestQuarantinedModuleIsolation(unittest.TestCase):
    """Invariant: duplicate intel builder stays quarantined — not imported by Tier A except home."""

    def test_today_intelligence_not_imported_by_tier_a_except_home(self):
        offenders: list[str] = []
        for rel in TIER_A_DECISION_PROJECTION:
            if rel == "ui/components/home_dashboard.py":
                continue
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            if "today_intelligence" in text:
                offenders.append(rel)
        self.assertEqual(
            offenders,
            [],
            "Architectural rule: QUARANTINED today_intelligence must not spread to "
            "Tier A projections other than home_dashboard (Phase 2 removes this). "
            f"Violations: {offenders}",
        )


if __name__ == "__main__":
    unittest.main()
