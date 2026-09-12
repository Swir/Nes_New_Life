from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from studio_grade_art_pass import apply_studio_grade_pass  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StudioGradeArtPassTests(unittest.TestCase):
    @staticmethod
    def _make_kit(root: Path, *, count: int = 1, group: str = "PLAYER") -> Path:
        kit = root / "kit"
        editable = kit / "editable"
        reference = kit / "reference"
        editable.mkdir(parents=True)
        reference.mkdir(parents=True)
        items = []
        for index in range(count):
            name = f"{index + 1:03d}_master_{index}.png"
            image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
            for y in range(4, 28):
                for x in range(4, 28):
                    r = 35 + ((x * 7 + index * 3) % 120)
                    g = 70 + ((y * 5 + index * 2) % 110)
                    b = 120 + ((x + y) % 80)
                    image.putpixel((x, y), (r, g, b, 255))
            image.save(editable / name)
            image.save(reference / name)
            items.append({
                "kit_file": name,
                "master_file": f"master_{index}.png",
                "group": group,
                "tile_id": f"{0x2E + index:02X}",
                "palette": "FF16360F",
                "workspace_editable_sha256_at_export": sha(editable / name),
            })
        (kit / "ART_SPRINT_KIT.json").write_text(json.dumps({"selection_mode": "test", "items": items}), encoding="utf-8")
        return kit

    def test_pass_preserves_dimensions_and_alpha_and_changes_rgb(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            kit = self._make_kit(Path(td))
            target = next((kit / "editable").glob("*.png"))
            with Image.open(target) as before:
                size = before.size
                alpha = before.convert("RGBA").getchannel("A").tobytes()
                before_rgb = before.convert("RGB").tobytes()
            result = apply_studio_grade_pass(kit)
            self.assertEqual(result["applied"], 1)
            with Image.open(target) as after:
                self.assertEqual(after.size, size)
                self.assertEqual(after.convert("RGBA").getchannel("A").tobytes(), alpha)
                self.assertNotEqual(after.convert("RGB").tobytes(), before_rgb)
            self.assertTrue((kit / "STUDIO_GRADE_ART_PASS.json").is_file())
            self.assertTrue((kit / "STUDIO_GRADE_ART_PASS.html").is_file())
            self.assertEqual(len(list((kit / "quality_candidates").rglob("*.png"))), 3)

    def test_existing_artist_edit_is_preserved_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            kit = self._make_kit(Path(td))
            target = next((kit / "editable").glob("*.png"))
            with Image.open(target) as image:
                edited = image.convert("RGBA")
            edited.putpixel((10, 10), (255, 20, 20, 255))
            edited.save(target)
            edited_sha = sha(target)
            result = apply_studio_grade_pass(kit)
            self.assertEqual(result["applied"], 0)
            self.assertEqual(result["preserved_existing_edits"], 1)
            self.assertEqual(sha(target), edited_sha)

    def test_force_can_replace_existing_sprint_edit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            kit = self._make_kit(Path(td))
            target = next((kit / "editable").glob("*.png"))
            with Image.open(target) as image:
                edited = image.convert("RGBA")
            edited.putpixel((10, 10), (255, 20, 20, 255))
            edited.save(target)
            edited_sha = sha(target)
            result = apply_studio_grade_pass(kit, force=True)
            self.assertEqual(result["applied"], 1)
            self.assertNotEqual(sha(target), edited_sha)

    def test_identical_assets_in_same_group_receive_deterministic_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            kit = self._make_kit(root, count=2, group="BOSS")
            # Make second asset byte-identical to the first and repair export hash.
            files = sorted((kit / "editable").glob("*.png"))
            refs = sorted((kit / "reference").glob("*.png"))
            files[1].write_bytes(files[0].read_bytes())
            refs[1].write_bytes(refs[0].read_bytes())
            manifest_path = kit / "ART_SPRINT_KIT.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["items"][1]["workspace_editable_sha256_at_export"] = sha(files[1])
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = apply_studio_grade_pass(kit)
            self.assertEqual(result["applied"], 2)
            self.assertEqual(sha(files[0]), sha(files[1]))
            selected = [row["selected_variant"] for row in result["records"]]
            self.assertEqual(selected[0], selected[1])

    def test_metadata_dashboard_does_not_embed_image_payload(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            kit = self._make_kit(Path(td))
            apply_studio_grade_pass(kit)
            dashboard = (kit / "STUDIO_GRADE_ART_PASS.html").read_text(encoding="utf-8")
            self.assertNotIn("data:image", dashboard.lower())
            self.assertNotIn("base64", dashboard.lower())


if __name__ == "__main__":
    unittest.main()
