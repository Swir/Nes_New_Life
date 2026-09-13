from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from animation_workbench import semantic_family
from visual_completion_matrix import FINAL_STATES

CHARACTER_GROUPS = {"PLAYER", "ENEMY", "BOSS"}


def _read_states(workspace: Path) -> tuple[dict[tuple[str, str], dict], dict[str, dict]]:
    path = Path(workspace) / "ART_STATE.csv"
    if not path.is_file():
        raise ValueError("MasterWorkspace is missing ART_STATE.csv")
    by_key: dict[tuple[str, str], dict] = {}
    by_file: dict[str, dict] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            tile = (row.get("tile_id") or "").upper()
            palette = (row.get("palette") or "").upper()
            master_file = row.get("master_file") or ""
            if tile and palette:
                by_key[(tile, palette)] = row
            if master_file:
                by_file[master_file] = row
    return by_key, by_file


def _manifest_index(workspace: Path) -> tuple[dict[str, dict], dict[str, set[str]], dict[str, set[str]]]:
    path = Path(workspace) / "MASTER_TILES.json"
    if not path.is_file():
        raise ValueError("MasterWorkspace is missing MASTER_TILES.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    masters: dict[str, dict] = {}
    families: dict[str, set[str]] = defaultdict(set)
    palette_sets: dict[str, set[str]] = defaultdict(set)
    for master in payload.get("masters", []):
        name = str(master.get("file") or "")
        if not name:
            continue
        masters[name] = master
        group = str(master.get("group") or "UNASSIGNED").upper()
        if group not in CHARACTER_GROUPS:
            continue
        tile_id = str(master.get("tile_id") or "").upper()
        if tile_id:
            palette_sets[tile_id].add(name)
        for target in master.get("targets", []):
            condition = str(target.get("condition") or "")
            if not condition:
                continue
            family = semantic_family(condition)
            if family and family != "UNCONDITIONED":
                families[family].add(name)
    return masters, families, palette_sets


def _status_is_final(row: dict) -> bool:
    return str(row.get("status") or "TODO").upper() in FINAL_STATES


def _peer_row(master: dict, state: dict, seed: dict, reasons: list[str]) -> dict:
    conditions = {
        str(target.get("condition") or "")
        for target in master.get("targets", [])
        if target.get("condition")
    }
    return {
        "group": str(master.get("group") or seed.get("group") or "UNASSIGNED").upper(),
        "tile_id": str(master.get("tile_id") or state.get("tile_id") or "").upper(),
        "palette": str(master.get("palette") or state.get("palette") or "").upper(),
        "status": str(state.get("status") or "TODO").upper(),
        "uses": len(master.get("targets", [])) or int(seed.get("uses") or 1),
        "condition_count": len(conditions),
        "visual_variants": 1,
        "impact_score": max(0, int(seed.get("impact_score") or 0) - 1),
        "reasons": list(dict.fromkeys([*seed.get("reasons", []), *reasons])),
        "master_file": str(master.get("file") or state.get("master_file") or ""),
        "family_bundle_member": True,
        "seed_tile_id": seed.get("tile_id"),
        "seed_palette": seed.get("palette"),
    }


def build_family_aware_batch(seed_rows: list[dict], workspace: Path, requested_batch_size: int) -> dict:
    """Expand high-impact character seeds into atomic animation/palette-family bundles.

    Character families are never partially selected merely to satisfy the nominal batch
    size. If the first highest-impact family is larger than the requested batch, that
    one family is allowed to overflow so the artist can redraw it coherently. Later
    families that do not fit are deferred as complete units.
    """
    workspace = Path(workspace)
    states_by_key, states_by_file = _read_states(workspace)
    masters, families, palette_sets = _manifest_index(workspace)

    family_names_by_file: dict[str, set[str]] = defaultdict(set)
    for family, names in families.items():
        for name in names:
            family_names_by_file[name].add(family)

    selected: list[dict] = []
    selected_keys: set[tuple[str, str]] = set()
    selected_files: set[str] = set()
    deferred: list[dict] = []
    bundle_summaries: list[dict] = []
    requested_batch_size = max(1, int(requested_batch_size))

    def row_key(row: dict) -> tuple[str, str]:
        return (str(row.get("tile_id") or "").upper(), str(row.get("palette") or "").upper())

    def add(row: dict) -> None:
        key = row_key(row)
        if not all(key) or key in selected_keys:
            return
        selected.append(dict(row))
        selected_keys.add(key)
        master_file = str(row.get("master_file") or "")
        if not master_file:
            state = states_by_key.get(key, {})
            master_file = str(state.get("master_file") or "")
            if master_file:
                selected[-1]["master_file"] = master_file
        if master_file:
            selected_files.add(master_file)

    for seed in seed_rows:
        key = row_key(seed)
        if key in selected_keys:
            continue
        state = states_by_key.get(key, {})
        master_file = str(state.get("master_file") or "")
        group = str(seed.get("group") or "UNASSIGNED").upper()
        bundle: list[dict] = [dict(seed)]
        bundle_files: set[str] = {master_file} if master_file else set()
        family_names = sorted(family_names_by_file.get(master_file, set())) if group in CHARACTER_GROUPS else []

        if group in CHARACTER_GROUPS and master_file:
            peer_files: set[str] = set()
            for family in family_names:
                peer_files.update(families.get(family, set()))
            tile_id = str(masters.get(master_file, {}).get("tile_id") or key[0]).upper()
            peer_files.update(palette_sets.get(tile_id, set()))
            peer_files.discard(master_file)
            for peer_file in sorted(peer_files):
                peer_state = states_by_file.get(peer_file)
                peer_master = masters.get(peer_file)
                if not peer_state or not peer_master or _status_is_final(peer_state):
                    continue
                peer_key = (
                    str(peer_master.get("tile_id") or peer_state.get("tile_id") or "").upper(),
                    str(peer_master.get("palette") or peer_state.get("palette") or "").upper(),
                )
                if not all(peer_key) or peer_key in selected_keys:
                    continue
                reasons = []
                shared = sorted(family_names_by_file.get(peer_file, set()).intersection(family_names))
                if shared:
                    reasons.append("animation-family:" + "+".join(shared))
                if peer_key[0] == tile_id and peer_file != master_file:
                    reasons.append("palette-sibling")
                bundle.append(_peer_row(peer_master, peer_state, seed, reasons or ["character-family-peer"]))
                bundle_files.add(peer_file)

        unique_bundle: list[dict] = []
        seen_bundle: set[tuple[str, str]] = set()
        for row in bundle:
            candidate_key = row_key(row)
            if candidate_key in selected_keys or candidate_key in seen_bundle or not all(candidate_key):
                continue
            unique_bundle.append(row)
            seen_bundle.add(candidate_key)

        if not unique_bundle:
            continue
        fits = len(selected) + len(unique_bundle) <= requested_batch_size
        allow_first_family_overflow = not selected and len(unique_bundle) > requested_batch_size and group in CHARACTER_GROUPS
        if not fits and not allow_first_family_overflow:
            deferred.append({
                "seed_tile_id": key[0],
                "seed_palette": key[1],
                "group": group,
                "family_names": family_names,
                "bundle_size": len(unique_bundle),
                "reason": "atomic-family-does-not-fit-current-batch",
            })
            continue

        for row in unique_bundle:
            add(row)
        bundle_summaries.append({
            "seed_tile_id": key[0],
            "seed_palette": key[1],
            "group": group,
            "family_names": family_names,
            "bundle_size": len(unique_bundle),
            "atomic_family": group in CHARACTER_GROUPS and len(unique_bundle) > 1,
            "overflowed_nominal_batch": allow_first_family_overflow,
        })
        if len(selected) >= requested_batch_size:
            break

    for index, row in enumerate(selected, 1):
        row["batch_order"] = index
        row.setdefault("family_bundle_member", False)
        row.setdefault("seed_tile_id", row.get("tile_id"))
        row.setdefault("seed_palette", row.get("palette"))

    return {
        "schema": "swir.project002.family-aware-art-batch.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "requested_batch_size": requested_batch_size,
        "seed_count": len(seed_rows),
        "selected_count": len(selected),
        "family_bundle_count": sum(1 for item in bundle_summaries if item["atomic_family"]),
        "deferred_family_count": len(deferred),
        "selection": selected,
        "bundles": bundle_summaries,
        "deferred": deferred,
        "policy": "PLAYER/ENEMY/BOSS animation and palette peers are selected atomically; already-final masters are never reopened automatically.",
    }


def write_family_aware_batch(plan: dict, output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "FAMILY_AWARE_ART_BATCH.json"
    csv_path = output_dir / "FAMILY_AWARE_ART_BATCH.csv"
    json_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    fields = [
        "batch_order", "impact_score", "group", "tile_id", "palette", "status", "uses",
        "condition_count", "visual_variants", "family_bundle_member", "seed_tile_id", "seed_palette", "reasons",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in plan.get("selection", []):
            writer.writerow({**{field: row.get(field, "") for field in fields}, "reasons": " | ".join(row.get("reasons", []))})
    return {"json": str(json_path), "csv": str(csv_path)}
