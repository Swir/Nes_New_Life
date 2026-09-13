from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from capture_mission_control import default_manifest  # noqa: E402
from route_capture_sequencer import build_session_plan, write_outputs  # noqa: E402


class RouteCaptureSequencerTests(unittest.TestCase):
    @staticmethod
    def _write_manifest(path: Path, completed: set[str] | None = None) -> None:
        data = default_manifest()
        completed = completed or set()
        for key in completed:
            data["missions"][key]["done"] = True
            data["missions"][key]["last_session"] = 1
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @staticmethod
    def _write_gap_plan(path: Path) -> None:
        path.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "queue": [
                        {
                            "priority": 1,
                            "score": 160,
                            "kind": "CAPTURE_REGRESSION",
                            "art_group": "BOSS",
                            "family": "BOSS_ALPHA",
                            "target": "restore previous coverage",
                            "reason": "coverage present in previous capture is absent now",
                        },
                        {
                            "priority": 2,
                            "score": 120,
                            "kind": "STATE_GAP",
                            "art_group": "PLAYER",
                            "family": "HERO",
                            "target": "trigger missing states",
                            "missing_expected_states": "jump | death",
                            "reason": "advisory state gap",
                        },
                        {
                            "priority": 3,
                            "score": 105,
                            "kind": "CLASSIFICATION_CAPTURE",
                            "art_group": "UNASSIGNED",
                            "family": "MIXED_1",
                            "target": "capture a clearer gameplay context",
                            "reason": "mixed family",
                        },
                    ],
                    "comparison": {"regressions": [{"family": "BOSS_ALPHA"}]},
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def test_all_pending_missions_are_assigned_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "CAPTURE_MISSIONS.json"
            self._write_manifest(manifest)
            plan = build_session_plan(manifest)
            self.assertEqual(plan["pending_mission_count"], 11)
            self.assertEqual(len(plan["mission_order"]), 11)
            self.assertEqual(len(set(plan["mission_order"])), 11)
            self.assertEqual(plan["planned_session_count"], 5)

    def test_completed_missions_are_removed_without_mutating_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "CAPTURE_MISSIONS.json"
            self._write_manifest(manifest, {"boot_title_menu", "ending_credits"})
            before = manifest.read_bytes()
            plan = build_session_plan(manifest)
            self.assertEqual(plan["pending_mission_count"], 9)
            self.assertNotIn("boot_title_menu", plan["mission_order"])
            self.assertNotIn("ending_credits", plan["mission_order"])
            self.assertEqual(before, manifest.read_bytes())

    def test_capture_regression_session_is_promoted_first(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "CAPTURE_MISSIONS.json"
            gap = root / "CAPTURE_GAP_PLAN.json"
            self._write_manifest(manifest)
            self._write_gap_plan(gap)
            plan = build_session_plan(manifest, gap)
            self.assertTrue(plan["capture_regression_present"])
            first = plan["sessions"][0]
            self.assertTrue(any(row["kind"] == "CAPTURE_REGRESSION" for row in first["gap_targets"]))
            self.assertEqual(first["session_key"], "boss_combat_sweep")

    def test_gap_targets_are_deduplicated_and_folded_into_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "CAPTURE_MISSIONS.json"
            gap = root / "CAPTURE_GAP_PLAN.json"
            self._write_manifest(manifest)
            self._write_gap_plan(gap)
            plan = build_session_plan(manifest, gap)
            signatures = []
            for session in plan["sessions"]:
                for row in session["gap_targets"]:
                    signatures.append((row["kind"], row["art_group"], row["family"], row["target"]))
            self.assertEqual(len(signatures), len(set(signatures)))
            self.assertEqual(len(signatures), 3)

    def test_outputs_are_metadata_only_and_contain_no_capture_pixels(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "CAPTURE_MISSIONS.json"
            gap = root / "CAPTURE_GAP_PLAN.json"
            output = root / "Reports" / "RouteCaptureSequencer"
            self._write_manifest(manifest)
            self._write_gap_plan(gap)
            plan = build_session_plan(manifest, gap)
            paths = write_outputs(plan, output)
            self.assertTrue(Path(paths["json"]).is_file())
            self.assertTrue(Path(paths["csv"]).is_file())
            self.assertTrue(Path(paths["html"]).is_file())
            self.assertEqual(list(output.glob("*.png")), [])
            payload = Path(paths["json"]).read_text(encoding="utf-8")
            self.assertNotIn(str(root.resolve()), payload)

    def test_sequencer_never_marks_roadmap_or_capture_mission_complete(self) -> None:
        source = (TOOLS / "route_capture_sequencer.py").read_text(encoding="utf-8")
        self.assertNotIn('"done"] = True', source)
        self.assertNotIn("ROADMAP.md", source)
        self.assertIn("VERIFIED_IN_GAME", source)


if __name__ == "__main__":
    unittest.main()
