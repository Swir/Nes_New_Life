from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from animation_consistency_gate import audit_animation_consistency


class AnimationConsistencyGateTests(unittest.TestCase):
    def _workspace(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "editable").mkdir()
        return temp, root

    def _sprite(self, path: Path, box: tuple[int, int, int, int], color=(80, 170, 240, 255)) -> None:
        image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        ImageDraw.Draw(image).rectangle(box, fill=color)
        image.save(path)

    def _manifest(self, root: Path) -> None:
        data = {
            "masters": [
                {
                    "file": "idle.png", "group": "PLAYER", "tile_id": "01", "palette": "AAAA",
                    "targets": [{"condition": "buster_idle_f1"}],
                },
                {
                    "file": "walk.png", "group": "PLAYER", "tile_id": "02", "palette": "AAAA",
                    "targets": [{"condition": "buster_walk_f2"}],
                },
                {
                    "file": "jump.png", "group": "PLAYER", "tile_id": "03", "palette": "AAAA",
                    "targets": [{"condition": "buster_jump_f3"}],
                },
                {
                    "file": "pal_a.png", "group": "ENEMY", "tile_id": "99", "palette": "1111",
                    "targets": [{"condition": "rat_walk_f1"}],
                },
                {
                    "file": "pal_b.png", "group": "ENEMY", "tile_id": "99", "palette": "2222",
                    "targets": [{"condition": "rat_walk_f1"}],
                },
                {
                    "file": "world.png", "group": "WORLD", "tile_id": "55", "palette": "3333",
                    "targets": [{"condition": "grass_anim_f1"}],
                },
            ]
        }
        (root / "MASTER_TILES.json").write_text(json.dumps(data), encoding="utf-8")

    def test_consistent_character_frame_passes(self) -> None:
        temp, root = self._workspace()
        try:
            self._manifest(root)
            for name in ("idle.png", "walk.png", "jump.png"):
                self._sprite(root / "editable" / name, (8, 6, 23, 27))
            self._sprite(root / "editable" / "pal_a.png", (7, 8, 24, 26))
            self._sprite(root / "editable" / "pal_b.png", (7, 8, 24, 26), (200, 80, 80, 255))
            self._sprite(root / "editable" / "world.png", (0, 0, 31, 31))
            report = audit_animation_consistency(root, [{"master_file": "walk.png"}])
            self.assertEqual("PASS", report["qa_gate"])
            self.assertEqual(1, report["checked_animation_families"])
            self.assertEqual(0, report["blocker_count"])
        finally:
            temp.cleanup()

    def test_family_scale_and_center_jump_are_blocking(self) -> None:
        temp, root = self._workspace()
        try:
            self._manifest(root)
            self._sprite(root / "editable" / "idle.png", (8, 6, 23, 27))
            self._sprite(root / "editable" / "jump.png", (8, 6, 23, 27))
            self._sprite(root / "editable" / "walk.png", (27, 27, 30, 30))
            self._sprite(root / "editable" / "pal_a.png", (7, 8, 24, 26))
            self._sprite(root / "editable" / "pal_b.png", (7, 8, 24, 26))
            self._sprite(root / "editable" / "world.png", (0, 0, 31, 31))
            report = audit_animation_consistency(root, [{"master_file": "walk.png"}])
            codes = {item["code"] for item in report["blockers"]}
            self.assertEqual("FAIL", report["qa_gate"])
            self.assertIn("FAMILY_BBOX_WIDTH_OUTLIER", codes)
            self.assertIn("FAMILY_BBOX_HEIGHT_OUTLIER", codes)
            self.assertIn("FAMILY_CANVAS_CENTER_JUMP", codes)
        finally:
            temp.cleanup()

    def test_palette_variant_silhouette_mismatch_is_blocking(self) -> None:
        temp, root = self._workspace()
        try:
            self._manifest(root)
            for name in ("idle.png", "walk.png", "jump.png"):
                self._sprite(root / "editable" / name, (8, 6, 23, 27))
            self._sprite(root / "editable" / "pal_a.png", (4, 5, 17, 25))
            self._sprite(root / "editable" / "pal_b.png", (23, 4, 31, 13))
            self._sprite(root / "editable" / "world.png", (0, 0, 31, 31))
            report = audit_animation_consistency(root, [{"master_file": "pal_b.png"}])
            codes = {item["code"] for item in report["blockers"]}
            self.assertEqual("FAIL", report["qa_gate"])
            self.assertIn("PALETTE_VARIANT_SILHOUETTE_MISMATCH", codes)
            self.assertEqual(1, report["checked_palette_variant_sets"])
        finally:
            temp.cleanup()

    def test_world_art_is_not_family_blocked(self) -> None:
        temp, root = self._workspace()
        try:
            self._manifest(root)
            for name in ("idle.png", "walk.png", "jump.png", "pal_a.png", "pal_b.png"):
                self._sprite(root / "editable" / name, (8, 6, 23, 27))
            self._sprite(root / "editable" / "world.png", (31, 31, 31, 31))
            report = audit_animation_consistency(root, [{"master_file": "world.png"}])
            self.assertEqual("PASS", report["qa_gate"])
            self.assertEqual(0, report["changed_character_masters"])
            self.assertEqual(0, report["checked_animation_families"])
        finally:
            temp.cleanup()

    def test_report_is_metadata_only(self) -> None:
        temp, root = self._workspace()
        try:
            self._manifest(root)
            for name in ("idle.png", "walk.png", "jump.png", "pal_a.png", "pal_b.png", "world.png"):
                self._sprite(root / "editable" / name, (8, 6, 23, 27))
            report_path = root / "report.json"
            audit_animation_consistency(root, [{"master_file": "walk.png"}], report_path)
            text = report_path.read_text(encoding="utf-8")
            self.assertNotIn(str(root), text)
            self.assertNotIn("image_bytes", text)
            self.assertIn("walk.png", text)
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
