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

from final_regression_cockpit import (  # noqa: E402
    cockpit_status,
    record_case_result,
    reset_case,
    write_dashboard,
)
from release_candidate import REGRESSION_CASES, regression_status  # noqa: E402
from studio_command_center import record_regression_result, regression_cockpit_dashboard  # noqa: E402


class FinalRegressionCockpitTests(unittest.TestCase):
    @staticmethod
    def _write_pack(folder: Path, color=(20, 70, 150, 255)) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (32, 32), color).save(folder / "tiles.png")
        (folder / "hires.txt").write_text(
            "<ver>106\n<scale>4\n<img>tiles.png\n[hero_player]<tile>0,2E,FF16360F,0,0,1,N\n",
            encoding="utf-8",
        )

    def test_pass_fail_and_next_case_are_exact_build_bound(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; manifest = root / "regression.json"
            self._write_pack(pack)
            first = REGRESSION_CASES[0][0]
            second = REGRESSION_CASES[1][0]
            record_case_result(manifest, first, pack, "PASS", notes="verified locally")
            record_case_result(manifest, second, pack, "FAIL", failure_category="ANIMATION_SEAM", failure_notes="landing frame seam")
            status = cockpit_status(manifest, pack)
            self.assertEqual(status["counts"]["PASS"], 1)
            self.assertEqual(status["counts"]["FAIL"], 1)
            self.assertEqual(status["next_case"]["key"], second)
            self.assertEqual(status["next_case"]["failure_category"], "ANIMATION_SEAM")
            authoritative = regression_status(manifest, pack)
            self.assertEqual(authoritative["done_current_build"], 1)
            self.assertEqual(authoritative["gate"], "BLOCKED")

    def test_runtime_art_change_makes_old_pass_stale(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; manifest = root / "regression.json"
            self._write_pack(pack)
            first = REGRESSION_CASES[0][0]
            record_case_result(manifest, first, pack, "PASS")
            self._write_pack(pack, color=(190, 40, 30, 255))
            status = cockpit_status(manifest, pack)
            row = next(item for item in status["cases"] if item["key"] == first)
            self.assertEqual(row["state"], "STALE")
            self.assertEqual(status["counts"]["STALE"], 1)
            self.assertEqual(status["gate"], "BLOCKED")

    def test_failed_case_can_be_retested_to_pass_and_history_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; manifest = root / "regression.json"
            self._write_pack(pack)
            case = REGRESSION_CASES[0][0]
            record_case_result(manifest, case, pack, "FAIL", failure_category="WRONG_PALETTE", failure_notes="wrong damage palette")
            record_case_result(manifest, case, pack, "PASS", notes="retested after art fix")
            status = cockpit_status(manifest, pack)
            row = next(item for item in status["cases"] if item["key"] == case)
            self.assertEqual(row["state"], "PASS")
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual([item["result"] for item in data["history"][-2:]], ["FAIL", "PASS"])

    def test_reset_returns_case_to_pending(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; manifest = root / "regression.json"
            self._write_pack(pack)
            case = REGRESSION_CASES[0][0]
            record_case_result(manifest, case, pack, "PASS")
            reset_case(manifest, case)
            status = cockpit_status(manifest, pack)
            row = next(item for item in status["cases"] if item["key"] == case)
            self.assertEqual(row["state"], "PENDING")

    def test_dashboard_is_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); pack = root / "pack"; manifest = root / "regression.json"; report = root / "report"
            self._write_pack(pack)
            status = cockpit_status(manifest, pack)
            outputs = write_dashboard(status, report)
            self.assertTrue(Path(outputs["dashboard"]).is_file())
            self.assertTrue(Path(outputs["json"]).is_file())
            self.assertEqual(list(report.rglob("*.png")), [])

    def test_studio_orchestration_records_and_refreshes_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); workspace = root / "workspace"; pack = root / "pack"
            workspace.mkdir(); self._write_pack(pack)
            initial = regression_cockpit_dashboard(workspace, pack)
            self.assertEqual(initial["counts"]["PASS"], 0)
            case = initial["next_case"]["key"]
            result = record_regression_result(workspace, pack, case, "PASS", notes="verified in MesenCE")
            self.assertEqual(result["recorded"]["result"], "PASS")
            self.assertEqual(result["status"]["counts"]["PASS"], 1)
            self.assertTrue(Path(result["status"]["outputs"]["dashboard"]).is_file())


if __name__ == "__main__":
    unittest.main()
