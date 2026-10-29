"""Scenario prompts and experiment lineage, without requiring market data."""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools import __main__ as cli
from tools.experiments.planning import KINDS, parent_record, preface, study_kind

ROOT = Path(__file__).resolve().parents[1]


class ScenarioTests(unittest.TestCase):
    def test_all_research_types_have_method_prompts(self):
        self.assertEqual(len(KINDS), 10)
        for kind in KINDS:
            self.assertIn(kind, preface(kind))
            self.assertIn("本次重点", preface(kind))

    def test_factor_and_followup_use_one_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            research = root / "research"
            research.mkdir()
            (research / "README.md").write_text("| 问题 | 报告 | 过程 |\n| --- | --- | --- |\n", encoding="utf-8")
            for name in ("TEMPLATE.md", "EXPERIMENT_TEMPLATE.md"):
                (research / name).write_text((ROOT / "research" / name).read_text(encoding="utf-8"), encoding="utf-8")
            def call(*arguments):
                with patch.object(sys, "argv", ["tools", *arguments]):
                    return cli.main()
            with patch.object(cli, "ROOT", root), contextlib.redirect_stdout(io.StringIO()):
                call("init-study", "signal", "--kind", "factor")
                call("init-experiment", "signal", "baseline")
                call("init-experiment", "signal", "followup", "--kind", "robustness",
                     "--parent", "baseline", "--relation", "out-of-sample")
                report = (research / "signal/report.md").read_text(encoding="utf-8")
                self.assertIn("factor", report)
                self.assertIn("factor", (research / "signal/experiments/baseline/experiment.md").read_text(encoding="utf-8"))
                self.assertIn("../../learning/research-scenarios.md", report)
                record = (research / "signal/experiments/followup/experiment.md").read_text(encoding="utf-8")
                self.assertIn("robustness", record)
                self.assertIn("../baseline/experiment.md", record)
                self.assertIn("样本外评价", record)
                self.assertEqual([p.name for p in research.iterdir() if p.is_dir()], ["signal"])
                for name, parent in (("missing", "absent"), ("escape", "../../../outside")):
                    with self.assertRaises(ValueError):
                        call("init-experiment", "signal", name, "--parent", parent)
                    self.assertFalse((research / f"signal/experiments/{name}").exists())

    def test_legacy_record_can_be_linked_without_rewriting(self):
        with tempfile.TemporaryDirectory() as temp:
            study = Path(temp)
            experiments = study / "experiments"
            experiments.mkdir()
            record = experiments / "old-run.md"
            record.write_text("# Old result\n", encoding="utf-8")
            text = parent_record(study, experiments / "new-run", "old-run.md", "correction")
            self.assertIn("../old-run.md", text)
            self.assertIn("修错", text)
            self.assertEqual(record.read_text(encoding="utf-8"), "# Old result\n")

    def test_relation_requires_a_parent(self):
        with self.assertRaises(ValueError):
            parent_record(Path("."), Path("run"), None, "correction")

    def test_legacy_study_default_preserves_compatibility(self):
        with tempfile.TemporaryDirectory() as temp:
            study = Path(temp)
            (study / "report.md").write_text("# Historical study", encoding="utf-8")
            self.assertEqual(study_kind(study), "strategy")


if __name__ == "__main__":
    unittest.main()
