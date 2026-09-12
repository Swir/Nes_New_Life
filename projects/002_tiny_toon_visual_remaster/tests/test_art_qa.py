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

from art_qa import audit_art_apply  # noqa: E402
from art_workspace import apply_workspace, init_workspace  # noqa: E402


class ArtQATests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path) -> None:
        folder.mkdir()
        image = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
        for y in range(32):
            for x in range(32):
                image.putpixel((x, y), (180, 40, 50, 255))
        for y in range(32):
            for x in range(32, 64):
                image.putpixel((x, y), (30, 120, 210, 255))
        image.save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "\n".join([
                "<ver>106",
                "<scale>4",
                "<img>tiles.png",
                "[hero_player]<tile>0,2E,FF16360F,0,0,1,N",
                "[boss_final]<tile>0,2F,FF27160F,32,0,1,N",
            ]) + "\n",
            encoding="utf-8",
        )

    def _build_one_edit(self, root: Path) -> tuple[Path, Path, Path, dict]:
        pack = root / "pack"
        workspace = root / "workspace"
        output = root / "output"
        self._write_pack(pack)
        init_workspace(pack, workspace)
        manifest = json.loads((workspace / "MASTER_TILES.json").read_text(encoding="utf-8"))
        master = manifest["masters"][0]
        editable = workspace / "editable" / master["file"]
        with Image.open(editable) as current:
            replacement = Image.new("RGBA", current.size, (20, 240, 90, 255))
        replacement.save(editable)
        apply_workspace(pack, workspace, output)
        return pack, workspace, output, master

    def test_pixel_qa_passes_when_changes_stay_inside_edited_master_targets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack, workspace, output, _ = self._build_one_edit(root)
            report_dir = root / "qa"
            result = audit_art_apply(pack, output, workspace, report_dir)
            self.assertEqual(result["qa_gate"], "PASS")
            self.assertTrue(result["mapping_preserved"])
            self.assertEqual(result["changed_master_count"], 1)
            self.assertGreater(result["authorized_changed_pixels"], 0)
            self.assertEqual(result["unauthorized_changed_pixels"], 0)
            self.assertEqual(result["edited_masters_with_no_output_difference"], [])
            self.assertTrue((report_dir / "ART_QA_RESULT.json").is_file())
            self.assertTrue((report_dir / "ART_QA_REPORT.html").is_file())

    def test_pixel_qa_blocks_single_pixel_change_outside_authorized_targets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack, workspace, output, master = self._build_one_edit(root)
            target = master["targets"][0]
            x0, y0 = int(target["x"]), int(target["y"])
            with Image.open(workspace / "original" / master["file"]) as tile:
                w, h = tile.size
            tamper = None
            for y in range(32):
                for x in range(64):
                    if not (x0 <= x < x0 + w and y0 <= y < y0 + h):
                        tamper = (x, y)
                        break
                if tamper:
                    break
            self.assertIsNotNone(tamper)
            sheet_path = output / "tiles.png"
            with Image.open(sheet_path) as raw:
                sheet = raw.convert("RGBA")
            old = sheet.getpixel(tamper)
            sheet.putpixel(tamper, ((old[0] + 1) % 256, old[1], old[2], old[3]))
            sheet.save(sheet_path)

            result = audit_art_apply(pack, output, workspace, root / "qa")
            self.assertEqual(result["qa_gate"], "BLOCKED")
            self.assertEqual(result["unauthorized_changed_pixels"], 1)


if __name__ == "__main__":
    unittest.main()
