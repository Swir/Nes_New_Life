from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from art_workspace import init_workspace  # noqa: E402
from capture_mission_control import default_manifest  # noqa: E402
from production_sprint import build_and_write, build_production_status  # noqa: E402
from studio_command_center import initialize_project_evidence, production_sprint_dashboard  # noqa: E402


class ProductionSprintTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", (96, 32), (0, 0, 0, 0))
        for index, color in enumerate(((220, 80, 60, 255), (70, 150, 240, 255), (240, 180, 50, 255))):
            for y in range(32):
                for x in range(index * 32, (index + 1) * 32):
                    image.putpixel((x, y), color)
        image.save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "<ver>106\n<scale>4\n<img>tiles.png\n"
            "[hero_idle]<tile>0,10,FF000001,0,0,1,N\n"
            "[hero_walk_f1]<tile>0,11,FF000001,32,0,1,N\n"
            "[boss_alpha_intro]<tile>0,20,FF000002,64,0,1,N\n",
            encoding="utf-8",
        )

    @staticmethod
    def _write_queue(path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["tile_id", "palette", "status", "art_group"])
            writer.writerow(["10", "FF000001", "TODO", "PLAYER"])
            writer.writerow(["11", "FF000001", "TODO", "PLAYER"])
            writer.writerow(["20", "FF000002", "TODO", "BOSS"])

    def _workspace(self, root: Path, pack: Path) -> None:
        paths = initialize_project_evidence(root)
        self._write_queue(paths.art_queue)
        init_workspace(pack, root / "Artwork" / "MasterWorkspace", paths.art_queue)
        manifest = default_manifest()
        paths.capture_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def test_status_combines_capture_review_and_art_actions(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "capture"
            self._write_pack(pack)
            self._workspace(root, pack)
            result = build_production_status(root, pack, pack, top=10)
            self.assertEqual(result["capture"]["release_capture_gate"], "BLOCKED")
            self.assertGreater(result["master_workspace"]["todo"], 0)
            self.assertGreater(result["final_art"]["top_count"], 0)
            actions = " ".join(item["action"] for item in result["actions"])
            self.assertIn("Capture Mission Control", actions)
            self.assertIn("Final Art Sprint", actions)

    def test_dashboard_is_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "capture"
            self._write_pack(pack)
            self._workspace(root, pack)
            output = root / "Reports" / "ProductionSprint"
            result = build_and_write(root, pack, pack, output)
            self.assertTrue(Path(result["outputs"]["dashboard"]).is_file())
            self.assertTrue(Path(result["outputs"]["json"]).is_file())
            self.assertEqual(list(output.glob("*.png")), [])
            text = Path(result["outputs"]["dashboard"]).read_text(encoding="utf-8")
            self.assertNotIn("data:image", text)

    def test_studio_orchestration_writes_production_sprint_report(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "capture"
            self._write_pack(pack)
            self._workspace(root, pack)
            result = production_sprint_dashboard(root, pack, pack, top=5)
            self.assertTrue(Path(result["outputs"]["dashboard"]).is_file())
            self.assertLessEqual(result["final_art"]["top_count"], 5)


if __name__ == "__main__":
    unittest.main()
