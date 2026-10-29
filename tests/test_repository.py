"""Keep the repository navigable without enforcing financial conclusions."""
import contextlib
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote
from tools.experiments import storage
from tools.engines.freqtrade import runner

ROOT = Path(__file__).resolve().parents[1]


def documents():
    for path in ROOT.rglob("*.md"):
        parts = path.relative_to(ROOT).parts
        if parts[:2] == ("data", "private") or parts[0] == ".git":
            continue
        yield path


class RepositoryTests(unittest.TestCase):
    def test_public_document_links(self):
        for path in documents():
            for target in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", path.read_text(encoding="utf-8-sig")):
                if re.match(r"^[a-zA-Z]+:", target) or target.startswith("#"):
                    continue
                destination = (path.parent / unquote(target.split("#")[0])).resolve()
                self.assertTrue(destination.is_relative_to(ROOT), (path, target))
                relative = destination.relative_to(ROOT)
                if relative.parts[:2] == ("data", "private"):
                    continue  # Clearly labelled local material is absent in public clones.
                self.assertTrue(destination.exists(), (path.relative_to(ROOT), target))

    def test_tools_top_level_has_one_command_entry(self):
        files = {p.name for p in (ROOT / "tools").iterdir() if p.is_file()}
        self.assertEqual(files, {"README.md", "commands.md", "__init__.py", "__main__.py"})
        self.assertFalse((ROOT / "tools/tests").exists())

    def test_blank_forms_are_present(self):
        for relative in ("research/TEMPLATE.md", "research/EXPERIMENT_TEMPLATE.md",
                         "strategies/TEMPLATE.md", "factors/TEMPLATE.md", "data/datasets/TEMPLATE.md"):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_cli_from_repository_root(self):
        result = subprocess.run([sys.executable, "-B", "-m", "tools", "--help"], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("init-study", result.stdout)

    def test_new_study_and_experiment_have_separate_homes(self):
        from tools import __main__ as cli
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            research = root / "research"
            research.mkdir()
            (research / "README.md").write_text("| 研究 | 报告 | 过程 |\n| --- | --- | --- |\n", encoding="utf-8")
            for name in ("TEMPLATE.md", "EXPERIMENT_TEMPLATE.md"):
                (research / name).write_text((ROOT / "research" / name).read_text(encoding="utf-8"), encoding="utf-8")
            with patch.object(cli, "ROOT", root), contextlib.redirect_stdout(io.StringIO()):
                with patch.object(sys, "argv", ["tools", "init-study", "example"]):
                    self.assertEqual(cli.main(), 0)
                    with self.assertRaises(ValueError):
                        cli.main()
                self.assertEqual({p.name for p in (research / "example").iterdir()}, {"report.md"})
                self.assertIn("example/report.md", (research / "README.md").read_text(encoding="utf-8"))
                with patch.object(sys, "argv", ["tools", "init-experiment", "example", "2025-v1"]):
                    self.assertEqual(cli.main(), 0)
                    with self.assertRaises(ValueError):
                        cli.main()
                self.assertTrue((research / "example/experiments/2025-v1/experiment.md").exists())

    def test_research_bodies_are_not_collected_in_readmes(self):
        for directory in (ROOT / "research").iterdir():
            if directory.is_dir():
                self.assertTrue((directory / "report.md").is_file(), directory.name)

    def test_recorded_code_excludes_tests_and_maintenance(self):
        paths = storage.code_files()
        self.assertTrue(paths)
        self.assertTrue(all(not p.is_relative_to(ROOT / "tests") for p in paths))
        self.assertTrue(all("archive" not in p.relative_to(ROOT).parts for p in paths))

    def test_version_difference_is_not_corrupt_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "run"
            with contextlib.redirect_stdout(io.StringIO()):
                storage.save(output, {"test": True}, [])
            manifest_path = output / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["code"][0]["sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = storage.verify(output)
            self.assertTrue(result["evidence_intact"])
            self.assertFalse(result["current_code_matches"])

    def test_artifact_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                storage.save(Path(temp) / "run", {}, [], {"../outside.json": {}})
            self.assertFalse((Path(temp) / "run").exists())

    def test_engine_never_allows_live_trade(self):
        with patch("subprocess.run") as execute:
            with self.assertRaises(SystemExit):
                runner.main(["trade"])
            execute.assert_not_called()

    def test_relocated_historical_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "data/private/archive"
            archive.mkdir(parents=True)
            target = archive / "input.json"
            target.write_text("{}", encoding="utf-8")
            (archive / "relocations.json").write_text(json.dumps([
                {"from": "old/input.json", "to": "data/private/archive/input.json"}
            ]), encoding="utf-8")
            with patch.object(storage, "ROOT", root), patch.object(storage, "ARCHIVE", archive):
                self.assertEqual(storage.relocated_input("old/input.json"), target)


if __name__ == "__main__":
    unittest.main()
