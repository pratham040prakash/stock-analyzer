"""Unit tests for the APEX Engineering Context MCP server."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engineering.mcp.engineering_context.config import EngineeringContextConfig
from engineering.mcp.engineering_context.git import GitCommandError
from engineering.mcp.engineering_context.git.changed_files import get_changed_files
from engineering.mcp.engineering_context.git.diff import get_git_diff
from engineering.mcp.engineering_context.models import TestCaseResult, TestResults, to_dict
from engineering.mcp.engineering_context.server import EngineeringContextService
from engineering.mcp.engineering_context.testing.test_results import get_test_results
from engineering.mcp.engineering_context.utilities.hashing import sha256_text
from engineering.mcp.engineering_context.utilities.paths import directory_key, find_repo_root


class TestPaths(unittest.TestCase):
    def test_find_repo_root(self) -> None:
        root = find_repo_root()
        self.assertTrue((root / ".git").exists())

    def test_directory_key(self) -> None:
        self.assertEqual(directory_key("ui/components/foo.py"), "ui")
        self.assertEqual(directory_key("README.md"), ".")


class TestHashing(unittest.TestCase):
    def test_sha256_text_is_deterministic(self) -> None:
        self.assertEqual(sha256_text("abc"), sha256_text("abc"))
        self.assertNotEqual(sha256_text("abc"), sha256_text("abcd"))


class TestChangedFiles(unittest.TestCase):
    def setUp(self) -> None:
        self.config = EngineeringContextConfig.from_env()

    def test_changed_files_structure(self) -> None:
        result = get_changed_files(self.config, base="main", head="HEAD")
        self.assertTrue(result.base_ref)
        self.assertTrue(result.head_ref)
        self.assertIsInstance(result.by_directory, dict)

    @patch("engineering.platform.git.changed_files.run_git")
    @patch("engineering.platform.git.changed_files.resolve_compare_refs")
    def test_changed_files_parses_name_status(
        self,
        mock_resolve,
        mock_run_git,
    ) -> None:
        mock_resolve.return_value = ("base", "head")
        mock_run_git.return_value = "A\tui/new.py\nM\tanalyzer/foo.py\nD\ttests/old.py\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            config = EngineeringContextConfig(repo_root=root)
            result = get_changed_files(config)
        self.assertEqual(result.added, ("ui/new.py",))
        self.assertEqual(result.modified, ("analyzer/foo.py",))
        self.assertEqual(result.deleted, ("tests/old.py",))
        self.assertIn("ui", result.by_directory)


class TestGitDiff(unittest.TestCase):
    def test_git_diff_includes_hash(self) -> None:
        config = EngineeringContextConfig.from_env()
        result = get_git_diff(config, base="main", head="HEAD")
        self.assertEqual(result.sha256, sha256_text(result.diff))
        self.assertEqual(result.line_count, len(result.diff.splitlines()))


class TestRepositoryTools(unittest.TestCase):
    def setUp(self) -> None:
        self.service = EngineeringContextService()

    def test_get_repository_status(self) -> None:
        payload = self.service.call("get_repository_status")
        self.assertIn("branch", payload)
        self.assertIn("head_sha", payload)
        self.assertIn("clean", payload)

    def test_get_recent_commits(self) -> None:
        payload = self.service.call("get_recent_commits", limit=3)
        self.assertEqual(payload["branch"], self.service.call("get_repository_status")["branch"])
        self.assertLessEqual(len(payload["commits"]), 3)

    def test_get_changed_files_tool(self) -> None:
        payload = self.service.call("get_changed_files", base="main", head="HEAD")
        self.assertIn("added", payload)
        self.assertIn("by_directory", payload)


class TestPhaseScaffolds(unittest.TestCase):
    def setUp(self) -> None:
        self.service = EngineeringContextService()

    def test_get_architecture_map(self) -> None:
        payload = self.service.call("get_architecture_map", base="main", head="HEAD")
        self.assertIn("affected_modules", payload)
        self.assertIn("boundaries_crossed", payload)

    def test_get_dependency_graph(self) -> None:
        payload = self.service.call("get_dependency_graph", base="main", head="HEAD")
        self.assertIn("imports", payload)

    def test_search_aps(self) -> None:
        payload = self.service.call("search_aps")
        self.assertIsInstance(payload, list)
        self.assertGreater(len(payload), 0)
        self.assertIn("id", payload[0])

    def test_search_adr(self) -> None:
        payload = self.service.call("search_adr")
        self.assertIsInstance(payload, list)
        self.assertGreater(len(payload), 0)
        self.assertIn("id", payload[0])

    def test_get_review_context(self) -> None:
        payload = self.service.call("get_review_context", compare_branch="main")
        self.assertIn("git_diff_sha256", payload)
        self.assertIn("changed_files", payload)
        self.assertIn("architecture", payload)
        self.assertIn("aps", payload)
        self.assertIn("adr", payload)
        self.assertIn("tests", payload)
        self.assertIn("dependency_graph", payload)


class TestTestResults(unittest.TestCase):
    def test_cached_results_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            config = EngineeringContextConfig(
                repo_root=root,
                test_results_cache_dir=root / ".apex" / "engineering_context",
            )
            result = get_test_results(config, execute=False)
            self.assertEqual(result.source, "unavailable")

    def test_load_cached_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache_dir = root / ".apex" / "engineering_context"
            cache_dir.mkdir(parents=True)
            payload = {
                "executed_at": "2026-08-06T00:00:00+00:00",
                "passed": 1,
                "failed": 0,
                "skipped": 0,
                "errors": 0,
                "duration_seconds": 0.1,
                "cases": [{"name": "tests.test_demo", "status": "passed"}],
            }
            (cache_dir / "test_results.json").write_text(json.dumps(payload), encoding="utf-8")
            config = EngineeringContextConfig(repo_root=root, test_results_cache_dir=cache_dir)
            result = get_test_results(config, execute=False)
            self.assertEqual(result.source, "cache")
            self.assertEqual(result.passed, 1)

    def test_execute_targeted_tests(self) -> None:
        config = EngineeringContextConfig.from_env()
        result = get_test_results(
            config,
            execute=True,
            pattern="test_engineering_context_mcp.py",
        )
        self.assertEqual(result.source, "executed")
        self.assertGreater(result.passed, 0)


class TestModels(unittest.TestCase):
    def test_to_dict_serializes_dataclass(self) -> None:
        payload = to_dict(
            TestResults(
                source="cache",
                executed_at=None,
                passed=1,
                failed=0,
                skipped=0,
                errors=0,
                duration_seconds=0.0,
                cases=(TestCaseResult(name="x", status="passed"),),
            )
        )
        self.assertEqual(payload["passed"], 1)
        self.assertEqual(payload["cases"][0]["name"], "x")


class TestGitErrors(unittest.TestCase):
    def test_git_command_error_message(self) -> None:
        error = GitCommandError(("status",), 128, "fatal: not a git repository")
        self.assertIn("git status failed", str(error))


if __name__ == "__main__":
    unittest.main()
