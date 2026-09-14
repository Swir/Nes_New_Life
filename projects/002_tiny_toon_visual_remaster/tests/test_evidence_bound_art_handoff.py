import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import evidence_bound_art_handoff as handoff


class EvidenceBoundArtHandoffTests(unittest.TestCase):
    def review(self, state="REVIEW_REQUIRED", fp="abc"):
        return {"schema": handoff.REVIEW_SCHEMA, "state": state, "capture_fingerprint_sha256": fp, "summary": {"verified": 4, "reviewable": 3, "blocked": 5}}

    def acceptance(self, fp="abc", blockers=None):
        return {"capture_fingerprint_sha256": fp, "acceptance_gate": "BLOCKED", "hard_blockers": blockers or []}

    def test_rejects_stale_review_fingerprint(self):
        with self.assertRaisesRegex(handoff.HandoffError, "STALE REVIEW"):
            handoff.validate_binding(self.review(fp="old"), self.acceptance(fp="new"))

    def test_rejects_unsafe_capture_even_when_fingerprint_matches(self):
        blockers = [{"kind": "CAPTURE_REGRESSION", "detail": "removed tile"}]
        with self.assertRaisesRegex(handoff.HandoffError, "Unsafe capture evidence"):
            handoff.validate_binding(self.review(), self.acceptance(blockers=blockers))

    def test_full_review_selects_full_handoff_mode(self):
        result = handoff.validate_binding(self.review(state="GATE_A_REVIEW_COMPLETE"), self.acceptance())
        self.assertTrue(result["gate_a_review_complete"])
        self.assertEqual(result["mode"], "FULL_GATE_A_HANDOFF")

    def test_orchestrator_binds_promotion_and_prepares_exact_sprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_json = root / "review.json"
            review_json.write_text(__import__("json").dumps(self.review()), encoding="utf-8")
            capture = root / "capture"
            capture.mkdir()
            (root / "Artwork").mkdir()
            with patch.object(handoff, "build_acceptance_manifest", return_value=self.acceptance()), \
                 patch.object(handoff, "promote_capture", return_value={"promotion_gate": "PROMOTED", "capture_regressions": 0, "coverage_acceptance": {"promotion_admission": {"capture_fingerprint_sha256": "abc", "mode": "INCREMENTAL_CAPTURE_READY"}}}), \
                 patch.object(handoff, "prepare_high_impact_sprint", return_value={"status": "READY", "exported": 12, "missing": 0, "matrix": {"overall_weighted_percent": 25.0}}) as sprint:
                result = handoff.run_handoff(root, capture, review_json, batch_size=12)
            self.assertEqual(result["status"], "ART_HANDOFF_READY")
            self.assertEqual(result["binding"]["mode"], "SAFE_INCREMENTAL_ART_HANDOFF")
            self.assertEqual(result["art_sprint"]["exported"], 12)
            sprint.assert_called_once()
            self.assertTrue((root / "Reports" / "EvidenceBoundArtHandoff" / "EVIDENCE_BOUND_ART_HANDOFF.json").is_file())


if __name__ == "__main__":
    unittest.main()
