from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from release_candidate import pack_fingerprint


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_mesence_args(rom_path: Path, *, fullscreen: bool = True) -> list[str]:
    """Build the legacy Mesen/MesenCE command line without copying the ROM."""
    rom = str(Path(rom_path))
    return (["/fullscreen"] if fullscreen else []) + [rom]


def record_fullscreen_evidence(
    pack_dir: Path,
    output_path: Path,
    *,
    emulator: str,
    rom_name: str,
    verified: bool,
    method: str,
    attempts: int = 1,
    details: str = "",
) -> dict:
    pack = Path(pack_dir)
    if not (pack / "hires.txt").is_file():
        raise ValueError("Cannot bind fullscreen evidence to a pack without hires.txt")
    result = {
        "schema": 1,
        "recorded_utc": _now(),
        "pack_fingerprint": pack_fingerprint(pack),
        "fullscreen_verified": bool(verified),
        "method": str(method),
        "attempts": int(attempts),
        "emulator": str(emulator),
        "rom_name": Path(rom_name).name,
        "details": str(details),
        "important_note": (
            "This evidence proves only that the exact HD-pack build was launched in a window matching the active "
            "monitor bounds. It does not prove full-game capture or visual regression completion."
        ),
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def fullscreen_evidence_status(pack_dir: Path, evidence_path: Path) -> dict:
    report = Path(evidence_path)
    current = pack_fingerprint(Path(pack_dir))
    result = {
        "exists": report.is_file(),
        "gate": "BLOCKED",
        "fullscreen_verified": False,
        "fingerprint_matches": False,
        "current_pack_fingerprint": current,
        "recorded_pack_fingerprint": None,
        "method": None,
        "attempts": 0,
        "path": str(report),
    }
    if not report.is_file():
        return result
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return result
    result["fullscreen_verified"] = bool(data.get("fullscreen_verified", False))
    result["recorded_pack_fingerprint"] = data.get("pack_fingerprint")
    result["fingerprint_matches"] = data.get("pack_fingerprint") == current
    result["method"] = data.get("method")
    result["attempts"] = int(data.get("attempts", 0) or 0)
    if result["fullscreen_verified"] and result["fingerprint_matches"]:
        result["gate"] = "PASS"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 fullscreen launch evidence")
    commands = parser.add_subparsers(dest="command", required=True)

    args_cmd = commands.add_parser("args")
    args_cmd.add_argument("rom", type=Path)
    args_cmd.add_argument("--windowed", action="store_true")

    record = commands.add_parser("record")
    record.add_argument("pack", type=Path)
    record.add_argument("output", type=Path)
    record.add_argument("--emulator", required=True)
    record.add_argument("--rom-name", required=True)
    record.add_argument("--verified", choices=["true", "false"], required=True)
    record.add_argument("--method", required=True)
    record.add_argument("--attempts", type=int, default=1)
    record.add_argument("--details", default="")

    status = commands.add_parser("status")
    status.add_argument("pack", type=Path)
    status.add_argument("evidence", type=Path)
    ns = parser.parse_args()

    if ns.command == "args":
        print(json.dumps(build_mesence_args(ns.rom, fullscreen=not ns.windowed)))
        return 0
    if ns.command == "record":
        result = record_fullscreen_evidence(
            ns.pack,
            ns.output,
            emulator=ns.emulator,
            rom_name=ns.rom_name,
            verified=ns.verified == "true",
            method=ns.method,
            attempts=ns.attempts,
            details=ns.details,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["fullscreen_verified"] else 2
    result = fullscreen_evidence_status(ns.pack, ns.evidence)
    print(json.dumps(result, indent=2))
    return 0 if result["gate"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
