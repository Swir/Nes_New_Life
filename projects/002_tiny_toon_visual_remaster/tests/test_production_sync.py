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

from production_sync import prepare_incremental, sync_art_queue, sync_master_workspace  # noqa: E402


class IncrementalProductionTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path, extra: bool = False) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        for y in range(32):
            for x in range(32):
                image.putpixel((x, y), (170, 40, 50, 255))
        image.save(folder / "tiles.png")
        lines = [
            "<ver>106",
            "<scale>4",
            "<img>tiles.png",
            "<tile>0,2E,FF16360F,0,0,1,N",
            "[hero_player]<tile>0,2F,FF16360F,32,0,1,N",
            "<condition>hero_player,tileNearby,8,0,2E,FF16360F",
        ]
        if extra:
            lines.extend([
                "<tile>0,30,FF27160F,0,32,1,N",
                "[boss_final]<tile>0,31,FF27160F,32,32,1,N",
                "<condition>boss_final,tileNearby,8,0,30,FF27160F",
            ])
        (folder / "hires.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_queue_sync_preserves_artist_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = root / "first"
            second = root / "second"
            self._write_pack(first)
            self._write_pack(second, extra=True)
            queue = root / "ART_QUEUE.csv"

            sync_art_queue(first, queue)
            with queue.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            target = next(row for row in rows if row["tile_id"] == "2E")
            target["status"] = "DONE"
            target["art_group"] = "WORLD"
            target["notes"] = "artist verified"
            with queue.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

            result = sync_art_queue(second, queue)
            self.assertGreaterEqual(result["added"], 2)
            self.assertEqual(result["preserved_non_todo_status"], 1)
            with queue.open(encoding="utf-8", newline="") as handle:
                updated = list(csv.DictReader(handle))
            kept = next(row for row in updated if row["tile_id"] == "2E")
            self.assertEqual(kept["status"], "DONE")
            self.assertEqual(kept["art_group"], "WORLD")
            self.assertEqual(kept["notes"], "artist verified")

    def test_workspace_sync_preserves_edited_master_across_capture_growth(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = root / "first"
            second = root / "second"
            self._write_pack(first)
            self._write_pack(second, extra=True)
            queue = root / "ART_QUEUE.csv"
            workspace = root / "MasterWorkspace"

            sync_art_queue(first, queue)
            initial = sync_master_workspace(first, workspace, queue)
            self.assertEqual(initial["mode"], "initialized")

            manifest = json.loads((workspace / "MASTER_TILES.json").read_text(encoding="utf-8"))
            master_name = manifest["masters"][0]["file"]
            editable = workspace / "editable" / master_name
            with Image.open(editable) as image:
                changed = image.convert("RGBA")
            changed.putpixel((0, 0), (1, 2, 3, 255))
            changed.save(editable)
            edited_bytes = editable.read_bytes()

            sync_art_queue(second, queue)
            result = sync_master_workspace(second, workspace, queue)
            self.assertEqual(result["mode"], "synchronized")
            self.assertGreaterEqual(result["preserved_edited_masters"], 1)
            self.assertEqual(editable.read_bytes(), edited_bytes)
            self.assertGreaterEqual(result["new_masters"], 0)
            self.assertEqual(result["scan"]["invalid"], 0)

    def test_prepare_incremental_builds_resume_safe_production_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "capture"
            project = root / "project"
            project.mkdir()
            self._write_pack(pack, extra=True)

            result = prepare_incremental(pack, project)
            self.assertEqual(result["scale"], 4)
            self.assertTrue((project / "Artwork" / "ART_QUEUE.csv").is_file())
            self.assertTrue((project / "Artwork" / "MasterWorkspace" / "MASTER_TILES.json").is_file())
            self.assertTrue((project / "Artwork" / "Workboards" / "WORKBOARDS.json").is_file())
            self.assertTrue((project / "Reports" / "CAPTURE_REPORT.html").is_file())
            self.assertTrue((project / "Reports" / "HD_READINESS.html").is_file())
            self.assertTrue((project / "Reports" / "PRODUCTION_SYNC.json").is_file())
            self.assertTrue((project / "HD_READINESS_CHECKLIST.json").is_file())


if __name__ == "__main__":
    unittest.main()
