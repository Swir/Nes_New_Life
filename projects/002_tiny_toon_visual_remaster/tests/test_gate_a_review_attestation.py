from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
SPEC = importlib.util.spec_from_file_location("gate_a_review_attestation", TOOLS / "gate_a_review_attestation.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def matrix(statuses=None, fingerprint="abc123"):
    statuses = statuses or ["EVIDENCE_READY_FOR_REVIEW"] * 12
    criteria = []
    for index in range(1, 13):
        criteria.append({
            "index": index,
            "criterion": f"Criterion {index}",
            "mission_key": f"mission_{index}",
            "status": statuses[index - 1],
            "reason": "synthetic",
            "capture_fingerprint_sha256": fingerprint,
            "source_fingerprint_sha256": fingerprint,
        })
    return {
        "schema": MODULE.MATRIX_SCHEMA,
        "capture_fingerprint_sha256": fingerprint,
        "criteria": criteria,
    }


class GateAReviewAttestationTests(unittest.TestCase):
    def test_prepare_never_counts_evidence_ready_as_completion(self):
        data = matrix()
        ledger = MODULE._empty_ledger("abc123")
        result = MODULE.build_review(data, ledger)
        self.assertEqual(result["summary"]["verified_gate_a"], 0)
        self.assertEqual(result["summary"]["awaiting_human_attestation"], 12)
        self.assertEqual(result["roadmap_patch_preview"]["projected_completed_over_52"], 0)
        self.assertEqual(result["roadmap_patch_preview"]["projected_percent"], 0.0)

    def test_attestation_requires_exact_confirmation(self):
        data = matrix()
        ledger = MODULE._empty_ledger("abc123")
        with self.assertRaises(MODULE.ReviewError):
            MODULE.attest(data, ledger, 1, "yes", "local-operator")

    def test_blocked_evidence_cannot_be_attested(self):
        statuses = ["BLOCKED_CAPTURE_INTEGRITY"] + ["EVIDENCE_READY_FOR_REVIEW"] * 11
        data = matrix(statuses)
        ledger = MODULE._empty_ledger("abc123")
        with self.assertRaises(MODULE.ReviewError):
            MODULE.attest(data, ledger, 1, MODULE.CONFIRMATION, "local-operator")

    def test_verified_attestation_updates_preview_only(self):
        data = matrix()
        ledger = MODULE._empty_ledger("abc123")
        ledger = MODULE.attest(data, ledger, 1, MODULE.CONFIRMATION, "local-operator")
        result = MODULE.build_review(data, ledger)
        self.assertEqual(result["summary"]["verified_gate_a"], 1)
        self.assertEqual(result["roadmap_patch_preview"]["verified_gate_a_indexes"], [1])
        self.assertEqual(result["roadmap_patch_preview"]["projected_completed_over_52"], 1)
        self.assertEqual(result["roadmap_patch_preview"]["projected_remaining_over_52"], 51)
        self.assertEqual(result["roadmap_patch_preview"]["projected_percent"], 1.9)

    def test_stale_fingerprint_ledger_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ledger.json"
            path.write_text(json.dumps(MODULE._empty_ledger("old")), encoding="utf-8")
            with self.assertRaises(MODULE.ReviewError):
                MODULE._load_ledger(path, "new")

    def test_outputs_are_metadata_only_and_no_roadmap_is_modified(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            roadmap = root / "ROADMAP.md"
            roadmap.write_text("- [ ] protected\n", encoding="utf-8")
            data = matrix()
            ledger = MODULE._empty_ledger("abc123")
            review = MODULE.build_review(data, ledger)
            outputs = MODULE.write_outputs(review, ledger, root / "Reports")
            self.assertEqual(roadmap.read_text(encoding="utf-8"), "- [ ] protected\n")
            payload = Path(outputs["review"]).read_text(encoding="utf-8")
            self.assertNotIn(str(root.resolve()), payload)
            self.assertIn("AWAITING_HUMAN_ATTESTATION", payload)


if __name__ == "__main__":
    unittest.main()
