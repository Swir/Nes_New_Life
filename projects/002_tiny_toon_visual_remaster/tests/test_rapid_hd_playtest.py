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

from rapid_hd_playtest import build_playtest, deploy_hdpack  # noqa: E402


class RapidHDPlaytestTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
        for y in range(32):
            for x in range(32):
                image.putpixel((x, y), (110, 70, 180, 255))
        for y in range(32):
            for x in range(32, 64):
                image.putpixel((x, y), (40, 160, 95, 255))
        image.save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "\n".join(
                [
                    "<ver>106",
                    "<scale>4",
                    "<img>tiles.png",
                    "[hero_player]<tile>0,2E,FF16360F,0,0,1,N",
                    "[world_grass]<tile>0,2F,FF27160F,32,0,1,N",
                    "<condition>hero_player,tileNearby,8,0,2E,FF16360F",
                    "<condition>world_grass,tileNearby,8,0,2F,FF27160F",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def test_one_click_build_produces_qa_gated_playtest_pack(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            capture = root / "capture"
            project = root / "project"
            self._write_pack(capture)

            result = build_playtest(capture, project)

            output = Path(result["output_pack"])
            self.assertTrue(result["playtest_ready"])
            self.assertTrue((output / "hires.txt").is_file())
            self.assertTrue((output / "tiles.png").is_file())
            self.assertEqual((output / "hires.txt").read_bytes(), (capture / "hires.txt").read_bytes())
            self.assertEqual(result["apply"]["pixel_qa"]["qa_gate"], "PASS")
            self.assertGreaterEqual(result["baseline"]["seeded"], 1)
            self.assertTrue((project / "Reports" / "RAPID_HD_PLAYTEST.json").is_file())
            self.assertTrue((project / "Reports" / "HD_READINESS_PLAYTEST.html").is_file())

    def test_deploy_uses_rom_stem_and_backs_up_previous_pack(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            self._write_pack(pack)
            hdpacks = root / "MesenCE" / "HdPacks"
            existing = hdpacks / "Tiny Toon Adventures (USA)"
            existing.mkdir(parents=True)
            (existing / "old.txt").write_text("old", encoding="utf-8")

            result = deploy_hdpack(pack, "Tiny Toon Adventures (USA).nes", hdpacks)
            installed = Path(result["destination"])
            backup = Path(result["backup"])

            self.assertEqual(installed.name, "Tiny Toon Adventures (USA)")
            self.assertTrue((installed / "hires.txt").is_file())
            self.assertTrue((installed / "tiles.png").is_file())
            self.assertTrue((backup / "old.txt").is_file())

    def test_deploy_refuses_rom_or_patch_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            self._write_pack(pack)
            (pack / "forbidden.nes").write_bytes(b"NES\x1a")
            with self.assertRaises(ValueError):
                deploy_hdpack(pack, "Tiny Toon Adventures (USA).nes", root / "HdPacks")

    def test_runtime_deploy_excludes_generated_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            self._write_pack(pack)
            (pack / "ART_APPLY_RESULT.json").write_text(json.dumps({"generated": True}), encoding="utf-8")
            result = deploy_hdpack(pack, "Tiny Toon.nes", root / "HdPacks", keep_backup=False)
            installed = Path(result["destination"])
            self.assertFalse((installed / "ART_APPLY_RESULT.json").exists())
            self.assertTrue((installed / "hires.txt").exists())


if __name__ == "__main__":
    unittest.main()
