from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from fullscreen_launch import (  # noqa: E402
    build_mesence_args,
    fullscreen_evidence_status,
    record_fullscreen_evidence,
)


class FullscreenLaunchTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path, color=(20, 80, 140, 255)) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (32, 32), color).save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "<ver>106\n<scale>4\n<img>tiles.png\n[hero_player]<tile>0,2E,FF16360F,0,0,1,N\n",
            encoding="utf-8",
        )

    def test_fullscreen_argument_precedes_rom(self) -> None:
        args = build_mesence_args(Path(r"C:\Games\Tiny Toon.nes"))
        self.assertEqual(args[0], "/fullscreen")
        self.assertTrue(args[-1].endswith("Tiny Toon.nes"))

    def test_verified_evidence_is_bound_to_exact_pack(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            evidence = root / "Reports" / "FullscreenPlaytest" / "FULLSCREEN_PLAYTEST.json"
            self._write_pack(pack)
            record_fullscreen_evidence(
                pack,
                evidence,
                emulator="Mesen.exe",
                rom_name="Tiny Toon.nes",
                verified=True,
                method="commandline:/fullscreen",
                attempts=1,
            )
            status = fullscreen_evidence_status(pack, evidence)
            self.assertEqual(status["gate"], "PASS")
            self.assertTrue(status["fingerprint_matches"])

            self._write_pack(pack, color=(180, 40, 80, 255))
            stale = fullscreen_evidence_status(pack, evidence)
            self.assertEqual(stale["gate"], "BLOCKED")
            self.assertFalse(stale["fingerprint_matches"])

    def test_unverified_fullscreen_never_passes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            evidence = root / "evidence.json"
            self._write_pack(pack)
            record_fullscreen_evidence(
                pack,
                evidence,
                emulator="Mesen.exe",
                rom_name="Tiny Toon.nes",
                verified=False,
                method="window-check-failed",
                attempts=2,
            )
            self.assertEqual(fullscreen_evidence_status(pack, evidence)["gate"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
