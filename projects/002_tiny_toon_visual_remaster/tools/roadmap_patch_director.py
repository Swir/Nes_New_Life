from __future__ import annotations

import argparse
import difflib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REVIEW_SCHEMA = "swir.project002.gate-a-review-attestation.v1"
PATCH_SCHEMA = "swir.project002.roadmap-patch-director.v1"
CONFIRMATION = "VERIFIED_GATE_A"
STYLE_MARKER = "<!-- SWIR-ROADMAP-STANDARD:v1 -->"
TOTAL_ITEMS = 52
GATE_A_ITEMS = 12
BAR_SEGMENTS = 20


class PatchError(RuntimeError):
    pass


def _load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PatchError(f"{path.name}: expected a JSON object")
    return data


def _gate_a_bounds(text: str) -> tuple[int, int]:
    start = text.find("## Gate A")
    end = text.find("## Gate B")
    if start < 0 or end < 0 or end <= start:
        raise PatchError("Project ROADMAP must contain ordered Gate A and Gate B sections.")
    return start, end


def _checkbox_matches(text: str) -> list[re.Match[str]]:
    return list(re.finditer(r"(?m)^(\s*-\s+\[)([ xX])(\]\s+.+)$", text))


def _validate_project_roadmap(text: str) -> dict:
    if STYLE_MARKER not in text:
        raise PatchError("Project ROADMAP is missing SWIR-ROADMAP-STANDARD:v1.")
    matches = _checkbox_matches(text)
    if len(matches) != TOTAL_ITEMS:
        raise PatchError(f"Project ROADMAP must contain exactly {TOTAL_ITEMS} authoritative checkboxes; found {len(matches)}.")
    start, end = _gate_a_bounds(text)
    gate_a = [m for m in matches if start <= m.start() < end]
    if len(gate_a) != GATE_A_ITEMS:
        raise PatchError(f"Gate A must contain exactly {GATE_A_ITEMS} checkboxes; found {len(gate_a)}.")
    checked = {i + 1 for i, m in enumerate(gate_a) if m.group(2).lower() == "x"}
    return {"matches": matches, "gate_a": gate_a, "checked_gate_a": checked}


def _validate_master_roadmap(text: str) -> None:
    if STYLE_MARKER not in text:
        raise PatchError("Master ROADMAP is missing SWIR-ROADMAP-STANDARD:v1.")
    if "#002 Tiny Toon Visual Remaster" not in text:
        raise PatchError("Master ROADMAP does not contain the Project #002 row.")
    if "## 🎮 Current game progress" not in text:
        raise PatchError("Master ROADMAP is missing the current-game progress dashboard.")


def _validated_attested_indexes(review: dict, ledger: dict) -> set[int]:
    if review.get("schema") != REVIEW_SCHEMA:
        raise PatchError(f"Unsupported review schema: {review.get('schema')!r}")
    if ledger.get("schema") != REVIEW_SCHEMA:
        raise PatchError(f"Unsupported attestation ledger schema: {ledger.get('schema')!r}")

    fingerprint = str(review.get("capture_fingerprint_sha256", ""))
    if not fingerprint:
        raise PatchError("Review handoff is missing capture fingerprint.")
    if str(ledger.get("capture_fingerprint_sha256", "")) != fingerprint:
        raise PatchError("Review handoff and attestation ledger fingerprints differ.")

    criteria = review.get("criteria")
    attestations = ledger.get("attestations")
    if not isinstance(criteria, list) or len(criteria) != GATE_A_ITEMS:
        raise PatchError(f"Review handoff must contain exactly {GATE_A_ITEMS} Gate A criteria.")
    if not isinstance(attestations, list):
        raise PatchError("Attestation ledger has invalid attestations payload.")

    by_index = {}
    for row in criteria:
        if not isinstance(row, dict):
            raise PatchError("Review criteria must be objects.")
        index = int(row.get("index", 0) or 0)
        if index < 1 or index > GATE_A_ITEMS or index in by_index:
            raise PatchError("Review criteria contain duplicate or invalid Gate A indexes.")
        by_index[index] = row

    verified: set[int] = set()
    for att in attestations:
        if not isinstance(att, dict):
            raise PatchError("Attestation rows must be objects.")
        index = int(att.get("index", 0) or 0)
        if index < 1 or index > GATE_A_ITEMS or index in verified:
            raise PatchError("Attestation ledger contains duplicate or invalid Gate A indexes.")
        row = by_index.get(index)
        if row is None:
            raise PatchError(f"Attestation index {index} is not present in the review handoff.")
        if att.get("confirmation") != CONFIRMATION:
            raise PatchError(f"Gate A index {index} does not carry exact {CONFIRMATION} confirmation.")
        if str(att.get("capture_fingerprint_sha256", "")) != fingerprint:
            raise PatchError(f"Gate A index {index} attestation fingerprint is stale.")
        source_fp = str(att.get("source_fingerprint_sha256", ""))
        if not source_fp or source_fp != str(row.get("source_fingerprint_sha256", "")):
            raise PatchError(f"Gate A index {index} source fingerprint does not match reviewed evidence.")
        if row.get("review_status") != CONFIRMATION:
            raise PatchError(f"Gate A index {index} is not marked {CONFIRMATION} by the review handoff.")
        if row.get("evidence_status") != "EVIDENCE_READY_FOR_REVIEW":
            raise PatchError(f"Gate A index {index} was attested without evidence-ready status.")
        verified.add(index)

    preview = review.get("roadmap_patch_preview") or {}
    preview_indexes = {int(v) for v in preview.get("verified_gate_a_indexes", [])}
    if preview_indexes != verified:
        raise PatchError("Review preview and attestation ledger disagree on verified Gate A indexes.")
    return verified


def _set_gate_a_checks(text: str, target_indexes: set[int]) -> str:
    state = _validate_project_roadmap(text)
    gate_a = state["gate_a"]
    out = []
    last = 0
    for ordinal, match in enumerate(gate_a, start=1):
        out.append(text[last:match.start()])
        mark = "x" if ordinal in target_indexes else " "
        out.append(match.group(1) + mark + match.group(3))
        last = match.end()
    out.append(text[last:])
    return "".join(out)


def _bar(percent: float) -> str:
    filled = min(BAR_SEGMENTS, max(0, int((percent * BAR_SEGMENTS / 100.0) + 0.5)))
    return "█" * filled + "░" * (BAR_SEGMENTS - filled)


def _update_project_dashboard(text: str) -> tuple[str, dict]:
    matches = _checkbox_matches(text)
    completed = sum(m.group(2).lower() == "x" for m in matches)
    total = len(matches)
    if total != TOTAL_ITEMS:
        raise PatchError(f"Project ROADMAP total changed unexpectedly: {total} != {TOTAL_ITEMS}.")
    remaining = total - completed
    percent = round(completed * 100.0 / total, 1)
    bar = _bar(percent)

    text, n1 = re.subn(r"ROADMAP-[0-9]+(?:\.[0-9]+)?%25-", f"ROADMAP-{percent:.1f}%25-", text, count=1)
    text, n2 = re.subn(r"DONE-\d+%2F52-", f"DONE-{completed}%2F52-", text, count=1)
    text, n3 = re.subn(
        r"(?m)^[█░]{20}\s+[0-9]+(?:\.[0-9]+)?%$",
        f"{bar} {percent:.1f}%",
        text,
        count=1,
    )
    text, n4 = re.subn(
        r"\| \*\*\d+\*\* \| \*\*\d+\*\* \| \*\*52\*\* \| \*\*[0-9]+(?:\.[0-9]+)?%\*\* \|",
        f"| **{completed}** | **{remaining}** | **52** | **{percent:.1f}%** |",
        text,
        count=1,
    )
    if (n1, n2, n3, n4) != (1, 1, 1, 1):
        raise PatchError(f"Project dashboard structure drifted; replacements={(n1, n2, n3, n4)}")
    return text, {"completed": completed, "remaining": remaining, "total": total, "percent": percent, "bar": bar}


def _update_master_dashboard(text: str, stats: dict) -> str:
    _validate_master_roadmap(text)
    completed = int(stats["completed"])
    remaining = int(stats["remaining"])
    percent = float(stats["percent"])
    bar = str(stats["bar"])

    text, n1 = re.subn(
        r"(?m)^[█░]{20}\s+[0-9]+(?:\.[0-9]+)?%$",
        f"{bar} {percent:.1f}%",
        text,
        count=1,
    )
    text, n2 = re.subn(
        r"\| \*\*#002 Tiny Toon Visual Remaster\*\* \| \*\*\d+\*\* \| \*\*\d+\*\* \| \*\*[0-9]+(?:\.[0-9]+)?%\*\* \|",
        f"| **#002 Tiny Toon Visual Remaster** | **{completed}** | **{remaining}** | **{percent:.1f}%** |",
        text,
        count=1,
    )
    text, n3 = re.subn(
        r"\| #002 \| Tiny Toon Visual Remaster \| \*\*ACTIVE\*\* \| \*\*[0-9]+(?:\.[0-9]+)?%\*\* \|",
        f"| #002 | Tiny Toon Visual Remaster | **ACTIVE** | **{percent:.1f}%** |",
        text,
        count=1,
    )
    if (n1, n2, n3) != (1, 1, 1):
        raise PatchError(f"Master dashboard structure drifted; replacements={(n1, n2, n3)}")
    return text


def build_patch(review: dict, ledger: dict, project_text: str, master_text: str) -> dict:
    state = _validate_project_roadmap(project_text)
    _validate_master_roadmap(master_text)
    verified = _validated_attested_indexes(review, ledger)
    already_checked = set(state["checked_gate_a"])

    if not already_checked.issubset(verified):
        missing = sorted(already_checked - verified)
        raise PatchError(
            "Current ROADMAP already contains Gate A completions not backed by the exact current fingerprint "
            f"attestation ledger: {missing}. Refusing to rewrite or silently preserve stale proof."
        )

    target = set(verified)
    patched_project = _set_gate_a_checks(project_text, target)
    patched_project, stats = _update_project_dashboard(patched_project)
    patched_master = _update_master_dashboard(master_text, stats)

    before_state = _validate_project_roadmap(project_text)
    after_state = _validate_project_roadmap(patched_project)
    before_non_a = [m.group(0) for m in before_state["matches"][GATE_A_ITEMS:]]
    after_non_a = [m.group(0) for m in after_state["matches"][GATE_A_ITEMS:]]
    if before_non_a != after_non_a:
        raise PatchError("Gate B-D checkbox mutation detected; refusing patch.")

    return {
        "schema": PATCH_SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "capture_fingerprint_sha256": str(review["capture_fingerprint_sha256"]),
        "verified_gate_a_indexes": sorted(target),
        "previous_gate_a_indexes": sorted(already_checked),
        "new_gate_a_indexes": sorted(target - already_checked),
        "stats": stats,
        "project_text": patched_project,
        "master_text": patched_master,
        "status": "READY_FOR_REPOSITORY_REVIEW" if target != already_checked else "NO_ROADMAP_CHANGE",
        "policy": (
            "Generated only from exact-fingerprint VERIFIED_GATE_A attestations. "
            "Gate B-D remain untouched. Output is a reviewable patch preview and does not mutate repository files."
        ),
    }


def _diff(before: str, after: str, path: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )


def write_outputs(result: dict, project_before: str, master_before: str, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    project_path = output_dir / "PATCHED_PROJECT_ROADMAP.md"
    master_path = output_dir / "PATCHED_MASTER_ROADMAP.md"
    diff_path = output_dir / "ROADMAP_PATCH_PREVIEW.diff"
    manifest_path = output_dir / "ROADMAP_PATCH_DIRECTOR.json"

    project_path.write_text(result["project_text"], encoding="utf-8")
    master_path.write_text(result["master_text"], encoding="utf-8")
    diff_text = _diff(
        project_before,
        result["project_text"],
        "projects/002_tiny_toon_visual_remaster/ROADMAP.md",
    ) + _diff(master_before, result["master_text"], "docs/ROADMAP.md")
    diff_path.write_text(diff_text, encoding="utf-8")

    manifest = {k: v for k, v in result.items() if k not in {"project_text", "master_text"}}
    manifest["outputs"] = {
        "patched_project_roadmap": project_path.name,
        "patched_master_roadmap": master_path.name,
        "diff": diff_path.name,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "manifest": str(manifest_path),
        "project": str(project_path),
        "master": str(master_path),
        "diff": str(diff_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 fail-closed Gate A ROADMAP patch director")
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--project-roadmap", type=Path, required=True)
    parser.add_argument("--master-roadmap", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    review = _load_json(args.review)
    ledger = _load_json(args.ledger)
    project_text = args.project_roadmap.read_text(encoding="utf-8")
    master_text = args.master_roadmap.read_text(encoding="utf-8")
    result = build_patch(review, ledger, project_text, master_text)
    outputs = write_outputs(result, project_text, master_text, args.output)
    print(json.dumps({
        "status": result["status"],
        "capture_fingerprint_sha256": result["capture_fingerprint_sha256"],
        "new_gate_a_indexes": result["new_gate_a_indexes"],
        "stats": result["stats"],
        "outputs": outputs,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
