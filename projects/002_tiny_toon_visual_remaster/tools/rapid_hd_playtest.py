from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from art_workspace import apply_workspace
from auto_art_pass import seed_baseline_art
from hd_readiness import ensure_checklist, write_readiness_dashboard
from production_sync import prepare_incremental
from validate_hdpack import validate

BANNED_SUFFIXES = {
    ".nes", ".fds", ".unf", ".unif", ".sav", ".srm", ".state", ".mst",
    ".ips", ".bps", ".ups", ".xdelta", ".xdelta3",
}
GENERATED_SUFFIXES = {".json", ".html", ".csv"}


def _assert_runtime_safe(pack_dir: Path) -> None:
    offenders = [
        str(path.relative_to(pack_dir))
        for path in pack_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in BANNED_SUFFIXES
    ]
    if offenders:
        raise ValueError("Refusing playtest deployment; prohibited file(s): " + ", ".join(offenders))


def _copy_runtime_pack(source: Path, destination: Path) -> int:
    """Copy only runtime HD-pack assets, excluding generated reports/metadata."""
    _assert_runtime_safe(source)
    copied = 0
    for item in source.rglob("*"):
        if not item.is_file():
            continue
        relative = item.relative_to(source)
        if item.suffix.lower() in GENERATED_SUFFIXES:
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        copied += 1
    return copied


def deploy_hdpack(
    pack_dir: Path,
    rom_name: str,
    hdpacks_root: Path,
    *,
    keep_backup: bool = True,
) -> dict:
    """Atomically install a validated pack into MesenCE/HdPacks/<ROM stem>."""
    errors, warnings, stats = validate(pack_dir)
    if errors:
        raise ValueError("Refusing deployment; HD pack validation failed: " + "; ".join(errors))
    _assert_runtime_safe(pack_dir)

    rom_stem = Path(rom_name).stem.strip()
    if not rom_stem or rom_stem in {".", ".."}:
        raise ValueError("A valid ROM file name is required for MesenCE HD-pack deployment")

    hdpacks_root.mkdir(parents=True, exist_ok=True)
    destination = hdpacks_root / rom_stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = hdpacks_root / f"{rom_stem}__backup_{timestamp}"

    with tempfile.TemporaryDirectory(dir=str(hdpacks_root), prefix=f".{rom_stem}_staging_") as td:
        staging = Path(td)
        copied = _copy_runtime_pack(pack_dir, staging)
        if not (staging / "hires.txt").is_file():
            raise ValueError("Runtime staging pack is missing hires.txt")

        if destination.exists():
            if keep_backup:
                if backup.exists():
                    shutil.rmtree(backup)
                destination.replace(backup)
            else:
                shutil.rmtree(destination)
        staging.replace(destination)

    result = {
        "destination": str(destination),
        "backup": str(backup) if keep_backup and backup.exists() else None,
        "runtime_files_copied": copied,
        "validation_warnings": warnings,
        "validation_stats": stats,
        "rom_stem": rom_stem,
    }
    return result


def build_playtest(
    capture_dir: Path,
    project_root: Path,
    *,
    baseline_profile: str = "group-aware",
    seed_baseline: bool = True,
    rom_name: str | None = None,
    hdpacks_root: Path | None = None,
    keep_backup: bool = True,
) -> dict:
    """One command from a local Mesen capture to a QA-gated playable HD pack.

    Existing manual master edits survive incremental capture sync. The automatic baseline
    touches only still-unedited masters unless the caller explicitly uses lower-level tools.
    """
    capture_dir = Path(capture_dir)
    project_root = Path(project_root)
    reports = project_root / "Reports"
    reports.mkdir(parents=True, exist_ok=True)

    sync = prepare_incremental(capture_dir, project_root)
    master_workspace = project_root / "Artwork" / "MasterWorkspace"
    queue = project_root / "Artwork" / "ART_QUEUE.csv"
    checklist = project_root / "HD_READINESS_CHECKLIST.json"
    ensure_checklist(checklist)

    baseline = None
    if seed_baseline:
        baseline = seed_baseline_art(master_workspace, profile=baseline_profile, force=False)

    output = project_root / "ModernizedPack" / "playtest_current"
    apply = apply_workspace(capture_dir, master_workspace, output, overwrite=True)

    errors, warnings, stats = validate(output)
    if errors:
        raise ValueError("Final playtest pack validation failed: " + "; ".join(errors))
    if not apply.get("mapping_preserved"):
        raise ValueError("Final playtest pack changed hires.txt mappings")
    qa = apply.get("pixel_qa") or {}
    if qa.get("qa_gate") != "PASS":
        raise ValueError("Final playtest pack did not pass pixel QA")

    readiness_path = reports / "HD_READINESS_PLAYTEST.html"
    write_readiness_dashboard(output, checklist, queue, readiness_path)

    deployment = None
    if rom_name and hdpacks_root:
        deployment = deploy_hdpack(output, rom_name, Path(hdpacks_root), keep_backup=keep_backup)

    result = {
        "capture": str(capture_dir.resolve()),
        "project_root": str(project_root.resolve()),
        "output_pack": str(output.resolve()),
        "sync": sync,
        "baseline": baseline,
        "apply": apply,
        "validation": {"errors": errors, "warnings": warnings, "stats": stats},
        "readiness_report": str(readiness_path.resolve()),
        "deployment": deployment,
        "playtest_ready": True,
        "important": (
            "PLAYTEST READY means the currently captured content produced a structurally valid, mapping-preserved, "
            "pixel-QA-passed HD pack. It does not claim the whole game has been captured or final artwork is complete."
        ),
    }
    (reports / "RAPID_HD_PLAYTEST.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def default_mesence_hdpacks() -> Path:
    """Best-effort conventional Windows path; callers may override it."""
    return Path.home() / "Documents" / "MesenCE" / "HdPacks"


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 one-click capture → QA-gated MesenCE HD playtest")
    parser.add_argument("capture", type=Path, help="Local MesenCE HD Pack Builder capture folder")
    parser.add_argument("project_root", type=Path, help="Local Project #002 workspace root")
    parser.add_argument(
        "--profile",
        choices=["group-aware", "balanced", "cartoon", "dramatic", "painterly", "crisp", "vivid"],
        default="group-aware",
    )
    parser.add_argument("--no-baseline", action="store_true", help="Do not seed untouched masters")
    parser.add_argument("--rom-name", help="ROM filename; enables direct MesenCE deployment when supplied")
    parser.add_argument("--hdpacks-root", type=Path, help="MesenCE HdPacks directory")
    parser.add_argument("--no-backup", action="store_true", help="Replace existing installed pack without backup")
    args = parser.parse_args()

    hdpacks_root = args.hdpacks_root
    if args.rom_name and hdpacks_root is None:
        hdpacks_root = default_mesence_hdpacks()

    result = build_playtest(
        args.capture,
        args.project_root,
        baseline_profile=args.profile,
        seed_baseline=not args.no_baseline,
        rom_name=args.rom_name,
        hdpacks_root=hdpacks_root,
        keep_backup=not args.no_backup,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
