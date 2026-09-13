from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from active_family_workbench import WorkbenchError, resolve_active_family_workbench, write_active_state


class ActiveFamilyWorkbenchTests(unittest.TestCase):
    def _kit(self, root: Path) -> Path:
        kit = root / "CurrentImpactSprint"
        (kit / "family_boards").mkdir(parents=True)
        (kit / "editable").mkdir()
        (kit / "reference").mkdir()
        return kit

    def test_selects_highest_priority_family_and_exact_members(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            kit = self._kit(Path(tmp))
            (kit / "family_boards" / "FAMILY_001.png").write_bytes(b"png")
            (kit / "family_boards" / "FAMILY_002.png").write_bytes(b"png")
            sprint = {
                "schema": 4,
                "items": [
                    {"priority": 9, "tile_id": "B", "palette": "P2", "kit_file": "b.png"},
                    {"priority": 2, "tile_id": "A", "palette": "P1", "kit_file": "a.png"},
                    {"priority": 3, "tile_id": "A2", "palette": "P1", "kit_file": "a2.png"},
                ],
            }
            boards = {
                "schema": 1,
                "families": [
                    {"family": "ENEMY::B::P2", "file": "family_boards/FAMILY_001.png", "members": 1,
                     "metrics": [{"priority": 9, "tile_id": "B", "palette": "P2"}]},
                    {"family": "PLAYER::A::P1", "file": "family_boards/FAMILY_002.png", "members": 2,
                     "metrics": [
                         {"priority": 2, "tile_id": "A", "palette": "P1"},
                         {"priority": 3, "tile_id": "A2", "palette": "P1"},
                     ]},
                ],
            }
            (kit / "ART_SPRINT_KIT.json").write_text(json.dumps(sprint), encoding="utf-8")
            (kit / "FAMILY_CONTACT_BOARDS.json").write_text(json.dumps(boards), encoding="utf-8")
            result = resolve_active_family_workbench(kit)
            self.assertEqual("ACTIVE_FAMILY_READY", result["status"])
            self.assertEqual("PLAYER::A::P1", result["family"])
            self.assertEqual(2, result["priority"])
            self.assertEqual(["a.png", "a2.png"], result["editable_files"])
            state = write_active_state(result, kit)
            self.assertTrue(state.is_file())
            self.assertNotIn(str(Path(tmp).resolve()), state.read_text(encoding="utf-8"))

    def test_rejects_unsafe_board_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            kit = self._kit(Path(tmp))
            (kit / "ART_SPRINT_KIT.json").write_text(json.dumps({"items": []}), encoding="utf-8")
            (kit / "FAMILY_CONTACT_BOARDS.json").write_text(
                json.dumps({"families": [{"family": "PLAYER", "file": "../escape.png", "metrics": []}]}),
                encoding="utf-8",
            )
            with self.assertRaises(WorkbenchError):
                resolve_active_family_workbench(kit)

    def test_requires_real_generated_board(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            kit = self._kit(Path(tmp))
            (kit / "ART_SPRINT_KIT.json").write_text(json.dumps({"items": []}), encoding="utf-8")
            (kit / "FAMILY_CONTACT_BOARDS.json").write_text(
                json.dumps({"families": [{"family": "PLAYER", "file": "family_boards/missing.png", "metrics": []}]}),
                encoding="utf-8",
            )
            with self.assertRaises(WorkbenchError):
                resolve_active_family_workbench(kit)


if __name__ == "__main__":
    unittest.main()
