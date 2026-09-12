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

from final_regression_cockpit import record_case_result  # noqa: E402
from release_candidate import (  # noqa: E402
    REGRESSION_CASES,
    complete_regression_case,
    ensure_regression_manifest,
    pack_fingerprint,
    regression_status,
)


class AuthoritativeReleaseGateTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path, color=(20, 80, 140, 255)) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (32, 32), color).save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "<ver>106\n<scale>4\n<img>tiles.png\n[hero_player]<tile>0,2E,FF16360F,0,0,1,N\n",
            encoding="utf-8",
        )

    def test_cockpit_fail_is_visible_to_release_gate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            manifest = root / "FINAL_REGRESSION.json"
            self._write_pack(pack)
            ensure_regression_manifest(manifest)
            record_case_result(
                manifest,
                "bosses",
                pack,
                "FAIL",
                failure_category="ANIMATION_SEAM",
                failure_notes="synthetic boss transition seam",
            )
            status = regression_status(manifest, pack)
            self.assertEqual(status["counts"]["FAIL"], 1)
            self.assertEqual(status["next_case"]["key"], "bosses")
            boss = next(row for row in status["cases"] if row["key"] == "bosses")
            self.assertEqual(boss["state"], "FAIL")
            self.assertEqual(boss["failure_category"], "ANIMATION_SEAM")
            self.assertEqual(status["gate"], "BLOCKED")

    def test_runtime_change_invalidates_cockpit_passes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            manifest = root / "FINAL_REGRESSION.json"
            self._write_pack(pack)
            ensure_regression_manifest(manifest)
            for key, _ in REGRESSION_CASES:
                record_case_result(manifest, key, pack, "PASS", notes="synthetic verification")
            self.assertEqual(regression_status(manifest, pack)["gate"], "PASS")
            old = pack_fingerprint(pack)
            self._write_pack(pack, color=(160, 40, 80, 255))
            self.assertNotEqual(pack_fingerprint(pack), old)
            status = regression_status(manifest, pack)
            self.assertEqual(status["counts"]["PASS"], 0)
            self.assertEqual(status["counts"]["STALE"], len(REGRESSION_CASES))
            self.assertEqual(status["gate"], "BLOCKED")

    def test_legacy_complete_command_upgrades_to_schema2_history(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            manifest = root / "FINAL_REGRESSION.json"
            self._write_pack(pack)
            complete_regression_case(manifest, "boot_title_menu", pack, "verified")
            raw = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(raw["schema"], 2)
            self.assertEqual(raw["cases"]["boot_title_menu"]["result"], "PASS")
            self.assertEqual(len(raw["history"]), 1)
            self.assertEqual(raw["history"][0]["pack_fingerprint"], pack_fingerprint(pack))


if __name__ == "__main__":
    unittest.main()
