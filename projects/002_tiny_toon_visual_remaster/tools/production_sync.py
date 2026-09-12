from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from art_production import export_master_tiles, write_workboards
from art_workspace import init_workspace, scan_workspace
from hd_readiness import ensure_checklist, write_grouped_art_queue, write_readiness_dashboard
from hdpack_pipeline import analyze, write_report
from validate_hdpack import validate

QUEUE_FIELDS = (
    "priority", "tile_id", "palette", "uses", "conditional_uses", "conditions",
    "status", "art_group", "group_confidence", "notes",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _queue_key(row: dict[str, str]) -> tuple[str, str]:
    return ((row.get("tile_id") or "").strip().upper(), (row.get("palette") or "").strip().upper())


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fields=QUEUE_FIELDS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sync_art_queue(pack_dir: Path, output: Path) -> dict:
    """Regenerate the queue from the latest capture without erasing artist decisions."""
    previous_rows = _read_csv(output)
    previous = {_queue_key(row): row for row in previous_rows if all(_queue_key(row))}

    with tempfile.TemporaryDirectory() as td:
        generated = Path(td) / "queue.csv"
        write_grouped_art_queue(pack_dir, generated)
        current_rows = _read_csv(generated)

    current_keys: set[tuple[str, str]] = set()
    preserved_status = 0
    preserved_groups = 0
    preserved_notes = 0
    added = 0

    for row in current_rows:
        key = _queue_key(row)
        current_keys.add(key)
        old = previous.get(key)
        if old is None:
            added += 1
            continue

        old_status = (old.get("status") or "TODO").strip() or "TODO"
        if old_status.upper() != "TODO":
            row["status"] = old_status
            preserved_status += 1

        old_group = (old.get("art_group") or "UNASSIGNED").strip().upper() or "UNASSIGNED"
        if old_group != "UNASSIGNED":
            if old_group != (row.get("art_group") or "UNASSIGNED").strip().upper():
                row["group_confidence"] = "manual-preserved"
            row["art_group"] = old_group
            preserved_groups += 1

        old_notes = (old.get("notes") or "").strip()
        if old_notes:
            row["notes"] = old_notes
            preserved_notes += 1

    retired_rows = [row for key, row in previous.items() if key not in current_keys]
    _write_csv(output, current_rows)
    retired_path = output.with_name(output.stem + "_RETIRED.csv")
    if retired_rows:
        _write_csv(retired_path, retired_rows)
    elif retired_path.exists():
        retired_path.unlink()

    result = {
        "rows": len(current_rows),
        "added": added,
        "retired": len(retired_rows),
        "preserved_non_todo_status": preserved_status,
        "preserved_groups": preserved_groups,
        "preserved_notes": preserved_notes,
        "queue": str(output),
        "retired_queue": str(retired_path) if retired_rows else None,
    }
    output.with_name(output.stem + "_SYNC.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def _safe_master_name(master: dict) -> str:
    group = (master.get("group") or "UNASSIGNED").replace("/", "_")
    tile = (master.get("tile_id") or "TILE").replace("/", "_")
    palette = (master.get("palette") or "PAL")[:8].replace("/", "_")
    return f"MASTER_H{master['exact_hash'][:12]}_{group}_{tile}_{palette}.png"


def sync_master_workspace(pack_dir: Path, workspace: Path, queue: Path | None = None) -> dict:
    """Update master targets for a newer capture while preserving edited masters by exact pixel hash."""
    manifest_path = workspace / "MASTER_TILES.json"
    if not manifest_path.is_file():
        info = init_workspace(pack_dir, workspace, queue, overwrite=False)
        scan = scan_workspace(workspace)
        result = {
            "mode": "initialized",
            "new_masters": info["master_count"],
            "preserved_masters": 0,
            "preserved_edited_masters": 0,
            "retired_masters": 0,
            "scan": scan,
        }
        (workspace / "WORKSPACE_SYNC.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    old_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    old_by_hash = {item["exact_hash"]: item for item in old_manifest.get("masters", []) if item.get("exact_hash")}

    originals = workspace / "original"
    editable = workspace / "editable"
    originals.mkdir(parents=True, exist_ok=True)
    editable.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        fresh = export_master_tiles(pack_dir, temp, queue)
        fresh_masters = fresh.get("masters", [])

        current_hashes: set[str] = set()
        preserved = 0
        preserved_edited = 0
        new_count = 0
        rewritten: list[dict] = []

        for master in fresh_masters:
            exact_hash = master["exact_hash"]
            current_hashes.add(exact_hash)
            old = old_by_hash.get(exact_hash)
            if old:
                stable_name = old["file"]
                preserved += 1
            else:
                stable_name = _safe_master_name(master)
                new_count += 1

            fresh_source = temp / master["file"]
            target_original = originals / stable_name
            target_editable = editable / stable_name

            old_original = originals / old["file"] if old else None
            old_editable = editable / old["file"] if old else None
            was_edited = bool(
                old_original and old_editable and old_original.is_file() and old_editable.is_file()
                and _sha256(old_original) != _sha256(old_editable)
            )

            shutil.copy2(fresh_source, target_original)
            if old_editable and old_editable.is_file():
                if old_editable != target_editable:
                    shutil.copy2(old_editable, target_editable)
                if was_edited:
                    preserved_edited += 1
            elif not target_editable.is_file():
                shutil.copy2(fresh_source, target_editable)

            updated = dict(master)
            updated["file"] = stable_name
            rewritten.append(updated)

    retired_hashes = sorted(set(old_by_hash) - current_hashes)
    new_manifest = {"masters": rewritten}
    manifest_path.write_text(json.dumps(new_manifest, indent=2), encoding="utf-8")

    info_path = workspace / "WORKSPACE.json"
    info = {}
    if info_path.is_file():
        try:
            info = json.loads(info_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            info = {}
    info.update({
        "source_pack": str(pack_dir.resolve()),
        "master_count": len(rewritten),
        "resume_safe_sync": True,
        "important": "Existing editable masters are preserved by exact source-pixel hash when the capture grows.",
    })
    info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")

    scan = scan_workspace(workspace)
    result = {
        "mode": "synchronized",
        "masters": len(rewritten),
        "new_masters": new_count,
        "preserved_masters": preserved,
        "preserved_edited_masters": preserved_edited,
        "retired_masters": len(retired_hashes),
        "retired_exact_hashes": retired_hashes,
        "scan": scan,
    }
    (workspace / "WORKSPACE_SYNC.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def prepare_incremental(pack_dir: Path, project_root: Path) -> dict:
    """One resume-safe command for importing a newer Mesen capture into an existing production workspace."""
    errors, warnings, _ = validate(pack_dir)
    if errors:
        raise ValueError("Capture failed validation: " + "; ".join(errors))
    stats = analyze(pack_dir)
    if stats.scale < 4:
        raise ValueError(f"Capture scale is {stats.scale}x; Project #002 production target is 4x")

    artwork = project_root / "Artwork"
    queue = artwork / "ART_QUEUE.csv"
    master_workspace = artwork / "MasterWorkspace"
    workboards = artwork / "Workboards"
    checklist = project_root / "HD_READINESS_CHECKLIST.json"
    reports = project_root / "Reports"
    reports.mkdir(parents=True, exist_ok=True)

    queue_sync = sync_art_queue(pack_dir, queue)
    workspace_sync = sync_master_workspace(pack_dir, master_workspace, queue)
    boards = write_workboards(pack_dir, workboards, queue)
    capture_report = write_report(pack_dir, reports / "CAPTURE_REPORT.html")
    ensure_checklist(checklist)
    readiness_report = write_readiness_dashboard(
        pack_dir, checklist, queue, reports / "HD_READINESS.html"
    )

    result = {
        "capture": str(pack_dir.resolve()),
        "scale": stats.scale,
        "tile_rules": stats.tile_rules,
        "images": len(stats.images),
        "warnings": warnings,
        "queue_sync": queue_sync,
        "workspace_sync": workspace_sync,
        "workboards": boards,
        "capture_report": str(capture_report),
        "readiness_report": str(readiness_report),
        "next_action": (
            "Continue editing preserved/new masters in Artwork/MasterWorkspace/editable, then scan/apply."
            if workspace_sync["scan"]["todo"] or workspace_sync["scan"]["edited"]
            else "Capture more game states in MesenCE."
        ),
    }
    (reports / "PRODUCTION_SYNC.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 resume-safe incremental production sync")
    commands = parser.add_subparsers(dest="command", required=True)

    queue = commands.add_parser("queue")
    queue.add_argument("pack", type=Path)
    queue.add_argument("output", type=Path)

    masters = commands.add_parser("masters")
    masters.add_argument("pack", type=Path)
    masters.add_argument("workspace", type=Path)
    masters.add_argument("--queue", type=Path)

    all_cmd = commands.add_parser("all")
    all_cmd.add_argument("pack", type=Path)
    all_cmd.add_argument("project_root", type=Path)

    args = parser.parse_args()
    if args.command == "queue":
        result = sync_art_queue(args.pack, args.output)
    elif args.command == "masters":
        result = sync_master_workspace(args.pack, args.workspace, args.queue)
    else:
        result = prepare_incremental(args.pack, args.project_root)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
