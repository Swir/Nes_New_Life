from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / "tools"
WINDOWS = Path(__file__).resolve().parents[1] / "windows"
sys.path.insert(0, str(TOOLS))

import evidence_bound_art_handoff as handoff


def gate_review_payload(fp: str, verified: int) -> tuple[dict, dict]:
    criteria = []
    attestations = []
    for index in range(1, 13):
        if index <= verified:
            status = "VERIFIED_GATE_A"
            source_fp = fp
            evidence = "EVIDENCE_READY_FOR_REVIEW"
            attestations.append({
                "index": index,
                "criterion": f"Criterion {index}",
                "mission_key": f"mission_{index}",
                "confirmation": "VERIFIED_GATE_A",
                "reviewer": "local",
                "capture_fingerprint_sha256": fp,
                "source_fingerprint_sha256": fp,
            })
        else:
            status = "BLOCKED_BY_EVIDENCE"
            source_fp = ""
            evidence = "BLOCKED"
        criteria.append({
            "index": index,
            "criterion": f"Criterion {index}",
            "mission_key": f"mission_{index}",
            "evidence_status": evidence,
            "review_status": status,
            "capture_fingerprint_sha256": fp,
            "source_fingerprint_sha256": source_fp,
            "next_action": "capture more",
        })
    return (
        {
            "schema": handoff.GATE_REVIEW_SCHEMA,
            "capture_fingerprint_sha256": fp,
            "criteria": criteria,
        },
        {
            "schema": handoff.GATE_REVIEW_SCHEMA,
            "capture_fingerprint_sha256": fp,
            "attestations": attestations,
        },
    )


class EvidenceBoundArtHandoffTests(unittest.TestCase):
    def review(self, *, state: str = "REVIEW_REQUIRED", fp: str = "abc", verified: int = 4):
        return {
            "schema": handoff.REVIEW_SCHEMA,
            "state": state,
            "capture_fingerprint_sha256": fp,
            "summary": {"verified": verified, "reviewable": 0, "blocked": 12 - verified},
        }

    def acceptance(self, *, fp: str = "abc", blockers=None):
        return {"capture_fingerprint_sha256": fp, "acceptance_gate": "BLOCKED", "hard_blockers": blockers or []}

    def test_rejects_stale_review_fingerprint(self):
        gate_review, ledger = gate_review_payload("old", 4)
        with self.assertRaisesRegex(handoff.HandoffError, "STALE REVIEW"):
            handoff.validate_binding(
                self.review(fp="old"),
                self.acceptance(fp="new"),
                gate_review,
                ledger,
            )

    def test_rejects_unsafe_capture_even_when_fingerprint_matches(self):
        gate_review, ledger = gate_review_payload("abc", 4)
        blockers = [{"kind": "CAPTURE_REGRESSION", "detail": "removed tile"}]
        with self.assertRaisesRegex(handoff.HandoffError, "Unsafe capture evidence"):
            handoff.validate_binding(
                self.review(),
                self.acceptance(blockers=blockers),
                gate_review,
                ledger,
            )

    def test_full_review_requires_all_12_ledger_backed_attestations(self):
        fp = "f" * 64
        gate_review, ledger = gate_review_payload(fp, 12)
        result = handoff.validate_binding(
            self.review(state="GATE_A_REVIEW_COMPLETE", fp=fp, verified=12),
            self.acceptance(fp=fp),
            gate_review,
            ledger,
        )
        self.assertTrue(result["gate_a_review_complete"])
        self.assertEqual(result["verified_gate_a"], 12)
        self.assertEqual(result["mode"], "FULL_GATE_A_HANDOFF")

        ledger["attestations"].pop()
        with self.assertRaisesRegex(handoff.HandoffError, "without matching ledger evidence"):
            handoff.validate_binding(
                self.review(state="GATE_A_REVIEW_COMPLETE", fp=fp, verified=12),
                self.acceptance(fp=fp),
                gate_review,
                ledger,
            )

    def test_director_verified_count_must_match_ledger(self):
        fp = "g" * 64
        gate_review, ledger = gate_review_payload(fp, 3)
        with self.assertRaisesRegex(handoff.HandoffError, "verified count"):
            handoff.validate_binding(
                self.review(fp=fp, verified=4),
                self.acceptance(fp=fp),
                gate_review,
                ledger,
            )

    def _write_gate_files(self, root: Path, fp: str, verified: int) -> Path:
        gate_review, ledger = gate_review_payload(fp, verified)
        gate_dir = root / "Reports" / "GateAReviewAttestation"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "GATE_A_REVIEW_HANDOFF.json").write_text(json.dumps(gate_review), encoding="utf-8")
        (gate_dir / "GATE_A_ATTESTATIONS.json").write_text(json.dumps(ledger), encoding="utf-8")
        review_json = root / "Reports" / "CaptureReviewDirector" / "CAPTURE_REVIEW_DIRECTOR.json"
        review_json.parent.mkdir(parents=True, exist_ok=True)
        state = "GATE_A_REVIEW_COMPLETE" if verified == 12 else "CAPTURE_WORK_REQUIRED"
        review_json.write_text(json.dumps(self.review(state=state, fp=fp, verified=verified)), encoding="utf-8")
        return review_json

    def test_strict_full_mode_blocks_before_production(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture = root / "capture"
            capture.mkdir()
            fp = "h" * 64
            review_json = self._write_gate_files(root, fp, 2)
            with patch.object(handoff, "build_acceptance_manifest", return_value=self.acceptance(fp=fp)), \
                 patch.object(handoff, "run_director") as director, \
                 patch.object(handoff, "run_autopilot") as autopilot:
                with self.assertRaisesRegex(handoff.HandoffError, "Strict handoff"):
                    handoff.run_handoff(root, capture, review_json, require_full_gate_a=True)
            director.assert_not_called()
            autopilot.assert_not_called()

    def test_safe_incremental_path_uses_official_director_and_art_autopilot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture = root / "capture"
            capture.mkdir()
            fp = "i" * 64
            review_json = self._write_gate_files(root, fp, 3)
            director = {
                "acceptance": {"capture_fingerprint_sha256": fp},
                "decision": {"production_decision": "SAFE_INCREMENTAL_ART"},
                "promotion": {"promotion_gate": "PROMOTED"},
            }
            art = {
                "allowed": True,
                "status": "HIGH_IMPACT_SPRINT_READY",
                "visual_completion": {"captured_unfinished": 20, "next_batch_count": 12},
                "sprint": {"status": "READY", "exported": 12},
                "next_action": "edit the exact batch",
            }
            with patch.object(handoff, "build_acceptance_manifest", return_value=self.acceptance(fp=fp)), \
                 patch.object(handoff, "run_director", return_value=director) as director_mock, \
                 patch.object(handoff, "run_autopilot", return_value=art) as autopilot_mock:
                result = handoff.run_handoff(root, capture, review_json, batch_size=12)
            self.assertEqual(result["binding"]["mode"], "SAFE_INCREMENTAL_ART_HANDOFF")
            self.assertEqual(result["production_decision"], "SAFE_INCREMENTAL_ART")
            self.assertEqual(result["art"]["next_batch_count"], 12)
            director_mock.assert_called_once()
            autopilot_mock.assert_called_once()

    def test_production_fingerprint_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture = root / "capture"
            capture.mkdir()
            fp = "j" * 64
            review_json = self._write_gate_files(root, fp, 1)
            director = {
                "acceptance": {"capture_fingerprint_sha256": "k" * 64},
                "decision": {"production_decision": "SAFE_INCREMENTAL_ART"},
                "promotion": {"promotion_gate": "PROMOTED"},
            }
            with patch.object(handoff, "build_acceptance_manifest", return_value=self.acceptance(fp=fp)), \
                 patch.object(handoff, "run_director", return_value=director):
                with self.assertRaisesRegex(handoff.HandoffError, "fingerprint changed"):
                    handoff.run_handoff(root, capture, review_json)

    def test_report_is_metadata_only_and_has_no_absolute_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = {
                "schema": handoff.SCHEMA,
                "status": "ART_HANDOFF_READY",
                "binding": {
                    "mode": "SAFE_INCREMENTAL_ART_HANDOFF",
                    "capture_fingerprint_sha256": "a" * 64,
                    "verified_gate_a": 3,
                    "reviewable_gate_a": 0,
                    "blocked_gate_a": 9,
                },
                "production_decision": "SAFE_INCREMENTAL_ART",
                "promotion_gate": "PROMOTED",
                "art": {"status": "HIGH_IMPACT_SPRINT_READY", "captured_unfinished": 20, "next_batch_count": 12},
                "active_family": None,
                "next_action": "edit batch",
                "privacy_contract": {"metadata_only": True, "absolute_local_paths": False},
            }
            outputs = handoff._write_outputs(result, root)
            payload = json.loads((root / outputs["json"]).read_text(encoding="utf-8"))
            self.assertNotIn(str(root.resolve()), json.dumps(payload))
            self.assertTrue(payload["privacy_contract"]["metadata_only"])

    def test_windows_launcher_and_authoritative_studio_are_wired(self):
        launcher = (WINDOWS / "Evidence_Bound_Art_Handoff.ps1").read_text(encoding="utf-8")
        studio = (TOOLS / "AuthoritativeProductionStudio.py").read_text(encoding="utf-8")
        self.assertIn("capture-session.json", launcher)
        self.assertIn("Capture_Review_Director.ps1", launcher)
        self.assertIn("ACTIVE_FAMILY_WORKBENCH", launcher)
        self.assertIn("Evidence_Bound_Art_Handoff.bat", studio)
        self.assertIn("<Control-Shift-F11>", studio)


if __name__ == "__main__":
    unittest.main()
