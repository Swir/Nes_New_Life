from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from rom_probe import decode_chr_tile, parse_rom  # noqa: E402
from validate_hdpack import validate  # noqa: E402


class ToolTests(unittest.TestCase):
    def test_parse_synthetic_ines_mapper4(self) -> None:
        header = bytearray(16)
        header[:4] = b"NES\x1a"
        header[4] = 1  # 16 KiB PRG
        header[5] = 1  # 8 KiB CHR
        header[6] = 0x40  # mapper low nibble = 4
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
        # First bit set in low plane -> first pixel color index 1.
        tile = bytes([0x80] + [0] * 7 + [0] * 8)
        pixels = decode_chr_tile(tile)
        self.assertEqual(len(pixels), 64)
        self.assertEqual(pixels[0], 1)
        self.assertTrue(all(v == 0 for v in pixels[1:]))

    def test_template_hdpack_is_structurally_valid(self) -> None:
        errors, warnings, stats = validate(ROOT / "template_hdpack")
        self.assertEqual(errors, [])
        self.assertEqual(stats["images"], 0)
        self.assertEqual(stats["tiles"], 0)
        self.assertTrue(any("No <tile>" in item for item in warnings))


if __name__ == "__main__":
    unittest.main()
