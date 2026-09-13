from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import transactional_art_commit as tx  # noqa: E402


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


PASS_VISUAL = {
    "schema": "swir.project002.visual-quality-gate.v1",
    "qa_gate": "PASS",
    "masters_checked": 1,
    "masters_failed": 0,
    "warnings": 0,
    "blocker_codes": [],
    "results": [],
}


class TransactionalArtCommitTests(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path, Path, Path]:
        pack = root / "pack"
        workspace = root / "MasterWorkspace"
        kit = root / "CurrentImpactSprint"
        output = root / "output"
        (pack).mkdir(parents=True)
        (workspace / "editable").mkdir(parents=True)
        (workspace / "original").mkdir(parents=True)
        (kit / "editable").mkdir(parents=True)
        old = b"old-master"
        new = b"new-master"
        (workspace / "editable" / "hero.png").write_bytes(old)
        (workspace / "original" / "hero.png").write_bytes(old)
        (workspace / "ART_STATE.csv").write_text("state-before\n", encoding="utf-8")
        (workspace / "MASTER_TILES.json").write_text("{}\n", encoding="utf-8")
        (kit / "editable" / "001_hero.png").write_bytes(new)
        manifest = {
            "schema": 2,
            "items": [{
                "master_file": "hero.png",
                "kit_file": "001_hero.png",
                "workspace_editable_sha256_at_export": sha256_bytes(old),
            }],
        }
        (kit / "ART_SPRINT_KIT.json").write_text(json.dumps(manifest), encoding="utf-8")
        return pack, workspace, kit, output

    @staticmethod
    def _fake_import(workspace: Path, kit: Path) -> dict:
        source = kit / "editable" / "001_hero.png"
        target = workspace / "editable" / "hero.png"
        target.write_bytes(source.read_bytes())
        return {"imported": 1, "imported_files": ["hero.png"]}

    @staticmethod
    def _fake_scan(workspace: Path) -> dict:
        (workspace / "ART_STATE.csv").write_text("state-after\n", encoding="utf-8")
        return {"ok": True}

    def test_green_candidate_commits_workspace_and_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            pack, workspace, kit, output = self._fixture(Path(td))

            def fake_apply(_pack: Path, _workspace: Path, staged_output: Path, overwrite: bool = False) -> dict:
                staged_output.mkdir(parents=True)
                (staged_output / "hires.txt").write_text("<scale>4\n", encoding="utf-8")
                return {"pixel_qa": {"qa_gate": "PASS"}, "mapping_preserved": True}

            with patch.object(tx, "import_sprint_kit", side_effect=self._fake_import), \
                 patch.object(tx, "audit_workspace_visual_quality", return_value=PASS_VISUAL), \
                 patch.object(tx, "apply_workspace", side_effect=fake_apply), \
                 patch.object(tx, "scan_workspace", side_effect=self._fake_scan):
                result = tx.transactional_finish_sprint(pack, workspace, kit, output, overwrite=True)

            self.assertEqual("COMMITTED", result["transaction_status"])
            self.assertTrue(result["workspace_committed"])
            self.assertTrue(result["output_committed"])
            self.assertEqual("PASS", result["visual_quality_gate"]["qa_gate"])
            self.assertEqual(b"new-master", (workspace / "editable" / "hero.png").read_bytes())
            self.assertTrue((output / "hires.txt").is_file())

    def test_visual_quality_failure_blocks_before_candidate_build(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = root / "pack"
            workspace = root / "MasterWorkspace"
            kit = root / "CurrentImpactSprint"
            output = root / "output"
            pack.mkdir()
            (workspace / "editable").mkdir(parents=True)
            (workspace / "original").mkdir(parents=True)
            (kit / "editable").mkdir(parents=True)
            original = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
            for y in range(2, 14):
                for x in range(2, 14):
                    original.putpixel((x, y), ((x * 17) % 255, (y * 19) % 255, 180, 255))
            original.save(workspace / "editable" / "hero.png")
            original.save(workspace / "original" / "hero.png")
            old_sha = tx._sha256(workspace / "editable" / "hero.png")
            Image.new("RGBA", (16, 16), (0, 0, 0, 0)).save(kit / "editable" / "001_hero.png")
            (workspace / "ART_STATE.csv").write_text("state-before\n", encoding="utf-8")
            (workspace / "MASTER_TILES.json").write_text("{}\n", encoding="utf-8")
            (kit / "ART_SPRINT_KIT.json").write_text(json.dumps({
                "schema": 2,
                "items": [{
                    "master_file": "hero.png",
                    "kit_file": "001_hero.png",
                    "workspace_editable_sha256_at_export": old_sha,
                }],
            }), encoding="utf-8")

            with patch.object(tx, "import_sprint_kit", side_effect=self._fake_import), \
                 patch.object(tx, "apply_workspace") as apply_mock:
                result = tx.transactional_finish_sprint(pack, workspace, kit, output, overwrite=True)

            self.assertEqual("BLOCKED_VISUAL_QA", result["transaction_status"])
            self.assertEqual("FAIL", result["visual_quality_gate"]["qa_gate"])
            self.assertIn("FULLY_TRANSPARENT", result["visual_quality_gate"]["blocker_codes"])
            apply_mock.assert_not_called()
            self.assertEqual(old_sha, tx._sha256(workspace / "editable" / "hero.png"))
            self.assertFalse(output.exists())
            self.assertTrue((kit / "ART_VISUAL_QUALITY_GATE.json").is_file())

    def test_pixel_qa_failure_keeps_authoritative_state_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            pack, workspace, kit, output = self._fixture(Path(td))
            output.mkdir()
            (output / "old.txt").write_text("keep-me", encoding="utf-8")

            def fake_apply(_pack: Path, _workspace: Path, staged_output: Path, overwrite: bool = False) -> dict:
                staged_output.mkdir(parents=True)
                (staged_output / "bad.txt").write_text("candidate", encoding="utf-8")
                return {"pixel_qa": {"qa_gate": "FAIL"}, "mapping_preserved": True}

            with patch.object(tx, "import_sprint_kit", side_effect=self._fake_import), \
                 patch.object(tx, "audit_workspace_visual_quality", return_value=PASS_VISUAL), \
                 patch.object(tx, "apply_workspace", side_effect=fake_apply):
                result = tx.transactional_finish_sprint(pack, workspace, kit, output, overwrite=True)

            self.assertEqual("BLOCKED_QA", result["transaction_status"])
            self.assertFalse(result["workspace_committed"])
            self.assertFalse(result["output_committed"])
            self.assertEqual(b"old-master", (workspace / "editable" / "hero.png").read_bytes())
            self.assertEqual("keep-me", (output / "old.txt").read_text(encoding="utf-8"))
            self.assertFalse((output / "bad.txt").exists())

    def test_mapping_preservation_failure_never_commits(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            pack, workspace, kit, output = self._fixture(Path(td))

            def fake_apply(_pack: Path, _workspace: Path, staged_output: Path, overwrite: bool = False) -> dict:
                staged_output.mkdir(parents=True)
                return {"pixel_qa": {"qa_gate": "PASS"}, "mapping_preserved": False}

            with patch.object(tx, "import_sprint_kit", side_effect=self._fake_import), \
                 patch.object(tx, "audit_workspace_visual_quality", return_value=PASS_VISUAL), \
                 patch.object(tx, "apply_workspace", side_effect=fake_apply):
                result = tx.transactional_finish_sprint(pack, workspace, kit, output, overwrite=True)

            self.assertEqual("BLOCKED_QA", result["transaction_status"])
            self.assertEqual(b"old-master", (workspace / "editable" / "hero.png").read_bytes())
            self.assertFalse(output.exists())

    def test_stale_real_workspace_is_blocked_before_candidate_build(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            pack, workspace, kit, output = self._fixture(Path(td))
            (workspace / "editable" / "hero.png").write_bytes(b"newer-workspace-edit")
            with self.assertRaisesRegex(ValueError, "stale MasterWorkspace"):
                tx.transactional_finish_sprint(pack, workspace, kit, output, overwrite=True)


if __name__ == "__main__":
    unittest.main()
