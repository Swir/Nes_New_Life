from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from roadmap_evidence_readiness import assess, parse_roadmap, write_outputs


ROADMAP = """# Test
## Gate A — Capture
- [ ] Boot/title/menu states
- [ ] Compare repeated captures and resolve every `CAPTURE_REGRESSION`
## Gate B — Art
- [ ] Confirm candidate pack preserves `hires.txt` and Pixel QA PASSes before continuing
- [ ] Zero TODO/INVALID masters in every captured group
## Gate C — QA
- [ ] Pixel QA PASS and fingerprint matches the current build
- [ ] Fullscreen is verified against the active monitor bounds; windowed-only playtest is rejected
- [ ] Complete all ten cases with current-build PASS evidence
## Gate D — Release
- [ ] Final Release Readiness Director reports `FINAL RELEASE GATE: PASS`
- [ ] Runtime pack contains no ROM/save-state/patch payloads
"""


def dump(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class EvidenceReadinessTests(unittest.TestCase):
    def make_root(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "ROADMAP.md").write_text(ROADMAP, encoding="utf-8")
        return root

    def test_parser_keeps_gate_and_checkbox_count(self) -> None:
        root = self.make_root()
        rows = parse_roadmap(root / "ROADMAP.md")
        self.assertEqual(len(rows), 9)
        self.assertEqual([row["gate"] for row in rows[:2]], ["A", "A"])
        self.assertEqual(rows[-1]["gate"], "D")

    def test_no_local_reports_never_invents_completion(self) -> None:
        result = assess(self.make_root())
        self.assertEqual(result["roadmap_items"], 9)
        self.assertEqual(result["counts"].get("READY_FOR_HUMAN_REVIEW", 0), 0)
        self.assertGreater(result["counts"].get("WAITING_LOCAL_EVIDENCE", 0), 0)

    def test_clean_capture_acceptance_only_marks_review_ready(self) -> None:
        root = self.make_root()
        dump(root / "Reports/CaptureCoverageAcceptance/CAPTURE_COVERAGE_ACCEPTANCE.json", {
            "acceptance_gate": "READY_FOR_GATE_A_REVIEW",
            "mission_summary": {"verified": 11, "total": 11},
            "hard_blockers": [],
            "capture_integrity": {"admission_gate": "PASS", "regression_count": 0, "structural_blockers": [], "at_risk_missions": []},
        })
        result = assess(root)
        gate_a = [row for row in result["items"] if row["gate"] == "A"]
        self.assertTrue(all(row["status"] == "READY_FOR_HUMAN_REVIEW" for row in gate_a))
        self.assertTrue(all(not row["checked"] for row in gate_a))

    def test_regression_blocks_regression_checkbox(self) -> None:
        root = self.make_root()
        dump(root / "Reports/CaptureCoverageAcceptance/CAPTURE_COVERAGE_ACCEPTANCE.json", {
            "acceptance_gate": "BLOCKED",
            "mission_summary": {"verified": 10, "total": 11},
            "hard_blockers": [{"kind": "CAPTURE_REGRESSION", "detail": "1 regression remains"}],
            "capture_integrity": {"admission_gate": "BLOCKED", "regression_count": 1, "structural_blockers": [], "at_risk_missions": []},
        })
        result = assess(root)
        regression = next(row for row in result["items"] if "CAPTURE_REGRESSION" in row["text"])
        self.assertEqual(regression["status"], "BLOCKED")

    def test_exact_build_release_stages_expose_review_candidates(self) -> None:
        root = self.make_root()
        dump(root / "Reports/FinalReleaseReadiness/FINAL_RELEASE_READINESS.json", {
            "release_gate": "PASS",
            "stages": [
                {"name": "HD PACK STRUCTURE", "gate": "PASS", "summary": "clean"},
                {"name": "FINAL ART", "gate": "PASS", "summary": "done"},
                {"name": "PIXEL QA", "gate": "PASS", "summary": "exact-build PASS"},
                {"name": "VERIFIED FULLSCREEN", "gate": "PASS", "summary": "verified"},
                {"name": "FINAL REGRESSION", "gate": "PASS", "summary": "10/10"},
            ],
        })
        result = assess(root)
        by_text = {row["text"]: row for row in result["items"]}
        self.assertEqual(by_text["Pixel QA PASS and fingerprint matches the current build"]["status"], "READY_FOR_HUMAN_REVIEW")
        self.assertEqual(by_text["Fullscreen is verified against the active monitor bounds; windowed-only playtest is rejected"]["status"], "READY_FOR_HUMAN_REVIEW")
        self.assertEqual(by_text["Complete all ten cases with current-build PASS evidence"]["status"], "READY_FOR_HUMAN_REVIEW")
        self.assertEqual(by_text["Final Release Readiness Director reports `FINAL RELEASE GATE: PASS`"]["status"], "READY_FOR_HUMAN_REVIEW")

    def test_outputs_are_metadata_only(self) -> None:
        root = self.make_root()
        result = assess(root)
        outputs = write_outputs(result, root / "Reports/RoadmapEvidenceReadiness")
        raw = Path(outputs["json"]).read_text(encoding="utf-8")
        self.assertNotIn(".nes", raw.lower())
        self.assertTrue(result["privacy_contract"]["metadata_only"])


if __name__ == "__main__":
    unittest.main()
