from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
WINDOWS = PROJECT / "windows"
sys.path.insert(0, str(TOOLS))

import regression_capture_gap_retest as retest


class RegressionCaptureGapRetestTests(unittest.TestCase):
    def _write_history(self, root: Path, fp: str = "source-runtime", case: str = "bosses") -> None:
        (root / "FINAL_REGRESSION.json").write_text(json.dumps({
            "history": [{
                "case": case,
                "result": "FAIL",
                "failure_category": "CAPTURE_GAP",
                "pack_fingerprint": fp,
            }]
        }), encoding="utf-8")

    def _recovery_files(self, root: Path, *, case: str = "bosses") -> tuple[Path, Path]:
        token = root / "recovery-token.json"
        report = root / "recovery-report.json"
        token.write_text(json.dumps({
            "schema": retest.RECOVERY_TOKEN_SCHEMA,
            "case_key": case,
            "case_label": "Bosses",
            "source_runtime_fingerprint": "source-runtime",
            "source_capture_fingerprint": "capture-old",
            "target_mission_keys": ["bosses_all_phases"],
        }), encoding="utf-8")
        report.write_text(json.dumps({
            "status": "CAPTURE_RECOVERED_READY_FOR_HD_HANDOFF",
            "current_capture_fingerprint": "capture-new",
        }), encoding="utf-8")
        return token, report

    def test_prepare_requires_verified_recovery(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_history(root)
            token, report = self._recovery_files(root)
            report.write_text(json.dumps({"status": "CAPTURE_RECOVERY_BLOCKED", "current_capture_fingerprint": "capture-new"}), encoding="utf-8")
            with self.assertRaisesRegex(retest.CaptureGapRetestError, "not verified"):
                retest.prepare_retest(root, root / "candidate", token, report)

    def test_prepare_requires_original_authoritative_capture_gap_fail(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "FINAL_REGRESSION.json").write_text(json.dumps({"history": []}), encoding="utf-8")
            token, report = self._recovery_files(root)
            with patch.object(retest, "pack_fingerprint", return_value="repaired-runtime"):
                with self.assertRaisesRegex(retest.CaptureGapRetestError, "not backed"):
                    retest.prepare_retest(root, root / "candidate", token, report)

    def test_prepare_rejects_unchanged_runtime_after_art(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_history(root)
            token, report = self._recovery_files(root)
            with patch.object(retest, "pack_fingerprint", return_value="source-runtime"):
                with self.assertRaisesRegex(retest.CaptureGapRetestError, "did not change"):
                    retest.prepare_retest(root, root / "candidate", token, report)

    def test_prepare_binds_recovered_capture_to_repaired_runtime_and_same_case(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_history(root)
            token, report = self._recovery_files(root)
            with patch.object(retest, "pack_fingerprint", return_value="repaired-runtime"):
                result = retest.prepare_retest(root, root / "candidate", token, report, output_dir=root / "out")
            self.assertEqual("SAME_CASE_RETEST_READY", result["status"])
            self.assertEqual("bosses", result["case"]["key"])
            saved = json.loads((root / "out" / "REGRESSION_CAPTURE_GAP_RETEST_TOKEN.json").read_text(encoding="utf-8"))
            self.assertEqual("capture-new", saved["recovered_capture_fingerprint"])
            self.assertEqual("repaired-runtime", saved["repaired_runtime_fingerprint"])
            self.assertFalse(result["privacy_contract"]["capture_pixels"])

    def test_record_rejects_repaired_runtime_fingerprint_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_history(root)
            token_path = root / "token.json"
            token_path.write_text(json.dumps({
                "schema": retest.RETEST_TOKEN_SCHEMA,
                "case_key": "bosses",
                "case_label": "Bosses",
                "source_runtime_fingerprint": "source-runtime",
                "repaired_runtime_fingerprint": "expected-runtime",
            }), encoding="utf-8")
            with patch.object(retest, "pack_fingerprint", return_value="changed-runtime"):
                with self.assertRaisesRegex(retest.CaptureGapRetestError, "fingerprint changed"):
                    retest.record_retest(root, root / "candidate", token_path, "PASS")

    def test_pass_records_only_same_case_and_preserves_full_gate_requirement(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_history(root)
            token_path = root / "token.json"
            token_path.write_text(json.dumps({
                "schema": retest.RETEST_TOKEN_SCHEMA,
                "case_key": "bosses",
                "case_label": "Bosses",
                "source_runtime_fingerprint": "source-runtime",
                "repaired_runtime_fingerprint": "repaired-runtime",
            }), encoding="utf-8")
            after = {
                "gate": "BLOCKED",
                "counts": {"PASS": 1, "FAIL": 0, "STALE": 5, "PENDING": 4},
                "next_case": {"key": "boot_title_menu", "state": "STALE"},
            }
            with patch.object(retest, "pack_fingerprint", return_value="repaired-runtime"), \
                 patch.object(retest, "record_case_result", return_value={"case": "bosses", "result": "PASS"}) as recorder, \
                 patch.object(retest, "cockpit_status", return_value=after):
                result = retest.record_retest(root, root / "candidate", token_path, "PASS", output_dir=root / "out")
            recorder.assert_called_once()
            self.assertEqual("CAPTURE_GAP_RETEST_PASS", result["status"])
            self.assertEqual("BLOCKED", result["cockpit_gate"])
            self.assertIn("10/10", result["roadmap_policy"])

    def test_fail_records_remaining_category_for_authoritative_reroute(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_history(root)
            token_path = root / "token.json"
            token_path.write_text(json.dumps({
                "schema": retest.RETEST_TOKEN_SCHEMA,
                "case_key": "bosses",
                "case_label": "Bosses",
                "source_runtime_fingerprint": "source-runtime",
                "repaired_runtime_fingerprint": "repaired-runtime",
            }), encoding="utf-8")
            after = {"gate": "BLOCKED", "counts": {"PASS": 0, "FAIL": 1, "STALE": 0, "PENDING": 9}, "next_case": {"key": "bosses", "state": "FAIL"}}
            with patch.object(retest, "pack_fingerprint", return_value="repaired-runtime"), \
                 patch.object(retest, "record_case_result", return_value={"case": "bosses", "result": "FAIL"}) as recorder, \
                 patch.object(retest, "cockpit_status", return_value=after):
                result = retest.record_retest(root, root / "candidate", token_path, "FAIL", category="ANIMATION_SEAM", failure_notes="phase seam")
            self.assertEqual("CAPTURE_GAP_RETEST_FAIL", result["status"])
            self.assertEqual("ANIMATION_SEAM", recorder.call_args.kwargs["failure_category"])

    def test_windows_launcher_finishes_art_fullscreen_and_records_same_case(self):
        source = (WINDOWS / "Finish_Capture_Gap_Art_And_Retest.ps1").read_text(encoding="utf-8")
        self.assertIn("High_Impact_Art_Sprint.ps1", source)
        self.assertIn("-Finish", source)
        self.assertIn("launch_remaster.ps1", source)
        self.assertIn("Perform ONLY the SAME original CAPTURE_GAP case", source)
        self.assertIn("'record'", source)
        self.assertIn("verified-fullscreen MesenCE", source)


if __name__ == "__main__":
    unittest.main()
