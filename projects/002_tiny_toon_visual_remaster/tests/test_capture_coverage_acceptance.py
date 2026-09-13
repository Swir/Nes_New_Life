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

from capture_coverage_acceptance import build_acceptance_manifest, write_outputs  # noqa: E402
from capture_mission_control import MISSION_ITEMS  # noqa: E402
from guided_capture_marathon import ATTESTATION, confirm_mission  # noqa: E402


class CaptureCoverageAcceptanceTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path, *, omit_effects: bool = False) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        for y in range(64):
            for x in range(64):
                image.putpixel((x, y), ((x * 3) % 255, (y * 5) % 255, 170, 255))
        image.save(folder / "tiles.png")
        lines = [
            "<ver>106",
            "<scale>4",
            "<img>tiles.png",
            "[hero_player_idle]<tile>0,20,FF16360F,0,0,1,N",
            "[hero_player_walk]<tile>0,21,FF16360F,8,0,1,N",
            "[boss_final_idle]<tile>0,22,FF27160F,16,0,1,N",
            "[enemy_common_walk]<tile>0,23,FF16360F,24,0,1,N",
            "[world_stage_ground]<tile>0,24,FF16360F,32,0,1,N",
            "[hud_status]<tile>0,25,FF16360F,40,0,1,N",
            "<condition>hero_player_idle,tileNearby,8,0,20,FF16360F",
            "<condition>boss_final_idle,tileNearby,8,0,22,FF27160F",
        ]
        if not omit_effects:
            lines.append("[effect_projectile]<tile>0,26,FF16360F,48,0,1,N")
        (folder / "hires.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_pending_real_gameplay_evidence_blocks_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            capture = root / "capture"
            project.mkdir()
            self._write_pack(capture)

            result = build_acceptance_manifest(project, capture)

            self.assertEqual(result["acceptance_gate"], "BLOCKED")
            self.assertEqual(result["mission_summary"]["verified"], 0)
            self.assertEqual(result["mission_summary"]["pending"], len(MISSION_ITEMS))
            self.assertTrue(any(row["kind"] == "MISSION_COVERAGE" for row in result["hard_blockers"]))
            self.assertNotIn("[x]", json.dumps(result))

    def test_every_confirmed_mission_is_bound_to_capture_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            capture = root / "capture"
            project.mkdir()
            self._write_pack(capture)

            for key, *_ in MISSION_ITEMS:
                confirm_mission(project / "CAPTURE_MISSIONS.json", capture, key, attestation=ATTESTATION)

            result = build_acceptance_manifest(project, capture)
            fingerprint = result["capture_fingerprint_sha256"]

            self.assertEqual(result["acceptance_gate"], "READY_FOR_GATE_A_REVIEW")
            self.assertEqual(result["mission_summary"]["verified"], len(MISSION_ITEMS))
            self.assertEqual(result["mission_summary"]["pending"], 0)
            self.assertEqual(result["mission_summary"]["untrusted_completed"], 0)
            self.assertEqual(result["hard_blockers"], [])
            self.assertEqual(len(fingerprint), 64)
            for mission in result["missions"]:
                self.assertEqual(mission["status"], "VERIFIED_IN_GAME")
                self.assertEqual(len(mission["source_fingerprint_sha256"]), 64)

    def test_required_group_without_capture_signal_is_hard_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            capture = root / "capture"
            project.mkdir()
            self._write_pack(capture, omit_effects=True)

            result = build_acceptance_manifest(project, capture)
            group_blockers = [row for row in result["hard_blockers"] if row["kind"] == "GROUP_SIGNAL"]

            self.assertEqual(result["acceptance_gate"], "BLOCKED")
            self.assertTrue(group_blockers)
            self.assertIn("EFFECTS", group_blockers[0]["detail"])

    def test_reports_are_metadata_only_and_do_not_embed_local_paths_or_png(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            capture = root / "private_capture"
            output = root / "reports"
            project.mkdir()
            self._write_pack(capture)

            result = build_acceptance_manifest(project, capture)
            outputs = write_outputs(result, output)

            self.assertEqual(list(output.glob("*.png")), [])
            raw = Path(outputs["json"]).read_text(encoding="utf-8")
            self.assertNotIn(str(capture), raw)
            self.assertNotIn(str(project), raw)
            self.assertTrue(result["privacy_contract"]["metadata_only"])
            self.assertFalse(result["privacy_contract"]["contains_capture_pixels"])

    def test_fingerprint_changes_when_runtime_capture_changes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = root / "project"
            capture = root / "capture"
            project.mkdir()
            self._write_pack(capture)
            before = build_acceptance_manifest(project, capture)["capture_fingerprint_sha256"]

            with Image.open(capture / "tiles.png") as image:
                changed = image.copy()
            changed.putpixel((63, 63), (255, 0, 255, 255))
            changed.save(capture / "tiles.png")
            after = build_acceptance_manifest(project, capture)["capture_fingerprint_sha256"]

            self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()
