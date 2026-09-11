from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from rom_probe import export_chr, parse_rom


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a safe local Tiny Toon visual-remaster workspace.")
    parser.add_argument("rom", help="Path to user-supplied .nes ROM")
    parser.add_argument("--output", type=Path, default=Path("work"), help="Workspace root")
    parser.add_argument("--no-chr", action="store_true", help="Skip local CHR reference export")
    args = parser.parse_args()
    try:
        info, data = parse_rom(args.rom)
        root = args.output.resolve() / Path(info.filename).stem
        pack, artwork, reference = root / "MesenPack", root / "Artwork", root / "reference_chr"
        pack.mkdir(parents=True, exist_ok=True)
        artwork.mkdir(parents=True, exist_ok=True)
        metadata = asdict(info)
        metadata["rom_copied_to_workspace"] = False
        metadata["note"] = "The commercial ROM is intentionally not copied into this workspace."
        (root / "ROM_INFO.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        (pack / "README_FIRST.txt").write_text(
            "Use Mesen 2 -> Tools -> HD Pack Builder with your local ROM.\n"
            "Record the game thoroughly, then put the generated hires.txt and PNG sheets in this folder.\n"
            "Do not publish raw capture sheets made from commercial graphics.\n", encoding="utf-8")
        (artwork / "README.txt").write_text(
            "Create replacement/remaster artwork here. Keep editable source files separate from Mesen capture sheets.\n",
            encoding="utf-8")
        (root / "CONTROLS.txt").write_text(
            "Recommended Mesen input mapping\nArrow keys = D-pad\nZ = NES A\nX = NES B\nEnter = Start\nRight Shift = Select\nEsc = Mesen/menu\n",
            encoding="utf-8")
        if not args.no_chr and info.chr_rom_bytes:
            export_chr(info, data, reference, scale=4)
        print(f"Workspace ready: {root}")
        print("ROM was NOT copied.")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
