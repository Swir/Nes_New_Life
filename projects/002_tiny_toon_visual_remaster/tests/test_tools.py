from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from hdpack_pipeline import (  # noqa: E402
    analyze,
    build_preview,
    compare_captures,
    parse_tile_rules,
    write_art_queue,
    write_report,
)
from rom_probe import decode_chr_tile, parse_rom  # noqa: E402
from validate_hdpack import validate  # noqa: E402


class ToolTests(unittest.TestCase):
    def test_parse_synthetic_ines_mapper4(self) -> None:
        header = bytearray(16)
        header[:4] = b"NES\x1a"
        header[4] = 1
        header[5] = 1
        header[6] = 0x40
        data = bytes(header) + bytes(16384) + bytes(8192)
        with tempfile.TemporaryDirectory() as td:
            rom = Path(td) / "synthetic.nes"
            rom.write_bytes(data)
            info, loaded = parse_rom(rom)
        self.assertEqual(info.mapper, 4)
        self.assertEqual(info.prg_rom_bytes, 16384)
        self.assertEqual(info.chr_rom_bytes, 8192)
        self.assertEqual(info.chr_tile_count, 512)
        self.assertEqual(len(loaded), len(data))

    def test_chr_decode(self) -> None:
        tile = bytes([0x80] + [0] * 7 + [0] * 8)
        pixels = decode_chr_tile(tile)
        self.assertEqual(len(pixels), 64)
        self.assertEqual(pixels[0], 1)
        self.assertTrue(all(value == 0 for value in pixels[1:]))

    def test_template_hdpack_is_structurally_valid(self) -> None:
        errors, warnings, stats = validate(ROOT / "template_hdpack")
        self.assertEqual(errors, [])
        self.assertEqual(stats["images"], 0)
        self.assertEqual(stats["tiles"], 0)
        self.assertTrue(any("No <tile>" in item for item in warnings))

    @staticmethod
    def _write_pack(folder: Path, extra: bool = False) -> None:
        folder.mkdir()
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
            "[hero]<tile>0,2F,FF16360F,32,0,1,N",
            "<condition>hero,tileNearby,8,0,2E,FF16360F",
        ]
        if extra:
            lines.extend(
                [
                    "<tile>0,30,FF27160F,0,32,1,N",
                    "[boss]<tile>0,31,FF27160F,32,32,1,N",
                    "<condition>boss,tileNearby,8,0,30,FF27160F",
                ]
            )
        (folder / "hires.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_analyze_and_build_non_destructive_preview(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            output = root / "preview"
            self._write_pack(source)
            hires = (source / "hires.txt").read_text(encoding="utf-8")

            stats = analyze(source)
            self.assertEqual(stats.version, 106)
            self.assertEqual(stats.scale, 4)
            self.assertEqual(stats.tile_rules, 2)
            self.assertEqual(stats.conditional_tile_rules, 1)
            self.assertEqual(stats.conditions, 1)
            self.assertEqual(stats.unique_tile_ids, 2)
            self.assertEqual(stats.unique_palettes, 1)
            self.assertEqual(stats.missing_images, [])

            rules = parse_tile_rules(source)
            self.assertEqual(rules[0].tile_id, "2E")
            self.assertEqual(rules[1].condition, "hero")
            self.assertEqual((rules[1].x, rules[1].y), (32, 0))

            manifest = build_preview(source, output, style="vibrant")
            self.assertTrue(manifest["mapping_preserved"])
            self.assertEqual((output / "hires.txt").read_text(encoding="utf-8"), hires)
            self.assertTrue((output / "tiles.png").is_file())
            self.assertTrue((output / "NES_NEW_LIFE_PREVIEW.json").is_file())
            self.assertNotEqual((source / "tiles.png").read_bytes(), (output / "tiles.png").read_bytes())

            errors, _, validated = validate(output)
            self.assertEqual(errors, [])
            self.assertEqual(validated["tiles"], 2)

            report = write_report(output)
            self.assertTrue(report.is_file())
            self.assertIn("Tile rules", report.read_text(encoding="utf-8"))

    def test_capture_growth_and_ranked_art_queue(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            baseline = root / "baseline"
            current = root / "current"
            self._write_pack(baseline)
            self._write_pack(current, extra=True)

            diff = compare_captures(baseline, current)
            self.assertTrue(diff["capture_progressed"])
            self.assertEqual(diff["baseline_rule_count"], 2)
            self.assertEqual(diff["current_rule_count"], 4)
            self.assertEqual(diff["added_rule_count"], 2)
            self.assertEqual(diff["removed_rule_count"], 0)
            self.assertEqual(diff["new_tile_ids"], ["30", "31"])
            self.assertEqual(diff["new_palettes"], ["FF27160F"])

            queue = write_art_queue(current)
            with queue.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 4)
            self.assertEqual(rows[0]["priority"], "1")
            self.assertEqual(rows[0]["status"], "TODO")
            self.assertEqual(rows[0]["art_group"], "UNASSIGNED")


if __name__ == "__main__":
    unittest.main()
