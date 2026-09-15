from __future__ import annotations

import hashlib
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

import release_finalization_director as director  # noqa: E402


class ReleaseFinalizationDirectorTests(unittest.TestCase):
    def _audit(self, stage: str | None) -> dict:
        stages = []
        names = [
            "HD PACK STRUCTURE",
            "CAPTURE COVERAGE",
            "FINAL ART",
            "VISUAL CONTEXT",
            "PIXEL QA",
            "VERIFIED FULLSCREEN",
            "FINAL REGRESSION",
        ]
        for name in names:
            stages.append({"name": name, "gate": "BLOCKED" if name == stage else "PASS", "summary": name})
        next_stage = next((item for item in stages if item["gate"] != "PASS"), None)
        return {
            "release_gate": "PASS" if stage is None else "BLOCKED",
            "pack_fingerprint": "abc123fingerprint",
            "next_stage": next_stage,
            "blockers": [] if stage is None else [stage + " blocked"],
            "stages": stages,
        }

    def test_every_release_stage_has_one_concrete_route(self) -> None:
        expected = {
            "HD PACK STRUCTURE": ("REPAIR_HD_STRUCTURE", "Regression_Mapping_Repair.bat"),
            "CAPTURE COVERAGE": ("COMPLETE_CAPTURE", "Guided_Capture_Marathon.bat"),
            "FINAL ART": ("FINISH_FINAL_ART", "High_Impact_Art_Sprint.bat"),
            "VISUAL CONTEXT": ("REFRESH_VISUAL_CONTEXT", "Continue_HD_Art_Session.bat"),
            "PIXEL QA": ("REFRESH_PIXEL_QA", "Finish_High_Impact_Art_Sprint.bat"),
            "VERIFIED FULLSCREEN": ("REFRESH_FULLSCREEN", "Build_HD_Playtest.bat"),
            "FINAL REGRESSION": ("COMPLETE_FINAL_REGRESSION", "Auto_Continue_Final_Regression.bat"),
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; pack.mkdir()
            for stage, route in expected.items():
                with self.subTest(stage=stage), patch.object(director, "final_release_audit", return_value=self._audit(stage)):
                    plan = director.build_plan(root, pack)
                    self.assertEqual(route[0], plan["state"])
                    self.assertEqual(route[1], plan["launcher"])

    def test_all_green_is_package_ready_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; pack.mkdir()
            with patch.object(director, "final_release_audit", return_value=self._audit(None)):
                plan = director.build_plan(root, pack)
            self.assertEqual("PACKAGE_READY", plan["state"])
            self.assertEqual("PASS", plan["release_gate"])
            self.assertIsNone(plan["launcher"])

    def test_evidence_resolver_prefers_existing_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            alt = root / "Reports" / "TransactionalArtCommit" / "ART_QA_RESULT.json"
            alt.parent.mkdir(parents=True)
            alt.write_text("{}", encoding="utf-8")
            evidence = director.resolve_evidence(root)
            self.assertEqual(alt, evidence["art_qa"])
            self.assertEqual(root / "CAPTURE_MISSIONS.json", evidence["capture"])

    def test_release_manifest_hashes_only_finished_zip_and_declares_rom_free(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = root / "plan.json"
            archive = root / "TinyToon_HD.zip"
            output = root / "release.manifest.json"
            plan.write_text(json.dumps({"state": "PACKAGE_READY", "release_gate": "PASS", "pack_fingerprint": "fp-final"}), encoding="utf-8")
            payload = b"synthetic-public-hd-pack"
            archive.write_bytes(payload)
            manifest = director.write_release_manifest(plan, archive, output)
            self.assertEqual(hashlib.sha256(payload).hexdigest(), manifest["zip_sha256"])
            self.assertFalse(manifest["rom_included"])
            self.assertFalse(manifest["save_states_included"])
            self.assertFalse(manifest["emulator_binary_included"])
            self.assertTrue(output.is_file())

    def test_manifest_refuses_blocked_plan(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); plan = root / "plan.json"; archive = root / "x.zip"
            plan.write_text(json.dumps({"state": "COMPLETE_CAPTURE", "release_gate": "BLOCKED", "pack_fingerprint": "fp"}), encoding="utf-8")
            archive.write_bytes(b"x")
            with self.assertRaises(director.ReleaseFinalizationError):
                director.write_release_manifest(plan, archive, root / "manifest.json")

    def test_windows_finalizer_reaudits_before_packaging_and_routes_blockers(self) -> None:
        source = (WINDOWS / "Finalize_Release_Candidate.ps1").read_text(encoding="utf-8")
        self.assertIn("final_release_director.py", source)
        self.assertIn("'package'", source)
        self.assertIn("REPAIR_HD_STRUCTURE", source)
        self.assertIn("COMPLETE_FINAL_REGRESSION", source)
        self.assertIn("Re-auditing atomically immediately before packaging", source)
        self.assertIn("ROM-FREE RELEASE READY", source)

    def test_authoritative_studio_exposes_finalization_entrypoint(self) -> None:
        source = (TOOLS / "AuthoritativeProductionStudio.py").read_text(encoding="utf-8")
        self.assertIn("CTRL+ALT+F8  FINALIZE RELEASE CANDIDATE", source)
        self.assertIn("Finalize_Release_Candidate.bat", source)
        self.assertIn("<Control-Alt-F8>", source)


if __name__ == "__main__":
    unittest.main()
