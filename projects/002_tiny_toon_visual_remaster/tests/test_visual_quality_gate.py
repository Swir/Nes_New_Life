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

from visual_quality_gate import audit_master_pair, audit_workspace_visual_quality  # noqa: E402


class VisualQualityGateTests(unittest.TestCase):
    @staticmethod
    def _pattern(path: Path, *, size: tuple[int, int] = (16, 16), colors: int = 8) -> None:
        image = Image.new("RGBA", size, (0, 0, 0, 0))
        px = image.load()
        for y in range(2, size[1] - 2):
            for x in range(2, size[0] - 2):
                value = ((x * 37 + y * 19) % max(colors, 1)) * max(1, 255 // max(colors, 1))
                px[x, y] = (value % 256, (value * 3) % 256, (255 - value) % 256, 255)
        image.save(path)

    def test_legitimate_redraw_passes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = root / "original.png"
            edited = root / "edited.png"
            self._pattern(original)
            self._pattern(edited, colors=12)
            with Image.open(edited) as raw:
                image = raw.convert("RGBA")
            image.putpixel((5, 5), (255, 80, 40, 255))
            image.save(edited)
            result = audit_master_pair(original, edited, "hero.png")
            self.assertEqual("PASS", result["gate"])
            self.assertEqual([], result["blockers"])
            self.assertGreater(result["changed_pixel_ratio"], 0)

    def test_fully_transparent_redraw_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = root / "original.png"
            edited = root / "edited.png"
            self._pattern(original)
            Image.new("RGBA", (16, 16), (0, 0, 0, 0)).save(edited)
            result = audit_master_pair(original, edited, "hero.png")
            self.assertEqual("FAIL", result["gate"])
            self.assertIn("FULLY_TRANSPARENT", result["blockers"])
            self.assertIn("ALPHA_COVERAGE_COLLAPSE", result["blockers"])

    def test_color_collapse_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = root / "original.png"
            edited = root / "edited.png"
            self._pattern(original)
            image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
            for y in range(2, 14):
                for x in range(2, 14):
                    image.putpixel((x, y), (80, 80, 80, 255))
            image.save(edited)
            result = audit_master_pair(original, edited, "hero.png")
            self.assertEqual("FAIL", result["gate"])
            self.assertIn("COLOR_COLLAPSE", result["blockers"])

    def test_bbox_collapse_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = root / "original.png"
            edited = root / "edited.png"
            self._pattern(original)
            image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
            image.putpixel((8, 8), (255, 255, 255, 255))
            image.save(edited)
            result = audit_master_pair(original, edited, "hero.png")
            self.assertEqual("FAIL", result["gate"])
            self.assertTrue({"BBOX_WIDTH_COLLAPSE", "BBOX_HEIGHT_COLLAPSE"}.intersection(result["blockers"]))

    def test_workspace_report_is_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            workspace = root / "MasterWorkspace"
            (workspace / "original").mkdir(parents=True)
            (workspace / "editable").mkdir(parents=True)
            self._pattern(workspace / "original" / "hero.png")
            self._pattern(workspace / "editable" / "hero.png", colors=12)
            report_path = root / "report.json"
            report = audit_workspace_visual_quality(workspace, [{"master_file": "hero.png"}], report_path)
            self.assertEqual("PASS", report["qa_gate"])
            payload = report_path.read_text(encoding="utf-8")
            self.assertNotIn(str(root), payload)
            decoded = json.loads(payload)
            self.assertEqual("hero.png", decoded["results"][0]["master_file"])
            self.assertNotIn("pixels", decoded["privacy"].lower().replace("no image pixels", ""))


if __name__ == "__main__":
    unittest.main()
