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

from capture_mission_control import (  # noqa: E402
    ensure_manifest,
    mission_status,
    record_session,
    write_dashboard,
)


class CaptureMissionControlTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path, extra_rule: bool = False) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (64, 32), (20, 40, 80, 255)).save(folder / "tiles.png")
        lines = [
            "<ver>106",
            "<scale>4",
            "<img>tiles.png",
            "[hero_player]<tile>0,2E,FF16360F,0,0,1,N",
        ]
        if extra_rule:
            lines.append("[boss_phase]<tile>0,2F,FF27160F,32,0,1,N")
        (folder / "hires.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_manifest_and_priority_queue(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            manifest = Path(td) / "capture.json"
            ensure_manifest(manifest)
            status = mission_status(manifest)
            self.assertEqual(status["done"], 0)
            self.assertEqual(status["release_capture_gate"], "BLOCKED")
            self.assertTrue(status["next_missions"])
            self.assertEqual(status["next_missions"][0]["priority"], 100)

    def test_sessions_record_delta_and_manual_completion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "capture.json"
            capture = root / "capture"
            self._write_pack(capture)
            first = record_session(manifest, capture, ["boot_title_menu"], "title captured")
            self.assertGreater(first["delta"]["tile_rules"], 0)

            self._write_pack(capture, extra_rule=True)
            second = record_session(manifest, capture, ["bosses_all_phases"])
            self.assertEqual(second["delta"]["tile_rules"], 1)
            status = mission_status(manifest)
            self.assertEqual(status["done"], 2)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertTrue(data["missions"]["bosses_all_phases"]["done"])

    def test_stagnation_is_detected_without_false_completion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "capture.json"
            capture = root / "capture"
            self._write_pack(capture)
            record_session(manifest, capture)
            record_session(manifest, capture)
            status = mission_status(manifest)
            self.assertTrue(status["stagnating"])
            self.assertEqual(status["release_capture_gate"], "BLOCKED")

    def test_dashboard_writes_html_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "capture.json"
            output = root / "report" / "capture.html"
            ensure_manifest(manifest)
            write_dashboard(manifest, output)
            self.assertTrue(output.is_file())
            self.assertTrue(output.with_suffix(".json").is_file())
            self.assertIn("Capture Mission Control", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
