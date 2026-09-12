from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from capture_evidence_triage import build_triage, render_markdown  # noqa: E402
from local_capture_bridge import SCHEMA  # noqa: E402


def _evidence(*, fingerprint: str, regressions: int = 0, scale: int = 4, missing_image: bool = False, done: int = 2, conditions=None, tiles=None):
    conditions = conditions or ["hero_player_idle", "boss_final_attack_1", "hud_status"]
    tiles = tiles or ["2E", "2F", "30"]
    return {
        "schema": SCHEMA,
        "generated_utc": "2026-09-12T20:00:00+00:00",
        "privacy_contract": {
            "contains_rom": False,
            "contains_save_state": False,
            "contains_capture_pixels": False,
            "contains_emulator_binary": False,
            "contains_absolute_local_paths": False,
            "metadata_only": True,
        },
        "hd_pack": {
            "scale": scale,
            "warnings": [],
            "hires_sha256": "a" * 64,
            "capture_fingerprint": fingerprint,
            "mapping_count": 8,
            "unique_tile_ids": len(tiles),
            "unique_palettes": 2,
            "condition_count": len(conditions),
            "groups": {"PLAYER": 3, "BOSS": 2, "ENEMY": 1, "WORLD": 1, "UI": 1, "EFFECTS": 0, "UNASSIGNED": 0},
            "tile_ids": tiles,
            "palettes": ["FF16360F", "FF27160F"],
            "condition_names": conditions,
            "images": [{"name": "tiles.png", "present": not missing_image, "bytes": 1234, "sha256": "b" * 64, "width": 64, "height": 64, "mode": "RGBA"}],
        },
        "capture_missions": {"gate": "BLOCKED", "done": done, "total": 12, "percent": round(done / 12 * 100, 1)},
        "capture_gap": {
            "regressions": regressions,
            "progressed": True,
            "next": [{"priority": 95, "kind": "CAPTURE_MISSION", "group": "", "target": "ending_credits"}],
        },
        "release_claim": "NO CLAIM — local evidence must still satisfy authoritative Gate A–D review.",
    }


class CaptureEvidenceTriageTests(unittest.TestCase):
    def test_clean_incremental_evidence_passes_without_claiming_release(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "one.json").write_text(json.dumps(_evidence(fingerprint="1" * 64)), encoding="utf-8")
            result = build_triage(root)
            self.assertEqual(result["evidence_gate"], "PASS_INCREMENTAL")
            self.assertEqual(result["release_capture_gate"], "BLOCKED")
            self.assertEqual(result["next_action"]["kind"], "CAPTURE_MISSION")
            self.assertTrue(any(row["gate_a_item"] == "boss_phases_attacks_death_effects" and row["status"] == "CANDIDATE_REVIEW" for row in result["gate_a_candidates"]))
            self.assertIn("auto-completes", result["roadmap_policy"].lower())

    def test_explicit_regression_blocks_evidence_baseline(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "one.json").write_text(json.dumps(_evidence(fingerprint="2" * 64, regressions=3)), encoding="utf-8")
            result = build_triage(root)
            self.assertEqual(result["evidence_gate"], "BLOCKED")
            self.assertEqual(result["next_action"]["kind"], "RECAPTURE_REGRESSION")

    def test_missing_referenced_image_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "one.json").write_text(json.dumps(_evidence(fingerprint="3" * 64, missing_image=True)), encoding="utf-8")
            result = build_triage(root)
            self.assertEqual(result["evidence_gate"], "BLOCKED")
            self.assertEqual(result["next_action"]["kind"], "REPAIR_CAPTURE")

    def test_history_delta_reports_growth_and_loss_without_auto_check(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = _evidence(fingerprint="4" * 64, done=1, conditions=["hero_player_idle"], tiles=["2E"])
            second = _evidence(fingerprint="5" * 64, done=3, conditions=["hero_player_idle", "hero_player_jump", "boss_final_attack_1"], tiles=["2E", "2F", "30"])
            second["generated_utc"] = "2026-09-12T21:00:00+00:00"
            (root / "a.json").write_text(json.dumps(first), encoding="utf-8")
            (root / "b.json").write_text(json.dumps(second), encoding="utf-8")
            result = build_triage(root)
            self.assertEqual(result["deltas"][0]["mission_done_delta"], 2)
            self.assertEqual(result["deltas"][0]["added_tile_ids"], ["2F", "30"])
            markdown = render_markdown(result)
            self.assertIn("signals only", markdown.lower())
            self.assertNotIn("[x]", markdown)


if __name__ == "__main__":
    unittest.main()
