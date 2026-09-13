from __future__ import annotations

import json
from pathlib import Path


class WorkbenchError(RuntimeError):
    pass


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkbenchError(f"Missing required file: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise WorkbenchError(f"Invalid JSON: {path.name}") from exc


def _safe_relative(path_text: str) -> Path:
    rel = Path(path_text)
    if not path_text or rel.is_absolute() or ".." in rel.parts:
        raise WorkbenchError(f"Unsafe workbench path: {path_text}")
    return rel


def _item_key(row: dict) -> tuple[str, str]:
    return (str(row.get("tile_id", "")).upper(), str(row.get("palette", "")).upper())


def resolve_active_family_workbench(kit_dir: Path) -> dict:
    """Resolve the highest-priority active PLAYER/ENEMY/BOSS family in a sprint kit.

    The result contains metadata and local relative paths only. It never reads or
    serializes PNG bytes and therefore remains safe to use as operational state.
    """
    kit_dir = Path(kit_dir)
    sprint = _load_json(kit_dir / "ART_SPRINT_KIT.json")
    boards = _load_json(kit_dir / "FAMILY_CONTACT_BOARDS.json")

    items = sprint.get("items") or sprint.get("batch") or []
    priority_by_key: dict[tuple[str, str], int] = {}
    item_by_key: dict[tuple[str, str], dict] = {}
    for item in items:
        try:
            key = _item_key(item)
            priority = int(item.get("priority", 10**9))
            if key not in priority_by_key or priority < priority_by_key[key]:
                priority_by_key[key] = priority
                item_by_key[key] = item
        except (TypeError, ValueError):
            continue

    candidates = []
    for family in boards.get("families", []):
        rel_board = _safe_relative(str(family.get("file", "")))
        board_path = kit_dir / rel_board
        if not board_path.is_file():
            continue
        members = family.get("metrics") or []
        member_keys = {_item_key(member) for member in members}
        member_priorities = [
            priority_by_key.get(_item_key(member), int(member.get("priority", 10**9)))
            for member in members
        ]
        editable_files = []
        for key in member_keys:
            item = item_by_key.get(key)
            if not item:
                continue
            kit_file = item.get("kit_file")
            if kit_file:
                editable_files.append(str(_safe_relative(str(kit_file))))
        candidates.append(
            {
                "family": str(family.get("family", "UNKNOWN")),
                "board": rel_board.as_posix(),
                "priority": min(member_priorities) if member_priorities else 10**9,
                "members": int(family.get("members", len(members)) or len(members)),
                "editable_files": sorted(set(editable_files)),
            }
        )

    if not candidates:
        raise WorkbenchError("No usable PLAYER/ENEMY/BOSS family contact board exists in CurrentImpactSprint.")

    active = min(candidates, key=lambda row: (row["priority"], row["family"]))
    result = {
        "schema": 1,
        "status": "ACTIVE_FAMILY_READY",
        "family": active["family"],
        "priority": active["priority"],
        "members": active["members"],
        "board": active["board"],
        "editable_dir": "editable",
        "editable_files": active["editable_files"],
        "candidate_family_count": len(candidates),
        "next_action": "Redraw this family together, then finish through transactional QA before playtest.",
    }
    return result


def write_active_state(result: dict, kit_dir: Path) -> Path:
    out = Path(kit_dir) / "ACTIVE_FAMILY_WORKBENCH.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return out
