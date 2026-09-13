from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
SPEC = importlib.util.spec_from_file_location("roadmap_patch_director", TOOLS / "roadmap_patch_director.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def synthetic_project(checked_gate_a=()):
    gate_a = "\n".join(f"- [{'x' if i in checked_gate_a else ' '}] A{i}" for i in range(1, 13))
    gate_b = "\n".join(f"- [ ] B{i}" for i in range(1, 14))
    gate_c = "\n".join(f"- [ ] C{i}" for i in range(1, 16))
    gate_d = "\n".join(f"- [ ] D{i}" for i in range(1, 13))
    completed = len(tuple(checked_gate_a))
    remaining = 52 - completed
    percent = round(completed * 100.0 / 52, 1)
    filled = min(20, max(0, int((percent * 20 / 100.0) + 0.5)))
    bar = "█" * filled + "░" * (20 - filled)
    return f"""# Project #002 — HD Completion Roadmap
<!-- SWIR-ROADMAP-STANDARD:v1 -->
<img src="https://img.shields.io/badge/ROADMAP-{percent:.1f}%25-x">
<img src="https://img.shields.io/badge/DONE-{completed}%2F52-x">
```text
{bar} {percent:.1f}%
```
| ✅ Completed | ⏳ Remaining | 📦 Total | 🎯 Progress |
|---:|---:|---:|---:|
| **{completed}** | **{remaining}** | **52** | **{percent:.1f}%** |
## Gate A — Complete local capture
{gate_a}
## Gate B — HD art production
{gate_b}
## Gate C — QA
{gate_c}
## Gate D — Release
{gate_d}
"""


def synthetic_master(completed=0):
    remaining = 52 - completed
    percent = round(completed * 100.0 / 52, 1)
    filled = min(20, max(0, int((percent * 20 / 100.0) + 0.5)))
    bar = "█" * filled + "░" * (20 - filled)
    return f"""# NES New Life — Master Roadmap
<!-- SWIR-ROADMAP-STANDARD:v1 -->
## 🎮 Current game progress
```text
{bar} {percent:.1f}%
```
| 🎮 Current game | ✅ Completed gates | ⏳ Remaining | 🎯 Progress |
|---|---:|---:|---:|
| **#002 Tiny Toon Visual Remaster** | **{completed}** | **{remaining}** | **{percent:.1f}%** |
| #002 | Tiny Toon Visual Remaster | **ACTIVE** | **{percent:.1f}%** | [`ROADMAP`](x) |
"""


def review_and_ledger(indexes=(1,), fingerprint="fp"):
    indexes = set(indexes)
    criteria = []
    attestations = []
    for index in range(1, 13):
        criteria.append({
            "index": index,
            "evidence_status": "EVIDENCE_READY_FOR_REVIEW",
            "review_status": "VERIFIED_GATE_A" if index in indexes else "AWAITING_HUMAN_ATTESTATION",
            "source_fingerprint_sha256": fingerprint,
        })
        if index in indexes:
            attestations.append({
                "index": index,
                "confirmation": "VERIFIED_GATE_A",
                "capture_fingerprint_sha256": fingerprint,
                "source_fingerprint_sha256": fingerprint,
            })
    review = {
        "schema": MODULE.REVIEW_SCHEMA,
        "capture_fingerprint_sha256": fingerprint,
        "criteria": criteria,
        "roadmap_patch_preview": {"verified_gate_a_indexes": sorted(indexes)},
    }
    ledger = {
        "schema": MODULE.REVIEW_SCHEMA,
        "capture_fingerprint_sha256": fingerprint,
        "attestations": attestations,
    }
    return review, ledger


class RoadmapPatchDirectorTests(unittest.TestCase):
    def test_verified_attestations_patch_only_gate_a_and_both_dashboards(self):
        review, ledger = review_and_ledger((1, 3))
        project = synthetic_project()
        master = synthetic_master()
        result = MODULE.build_patch(review, ledger, project, master)

        self.assertEqual(result["new_gate_a_indexes"], [1, 3])
        self.assertEqual(result["stats"]["completed"], 2)
        self.assertEqual(result["stats"]["remaining"], 50)
        self.assertEqual(result["stats"]["percent"], 3.8)
        self.assertIn("- [x] A1", result["project_text"])
        self.assertIn("- [x] A3", result["project_text"])
        self.assertIn("- [ ] B1", result["project_text"])
        self.assertIn("| **2** | **50** | **52** | **3.8%** |", result["project_text"])
        self.assertIn("| **#002 Tiny Toon Visual Remaster** | **2** | **50** | **3.8%** |", result["master_text"])
        self.assertIn("| #002 | Tiny Toon Visual Remaster | **ACTIVE** | **3.8%** |", result["master_text"])

    def test_stale_fingerprint_fails_closed(self):
        review, ledger = review_and_ledger((1,), "current")
        ledger["capture_fingerprint_sha256"] = "old"
        with self.assertRaises(MODULE.PatchError):
            MODULE.build_patch(review, ledger, synthetic_project(), synthetic_master())

    def test_unattested_preexisting_gate_a_completion_fails_closed(self):
        review, ledger = review_and_ledger((1,))
        with self.assertRaises(MODULE.PatchError):
            MODULE.build_patch(review, ledger, synthetic_project((1, 2)), synthetic_master(2))

    def test_gate_b_d_are_byte_stable(self):
        review, ledger = review_and_ledger((2, 4, 6))
        project = synthetic_project()
        result = MODULE.build_patch(review, ledger, project, synthetic_master())
        before = project.split("## Gate B — HD art production", 1)[1]
        after = result["project_text"].split("## Gate B — HD art production", 1)[1]
        self.assertEqual(before, after)

    def test_write_outputs_are_preview_only(self):
        review, ledger = review_and_ledger((1,))
        project = synthetic_project()
        master = synthetic_master()
        result = MODULE.build_patch(review, ledger, project, master)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project_path = root / "ROADMAP.md"
            master_path = root / "MASTER.md"
            project_path.write_text(project, encoding="utf-8")
            master_path.write_text(master, encoding="utf-8")
            outputs = MODULE.write_outputs(result, project, master, root / "Reports")
            self.assertEqual(project_path.read_text(encoding="utf-8"), project)
            self.assertEqual(master_path.read_text(encoding="utf-8"), master)
            diff = Path(outputs["diff"]).read_text(encoding="utf-8")
            self.assertIn("projects/002_tiny_toon_visual_remaster/ROADMAP.md", diff)
            self.assertIn("docs/ROADMAP.md", diff)


if __name__ == "__main__":
    unittest.main()
