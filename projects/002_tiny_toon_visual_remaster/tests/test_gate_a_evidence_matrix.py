from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from gate_a_evidence_matrix import MISSION_CRITERIA, build_matrix, write_outputs


def _acceptance(*, verified: set[str] | None = None, regression_count: int = 0, at_risk: list[str] | None = None) -> dict:
    verified = verified or set()
    missions = []
    for key, label in MISSION_CRITERIA:
        done = key in verified
        missions.append({
            "key": key,
            "label": label,
            "status": "VERIFIED_IN_GAME" if done else "PENDING",
            "verified_in_game": done,
            "source_fingerprint_sha256": f"fp-{key}" if done else "",
            "same_as_current_capture": done,
        })
    return {
        "schema": "swir.project002.capture-coverage-acceptance.v1",
        "capture_fingerprint_sha256": "current-fingerprint",
        "acceptance_gate": "READY_FOR_GATE_A_REVIEW" if len(verified) == len(MISSION_CRITERIA) and regression_count == 0 and not at_risk else "BLOCKED",
        "capture_integrity": {
            "admission_gate": "PASS",
            "integrity_gate": "PASS",
            "regression_count": regression_count,
            "structural_blockers": [],
            "at_risk_missions": at_risk or [],
        },
        "missions": missions,
    }


class GateAEvidenceMatrixTests(unittest.TestCase):
    def test_clean_verified_capture_makes_all_twelve_criteria_review_ready(self) -> None:
        result = build_matrix(_acceptance(verified={key for key, _ in MISSION_CRITERIA}))
        self.assertEqual(result["summary"], {"evidence_ready": 12, "remaining": 0, "total": 12})
        self.assertEqual(result["next_action"]["kind"], "MANUAL_GATE_A_CHECKLIST_REVIEW")
        self.assertTrue(all(row["status"] == "EVIDENCE_READY_FOR_REVIEW" for row in result["criteria"]))

    def test_pending_mission_never_becomes_ready(self) -> None:
        verified = {key for key, _ in MISSION_CRITERIA if key != "bosses_all_phases"}
        result = build_matrix(_acceptance(verified=verified))
        boss = next(row for row in result["criteria"] if row["mission_key"] == "bosses_all_phases")
        self.assertEqual(boss["status"], "PENDING_EVIDENCE")
        self.assertEqual(result["summary"]["evidence_ready"], 11)

    def test_regression_blocks_verified_mission_evidence_and_regression_criterion(self) -> None:
        result = build_matrix(_acceptance(verified={key for key, _ in MISSION_CRITERIA}, regression_count=2))
        self.assertTrue(all(row["status"] != "EVIDENCE_READY_FOR_REVIEW" for row in result["criteria"]))
        self.assertEqual(result["criteria"][-1]["status"], "PENDING_REGRESSION_REPAIR")

    def test_at_risk_mission_is_fail_closed(self) -> None:
        result = build_matrix(_acceptance(verified={key for key, _ in MISSION_CRITERIA}, at_risk=["rare_enemies"]))
        rare = next(row for row in result["criteria"] if row["mission_key"] == "rare_enemies")
        self.assertEqual(rare["status"], "BLOCKED_AT_RISK")
        self.assertEqual(result["criteria"][-1]["status"], "BLOCKED_AT_RISK")

    def test_outputs_are_metadata_only_and_do_not_touch_roadmap(self) -> None:
        result = build_matrix(_acceptance(verified={key for key, _ in MISSION_CRITERIA}))
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_outputs(result, Path(tmp))
            payload = Path(outputs["json"]).read_text(encoding="utf-8")
            self.assertNotIn("ROADMAP.md", payload)
            self.assertNotIn(".png", payload.lower())
            self.assertNotIn(".nes", payload.lower())
            loaded = json.loads(payload)
            self.assertEqual(loaded["schema"], "swir.project002.gate-a-evidence-matrix.v1")


if __name__ == "__main__":
    unittest.main()
