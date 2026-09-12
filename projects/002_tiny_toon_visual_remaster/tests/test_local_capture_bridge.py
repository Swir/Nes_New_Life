from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from capture_evidence_validator import validate_evidence, validate_evidence_tree  # noqa: E402
from capture_mission_control import record_session  # noqa: E402
from guided_capture_marathon import ATTESTATION, confirm_mission  # noqa: E402
from local_capture_bridge import build_safe_evidence, write_safe_handoff  # noqa: E402


class LocalCaptureBridgeTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path, *, boss: bool = True) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        for y in range(32):
            for x in range(32):
                image.putpixel((x, y), (80, 180, 230, 255))
        if boss:
            for y in range(32, 64):
                for x in range(32, 64):
                    image.putpixel((x, y), (220, 70, 80, 255))
        image.save(folder / "tiles.png")
        lines = [
            "<ver>106",
            "<scale>4",
            "<img>tiles.png",
            "[hero_player_idle]<tile>0,2E,FF16360F,0,0,1,N",
            "[hero_player_walk_1]<tile>0,2F,FF16360F,32,0,1,N",
            "<condition>hero_player_idle,tileNearby,8,0,2E,FF16360F",
            "<condition>hero_player_walk_1,tileNearby,8,0,2F,FF16360F",
        ]
        if boss:
            lines.extend([
                "[boss_final_idle]<tile>0,30,FF27160F,0,32,1,N",
                "[boss_final_attack_1]<tile>0,31,FF27160F,32,32,1,N",
                "<condition>boss_final_idle,tileNearby,8,0,30,FF27160F",
                "<condition>boss_final_attack_1,tileNearby,8,0,31,FF27160F",
            ])
        (folder / "hires.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_generated_handoff_is_metadata_only_and_valid(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            capture = root / "capture"
            out = root / "handoff"
            project.mkdir()
            self._write_pack(capture)

            evidence = build_safe_evidence(project, capture)
            outputs = write_safe_handoff(evidence, out)

            self.assertEqual(validate_evidence(evidence), [])
            self.assertEqual(validate_evidence_tree(Path(outputs["json"])), [])
            self.assertTrue(evidence["privacy_contract"]["metadata_only"])
            self.assertFalse(evidence["privacy_contract"]["contains_capture_pixels"])
            self.assertGreaterEqual(evidence["hd_pack"]["groups"]["PLAYER"], 2)
            self.assertGreaterEqual(evidence["hd_pack"]["groups"]["BOSS"], 2)
            self.assertEqual(evidence["capture_integrity"]["admission_gate"], "PASS")
            self.assertEqual(
                evidence["hd_pack"]["capture_fingerprint"],
                evidence["capture_integrity"]["capture_fingerprint_sha256"],
            )
            self.assertEqual(evidence["capture_integrity"]["mission_evidence"]["verified_done"], 0)
            self.assertEqual(list(out.glob("*.png")), [])
            raw = Path(outputs["json"]).read_text(encoding="utf-8")
            self.assertNotIn(str(capture), raw)
            self.assertNotIn(str(project), raw)

    def test_guided_verified_mission_is_bound_into_safe_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            capture = root / "capture"
            project.mkdir()
            self._write_pack(capture)
            manifest = project / "CAPTURE_MISSIONS.json"

            confirmed = confirm_mission(manifest, capture, "boot_title_menu", attestation=ATTESTATION)
            evidence = build_safe_evidence(project, capture)
            mission = evidence["capture_integrity"]["mission_evidence"]

            self.assertEqual(evidence["capture_missions"]["done"], 1)
            self.assertEqual(mission["done"], 1)
            self.assertEqual(mission["verified_done"], 1)
            self.assertEqual(mission["unverified_done"], [])
            self.assertEqual(len(mission["bindings"]), 1)
            self.assertTrue(mission["bindings"][0]["verified_in_game"])
            self.assertTrue(mission["bindings"][0]["same_as_current_capture"])
            self.assertEqual(
                mission["bindings"][0]["capture_fingerprint_sha256"],
                confirmed["capture_integrity"]["fingerprint_sha256"],
            )

    def test_manual_completed_mission_without_attestation_is_not_transport_trusted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            capture = root / "capture"
            project.mkdir()
            self._write_pack(capture)
            manifest = project / "CAPTURE_MISSIONS.json"
            record_session(manifest, capture, ["boot_title_menu"], "manual legacy record")

            evidence = build_safe_evidence(project, capture)
            mission = evidence["capture_integrity"]["mission_evidence"]
            self.assertEqual(mission["verified_done"], 0)
            self.assertEqual(mission["unverified_done"], ["boot_title_menu"])
            self.assertFalse(mission["bindings"][0]["verified_in_game"])

    def test_regressed_capture_reports_regression_without_copying_pixels(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            previous = root / "previous"
            current = root / "current"
            project.mkdir()
            self._write_pack(previous, boss=True)
            self._write_pack(current, boss=False)

            evidence = build_safe_evidence(project, current, previous_capture=previous)

            self.assertGreater(evidence["capture_gap"]["regressions"], 0)
            self.assertTrue(any(row["kind"] == "CAPTURE_REGRESSION" for row in evidence["capture_gap"]["next"]))
            self.assertEqual(validate_evidence(evidence), [])

    def test_validator_blocks_absolute_paths_and_payload_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            capture = root / "capture"
            out = root / "evidence"
            project.mkdir()
            self._write_pack(capture)
            evidence = build_safe_evidence(project, capture)
            evidence["leak"] = "C:\\Users\\Example\\game.nes"
            self.assertTrue(any("absolute local path" in error for error in validate_evidence(evidence)))

            clean = build_safe_evidence(project, capture)
            write_safe_handoff(clean, out)
            (out / "forbidden.png").write_bytes(b"not an image")
            errors = validate_evidence_tree(out)
            self.assertTrue(any("forbidden payload file" in error for error in errors))


if __name__ == "__main__":
    unittest.main()