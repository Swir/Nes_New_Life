from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
SPEC = importlib.util.spec_from_file_location("capture_review_director", TOOLS / "capture_review_director.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def review(statuses=None, fingerprint="capture-fp"):
    statuses = statuses or {}
    criteria = []
    for index in range(1, 13):
        status = statuses.get(index, MODULE.BLOCKED)
        criteria.append({
            "index": index,
            "criterion": f"Criterion {index}",
            "mission_key": f"MISSION_{index}",
            "evidence_status": "EVIDENCE_READY_FOR_REVIEW" if status in {MODULE.READY, MODULE.VERIFIED} else "BLOCKED",
            "review_status": status,
            "capture_fingerprint_sha256": fingerprint,
            "source_fingerprint_sha256": fingerprint if status in {MODULE.READY, MODULE.VERIFIED} else "",
            "next_action": f"Capture criterion {index}",
        })
    return {
        "schema": MODULE.REVIEW_SCHEMA,
        "capture_fingerprint_sha256": fingerprint,
        "criteria": criteria,
    }


class CaptureReviewDirectorTests(unittest.TestCase):
    def test_reviewable_criterion_is_next_even_when_earlier_row_is_blocked(self):
        result = MODULE.build_director(review({3: MODULE.READY, 6: MODULE.VERIFIED}))
        self.assertEqual(result["state"], "REVIEW_REQUIRED")
        self.assertEqual(result["next_action"]["index"], 3)
        self.assertEqual(result["summary"], {"verified": 1, "reviewable": 1, "blocked": 10, "total": 12})

    def test_blocked_state_returns_to_capture(self):
        result = MODULE.build_director(review())
        self.assertEqual(result["state"], "CAPTURE_WORK_REQUIRED")
        self.assertEqual(result["next_action"]["kind"], "RETURN_TO_CAPTURE")
        self.assertEqual(result["next_action"]["index"], 1)

    def test_all_verified_hands_off_to_roadmap_patch(self):
        statuses = {index: MODULE.VERIFIED for index in range(1, 13)}
        result = MODULE.build_director(review(statuses))
        self.assertEqual(result["state"], "GATE_A_REVIEW_COMPLETE")
        self.assertEqual(result["summary"]["verified"], 12)
        self.assertEqual(result["next_action"]["kind"], "ROADMAP_PATCH_READY")

    def test_stale_row_fingerprint_fails_closed(self):
        payload = review({1: MODULE.READY})
        payload["criteria"][0]["capture_fingerprint_sha256"] = "old-fp"
        with self.assertRaises(MODULE.DirectorError):
            MODULE.build_director(payload)

    def test_outputs_are_metadata_only_and_do_not_touch_roadmap(self):
        result = MODULE.build_director(review({2: MODULE.READY}))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            roadmap = root / "ROADMAP.md"
            roadmap.write_text("unchanged", encoding="utf-8")
            outputs = MODULE.write_outputs(result, root / "Reports")
            self.assertEqual(roadmap.read_text(encoding="utf-8"), "unchanged")
            payload = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["capture_fingerprint_sha256"], "capture-fp")
            self.assertNotIn("rom", json.dumps(payload).lower())


if __name__ == "__main__":
    unittest.main()
