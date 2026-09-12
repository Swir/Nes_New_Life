from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from capture_evidence_validator import SCHEMA, validate_evidence

GATE_A_HINTS = {
    "boot_title_menu": ("boot", "title", "menu", "intro"),
    "player_movement": ("player", "hero", "idle", "walk", "run", "crouch", "jump", "fall", "land"),
    "player_actions_damage_death": ("attack", "action", "hit", "hurt", "damage", "invul", "death"),
    "normal_routes_boundaries": ("stage", "level", "route", "scroll", "boundary"),
    "alternate_routes_secrets_revisits": ("alternate", "secret", "bonus", "revisit"),
    "common_enemies": ("enemy", "foe", "mob"),
    "rare_route_specific_enemies": ("rare", "route_enemy", "secret_enemy"),
    "boss_phases_attacks_death_effects": ("boss", "phase", "boss_attack", "boss_hit", "boss_death"),
    "hud_text_pause_status_result": ("hud", "ui", "menu", "pause", "status", "result", "text", "font"),
    "effects_projectiles_transitions": ("effect", "fx", "projectile", "shot", "spark", "smoke", "explosion", "transition"),
    "ending_credits_post_game": ("ending", "credits", "postgame", "post_game", "epilogue"),
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _json_files(root: Path) -> list[Path]:
    path = Path(root)
    if path.is_file():
        return [path] if path.suffix.lower() == ".json" else []
    return sorted(p for p in path.rglob("*.json") if p.is_file())


def _load(path: Path) -> tuple[dict | None, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [f"invalid JSON: {exc}"]
    if not isinstance(data, dict):
        return None, ["evidence root must be an object"]
    errors = validate_evidence(data)
    return data, errors


def _names(data: dict, key: str) -> set[str]:
    values = data.get("hd_pack", {}).get(key, [])
    return {str(value) for value in values if str(value)} if isinstance(values, list) else set()


def _groups(data: dict) -> dict[str, int]:
    raw = data.get("hd_pack", {}).get("groups", {})
    if not isinstance(raw, dict):
        return {}
    result: dict[str, int] = {}
    for key, value in raw.items():
        try:
            result[str(key)] = int(value)
        except (TypeError, ValueError):
            result[str(key)] = 0
    return result


def _capture_integrity(data: dict, fingerprint: str, mission_done: int) -> tuple[dict, list[str]]:
    raw = data.get("capture_integrity")
    if not isinstance(raw, dict):
        return {}, ["capture_integrity binding missing; regenerate evidence with current Local Capture Bridge"]
    errors: list[str] = []
    bound = str(raw.get("capture_fingerprint_sha256", ""))
    if not SHA256_RE.fullmatch(bound):
        errors.append("capture_integrity.capture_fingerprint_sha256 must be sha256 hex")
    elif bound != fingerprint:
        errors.append("capture_integrity fingerprint does not match hd_pack.capture_fingerprint")
    if raw.get("admission_gate") != "PASS":
        errors.append(f"capture integrity admission must PASS, got {raw.get('admission_gate')!r}")
    structural = raw.get("structural_blockers", [])
    if not isinstance(structural, list):
        errors.append("capture_integrity.structural_blockers must be a list")
        structural = []
    elif structural:
        errors.append(f"capture integrity has {len(structural)} structural blocker(s)")
    try:
        regression_count = int(raw.get("regression_count", 0) or 0)
    except (TypeError, ValueError):
        regression_count = -1
        errors.append("capture_integrity.regression_count must be an integer")
    if regression_count > 0:
        errors.append(f"capture integrity reports {regression_count} historical regression(s)")
    at_risk = raw.get("at_risk_missions", [])
    if not isinstance(at_risk, list):
        errors.append("capture_integrity.at_risk_missions must be a list")
        at_risk = []
    elif at_risk:
        errors.append(f"capture integrity reports {len(at_risk)} verified mission(s) at risk")

    mission = raw.get("mission_evidence")
    verified_done = 0
    unverified: list[str] = []
    bindings: list[dict] = []
    if not isinstance(mission, dict):
        errors.append("capture_integrity.mission_evidence missing")
    else:
        try:
            evidence_done = int(mission.get("done", 0) or 0)
            verified_done = int(mission.get("verified_done", 0) or 0)
        except (TypeError, ValueError):
            evidence_done = -1
            verified_done = -1
            errors.append("mission evidence counts must be integers")
        unverified_raw = mission.get("unverified_done", [])
        unverified = [str(item) for item in unverified_raw] if isinstance(unverified_raw, list) else []
        bindings_raw = mission.get("bindings", [])
        bindings = [row for row in bindings_raw if isinstance(row, dict)] if isinstance(bindings_raw, list) else []
        if evidence_done != mission_done:
            errors.append(f"mission evidence count {evidence_done} does not match capture_missions.done {mission_done}")
        if verified_done != mission_done or unverified:
            errors.append(f"only {verified_done}/{mission_done} completed missions have VERIFIED_IN_GAME fingerprint evidence")
        if len(bindings) != mission_done:
            errors.append(f"mission binding rows {len(bindings)} do not match capture_missions.done {mission_done}")
        for row in bindings:
            if not bool(row.get("verified_in_game", False)):
                continue
            fp = str(row.get("capture_fingerprint_sha256", ""))
            if not SHA256_RE.fullmatch(fp):
                errors.append(f"verified mission {row.get('mission', '')!r} has invalid session fingerprint")

    summary = {
        "schema": str(raw.get("schema", "")),
        "fingerprint": bound,
        "admission_gate": str(raw.get("admission_gate", "BLOCKED")),
        "integrity_gate": str(raw.get("integrity_gate", "BLOCKED")),
        "structural_blockers": structural,
        "regression_count": regression_count,
        "at_risk_missions": at_risk,
        "mission_verified_done": verified_done,
        "mission_unverified_done": unverified,
        "mission_bindings": bindings,
    }
    return summary, errors


def _snapshot(path: Path, data: dict, errors: list[str]) -> dict:
    hd = data.get("hd_pack", {}) if isinstance(data.get("hd_pack"), dict) else {}
    images = hd.get("images", []) if isinstance(hd.get("images"), list) else []
    missing_images = [
        str(row.get("name", ""))
        for row in images
        if isinstance(row, dict) and not bool(row.get("present", False))
    ]
    capture_gap = data.get("capture_gap", {}) if isinstance(data.get("capture_gap"), dict) else {}
    missions = data.get("capture_missions", {}) if isinstance(data.get("capture_missions"), dict) else {}
    try:
        regressions = int(capture_gap.get("regressions", 0) or 0)
    except (TypeError, ValueError):
        regressions = 0
    mission_done = int(missions.get("done", 0) or 0)
    fingerprint = str(hd.get("capture_fingerprint", ""))
    integrity, binding_errors = _capture_integrity(data, fingerprint, mission_done)
    blockers: list[str] = []
    blockers.extend(errors)
    blockers.extend(binding_errors)
    if hd.get("scale") != 4:
        blockers.append(f"HD Pack scale must be 4, got {hd.get('scale')!r}")
    if missing_images:
        blockers.append(f"{len(missing_images)} referenced capture image(s) are missing")
    if regressions:
        blockers.append(f"capture reports {regressions} regression(s)")
    return {
        "file": path.as_posix(),
        "schema": data.get("schema"),
        "generated_utc": str(data.get("generated_utc", "")),
        "fingerprint": fingerprint,
        "scale": hd.get("scale"),
        "mapping_count": int(hd.get("mapping_count", 0) or 0),
        "unique_tile_ids": int(hd.get("unique_tile_ids", 0) or 0),
        "unique_palettes": int(hd.get("unique_palettes", 0) or 0),
        "condition_count": int(hd.get("condition_count", 0) or 0),
        "groups": _groups(data),
        "tile_ids": sorted(_names(data, "tile_ids")),
        "palettes": sorted(_names(data, "palettes")),
        "condition_names": sorted(_names(data, "condition_names")),
        "missing_images": missing_images,
        "capture_regressions": regressions,
        "capture_progressed": bool(capture_gap.get("progressed", False)),
        "next_capture": capture_gap.get("next", []) if isinstance(capture_gap.get("next"), list) else [],
        "mission_gate": str(missions.get("gate", "BLOCKED")),
        "mission_done": mission_done,
        "mission_total": int(missions.get("total", 0) or 0),
        "mission_percent": missions.get("percent", 0),
        "capture_integrity": integrity,
        "integrity_binding_errors": binding_errors,
        "validation_errors": errors,
        "evidence_gate": "BLOCKED" if blockers else "PASS_INCREMENTAL",
        "blockers": blockers,
    }


def _delta(previous: dict, current: dict) -> dict:
    prev_tiles = set(previous.get("tile_ids", []))
    curr_tiles = set(current.get("tile_ids", []))
    prev_palettes = set(previous.get("palettes", []))
    curr_palettes = set(current.get("palettes", []))
    prev_conditions = set(previous.get("condition_names", []))
    curr_conditions = set(current.get("condition_names", []))
    all_groups = sorted(set(previous.get("groups", {})) | set(current.get("groups", {})))
    return {
        "from_fingerprint": previous.get("fingerprint", ""),
        "to_fingerprint": current.get("fingerprint", ""),
        "mapping_delta": int(current.get("mapping_count", 0)) - int(previous.get("mapping_count", 0)),
        "mission_done_delta": int(current.get("mission_done", 0)) - int(previous.get("mission_done", 0)),
        "mission_verified_delta": int(current.get("capture_integrity", {}).get("mission_verified_done", 0)) - int(previous.get("capture_integrity", {}).get("mission_verified_done", 0)),
        "added_tile_ids": sorted(curr_tiles - prev_tiles),
        "removed_tile_ids": sorted(prev_tiles - curr_tiles),
        "added_palettes": sorted(curr_palettes - prev_palettes),
        "removed_palettes": sorted(prev_palettes - curr_palettes),
        "added_conditions": sorted(curr_conditions - prev_conditions),
        "removed_conditions": sorted(prev_conditions - curr_conditions),
        "group_deltas": {
            group: int(current.get("groups", {}).get(group, 0)) - int(previous.get("groups", {}).get(group, 0))
            for group in all_groups
        },
    }


def _gate_a_candidates(current: dict) -> list[dict]:
    conditions = [str(value) for value in current.get("condition_names", [])]
    lower = [(value, value.lower()) for value in conditions]
    result: list[dict] = []
    for key, tokens in GATE_A_HINTS.items():
        matches = [original for original, lowered in lower if any(token in lowered for token in tokens)]
        result.append({
            "gate_a_item": key,
            "status": "CANDIDATE_REVIEW" if matches else "NO_SIGNAL",
            "signals": matches[:12],
            "important_note": "Condition-name signals are review hints only and never auto-complete a ROADMAP checkbox.",
        })
    return result


def _next_action(current: dict) -> dict:
    if current.get("validation_errors"):
        return {"kind": "FIX_EVIDENCE", "action": "Fix evidence schema/privacy validation errors before accepting this snapshot."}
    if current.get("integrity_binding_errors"):
        return {"kind": "FIX_EVIDENCE_BINDING", "action": "Regenerate evidence through Guided Capture Marathon + Local Capture Bridge so completed missions are fingerprint-bound and capture integrity admission is proven."}
    if current.get("scale") != 4:
        return {"kind": "RECAPTURE_4X", "action": "Regenerate the MesenCE capture at the required 4x HD Pack scale."}
    if current.get("missing_images"):
        return {"kind": "REPAIR_CAPTURE", "action": "Repair missing images referenced by hires.txt and regenerate safe evidence."}
    if int(current.get("capture_regressions", 0)) > 0:
        return {"kind": "RECAPTURE_REGRESSION", "action": "Recapture lost coverage before this snapshot is treated as a production baseline."}
    queue = current.get("next_capture", [])
    if queue:
        row = queue[0] if isinstance(queue[0], dict) else {}
        target = row.get("target") or row.get("kind") or "next capture target"
        return {"kind": str(row.get("kind", "CAPTURE_NEXT")), "action": f"Capture next highest-priority target: {target}."}
    if current.get("mission_gate") != "PASS":
        return {"kind": "CAPTURE_MISSIONS", "action": "Continue explicit Capture Mission Control coverage; GitHub evidence is structurally clean but release capture is incomplete."}
    return {"kind": "REVIEW_GATE_A", "action": "Evidence is structurally clean and all completed missions are fingerprint-bound; manually review Gate A against real gameplay evidence. Do not auto-check ROADMAP items."}


def build_triage(root: Path) -> dict:
    files = _json_files(root)
    loaded: list[tuple[Path, dict, list[str]]] = []
    parse_errors: list[dict] = []
    for path in files:
        data, errors = _load(path)
        if data is None:
            parse_errors.append({"file": path.as_posix(), "errors": errors})
            continue
        if data.get("schema") != SCHEMA:
            parse_errors.append({"file": path.as_posix(), "errors": errors or [f"unsupported schema: {data.get('schema')!r}"]})
            continue
        loaded.append((path, data, errors))
    snapshots = [_snapshot(path, data, errors) for path, data, errors in loaded]
    snapshots.sort(key=lambda row: (row.get("generated_utc", ""), row.get("file", "")))
    deltas = [_delta(snapshots[index - 1], snapshots[index]) for index in range(1, len(snapshots))]
    current = snapshots[-1] if snapshots else None
    overall_gate = "NO_EVIDENCE"
    if current:
        overall_gate = current["evidence_gate"]
    if parse_errors:
        overall_gate = "BLOCKED"
    result = {
        "schema": "swir.project002.capture-evidence-triage.v2",
        "evidence_files": len(files),
        "valid_snapshots": len(snapshots),
        "parse_or_schema_errors": parse_errors,
        "snapshots": snapshots,
        "deltas": deltas,
        "latest": current,
        "gate_a_candidates": _gate_a_candidates(current) if current else [],
        "evidence_gate": overall_gate,
        "release_capture_gate": current.get("mission_gate", "BLOCKED") if current else "BLOCKED",
        "next_action": _next_action(current) if current else {"kind": "LOCAL_CAPTURE_BRIDGE", "action": "Generate and submit the first SAFE_CAPTURE_HANDOFF.json from the local MesenCE capture."},
        "roadmap_policy": "Triage never edits or auto-completes Gate A-D. A human/local gameplay evidence review is required before any ROADMAP checkbox changes.",
    }
    return result


def render_markdown(result: dict) -> str:
    latest = result.get("latest") or {}
    lines = [
        "# Project #002 — Capture Evidence Triage",
        "",
        f"**Evidence gate:** `{result.get('evidence_gate')}`  ",
        f"**Release capture gate:** `{result.get('release_capture_gate')}`  ",
        f"**Snapshots:** {result.get('valid_snapshots', 0)} valid / {result.get('evidence_files', 0)} JSON files",
        "",
    ]
    if latest:
        integrity = latest.get("capture_integrity", {})
        lines.extend([
            "## Latest safe snapshot",
            "",
            f"- fingerprint: `{latest.get('fingerprint', '')}`",
            f"- integrity admission: **{integrity.get('admission_gate', 'BLOCKED')}**",
            f"- verified mission evidence: **{integrity.get('mission_verified_done', 0)}/{latest.get('mission_done', 0)}**",
            f"- mappings: **{latest.get('mapping_count', 0)}**",
            f"- unique tile IDs: **{latest.get('unique_tile_ids', 0)}**",
            f"- palettes: **{latest.get('unique_palettes', 0)}**",
            f"- conditions: **{latest.get('condition_count', 0)}**",
            f"- capture missions: **{latest.get('mission_done', 0)}/{latest.get('mission_total', 0)}**",
            f"- explicit capture regressions: **{latest.get('capture_regressions', 0)}**",
            "",
            "## Captured mapping groups",
            "",
            "| Group | Mappings |",
            "|---|---:|",
        ])
        for group, count in sorted(latest.get("groups", {}).items()):
            lines.append(f"| {group} | {count} |")
        lines.extend(["", "## Gate A review hints", "", "These are **signals only**. They never auto-check ROADMAP items.", "", "| Gate A area | Status | Signals |", "|---|---|---|"])
        for row in result.get("gate_a_candidates", []):
            signals = ", ".join(row.get("signals", [])[:5]) or "—"
            lines.append(f"| {row.get('gate_a_item')} | {row.get('status')} | {signals} |")
        if latest.get("blockers"):
            lines.extend(["", "## Snapshot blockers", ""])
            for blocker in latest["blockers"]:
                lines.append(f"- {blocker}")
    lines.extend([
        "",
        "## DO THIS NEXT",
        "",
        f"**{result.get('next_action', {}).get('kind', '')}:** {result.get('next_action', {}).get('action', '')}",
        "",
        f"> {result.get('roadmap_policy', '')}",
        "",
    ])
    if result.get("parse_or_schema_errors"):
        lines.extend(["## Evidence errors", ""])
        for row in result["parse_or_schema_errors"]:
            lines.append(f"- `{row.get('file')}`: {'; '.join(row.get('errors', []))}")
        lines.append("")
    return "\n".join(lines)


def write_outputs(result: dict, output_dir: Path) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "CAPTURE_EVIDENCE_TRIAGE.json"
    markdown_path = output / "CAPTURE_EVIDENCE_TRIAGE.md"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(result), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(markdown_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Triage privacy-safe Project #002 capture evidence on GitHub/CI")
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--github-summary", type=Path)
    args = parser.parse_args()
    result = build_triage(args.evidence)
    if args.output:
        write_outputs(result, args.output)
    markdown = render_markdown(result)
    print(markdown)
    if args.github_summary:
        args.github_summary.parent.mkdir(parents=True, exist_ok=True)
        with args.github_summary.open("a", encoding="utf-8") as handle:
            handle.write(markdown + "\n")
    return 2 if result["evidence_gate"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())