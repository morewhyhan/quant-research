"""Non-overwriting experiment storage and explicit integrity/version checks."""
from __future__ import annotations
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from tools.experiments.report import render_report

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "data/private/archive"


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_files():
    """Fingerprint loaded research modules, never unrelated tests/import scripts."""
    paths = {Path(__file__).resolve(), ROOT / "tools/__main__.py"}
    for module in list(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if filename:
            path = Path(filename).resolve()
            if path.suffix == ".py" and any(path.is_relative_to(ROOT / folder) for folder in ("tools", "factors")):
                paths.add(path)
    return sorted(paths)


def save(output, metrics, inputs, artifacts=None):
    output = Path(output)
    if output.exists():
        raise ValueError("Output exists: choose a new experiment directory")
    records = []
    for item in inputs:
        path = Path(item).resolve()
        records.append({"path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
                        "sha256": digest(path)})
    manifest = {"schema_version": 2, "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                "status": "completed", "command": [sys.executable, *sys.argv], "python": platform.python_version(),
                "inputs": records, "code": [{"path": p.relative_to(ROOT).as_posix(), "sha256": digest(p)} for p in code_files()],
                "artifact_hashes": {}}
    payloads = {"metrics.json": dump(metrics), "report.md": render_report(metrics)}
    for name, value in (artifacts or {}).items():
        if Path(name).name != name or name in {"manifest.json", "metrics.json", "report.md"}:
            raise ValueError("Artifact names must be unique simple filenames")
        payloads[name] = dump(value)
    output.mkdir(parents=True, exist_ok=False)
    for name, body in payloads.items():
        (output / name).write_text(body, encoding="utf-8")
        manifest["artifact_hashes"][name] = digest(output / name)
    (output / "manifest.json").write_text(dump(manifest), encoding="utf-8")
    print(f"Saved experiment: {output.resolve()}")


def relocated_input(path):
    """Optionally resolve moved inputs from a local relocation list."""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    if candidate.is_file():
        return candidate
    ledger = ARCHIVE / "relocations.json"
    if candidate.is_relative_to(ROOT) and ledger.is_file():
        old = candidate.relative_to(ROOT).as_posix()
        for item in json.loads(ledger.read_text(encoding="utf-8-sig")):
            if item["from"] == old:
                target = (ROOT / item["to"]).resolve()
                if not target.is_relative_to(ROOT):
                    raise ValueError("Relocated input escapes repository")
                return target
    return candidate


def verify(output):
    output = Path(output).resolve()
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    evidence_mismatches, code_differences = [], []
    for name, expected in manifest["artifact_hashes"].items():
        path = (output / name).resolve()
        if not path.is_relative_to(output):
            raise ValueError("Artifact path escapes experiment")
        if not path.is_file() or digest(path) != expected:
            evidence_mismatches.append(f"artifact:{name}")
    for item in manifest["inputs"]:
        path = relocated_input(item["path"])
        if not path.is_file() or digest(path) != item["sha256"]:
            evidence_mismatches.append(f"input:{item['path']}")
    for item in manifest["code"]:
        path = (ROOT / item["path"]).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError("Code path escapes repository")
        if not path.is_file() or digest(path) != item["sha256"]:
            code_differences.append(item["path"])
    mismatches = evidence_mismatches + [f"code:{name}" for name in code_differences]
    return {"evidence_intact": not evidence_mismatches,
            "current_code_matches": not code_differences,
            "evidence_mismatches": evidence_mismatches, "code_differences": code_differences,
            "intact_against_current_files": not mismatches, "mismatches": mismatches,
            "limitations": "Identity checks only; code-version differences do not imply corrupted results or prove market validity"}
