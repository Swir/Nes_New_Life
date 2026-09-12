from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from fullscreen_launch import fullscreen_evidence_status
from hd_readiness import package_hd_pack
from release_candidate import audit_release_candidate


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stage(name: str, gate: str, summary: str, action: str) -> dict:
    return {
        "name": name,
        "gate": gate,
        "summary": summary,
        "action": action,
    }


def final_release_audit(
    pack_dir: Path,
    capture_manifest: Path,
    art_queue: Path,
    art_qa: Path,
    regression_manifest: Path,
    visual_review: Path,
    fullscreen_evidence: Path,
) -> dict:
    """Build the authoritative user-facing release decision for Project #002.

    The existing release candidate audit remains authoritative for structure,
    capture, art, visual context, Pixel QA and regression. This director adds
    the exact-build fullscreen evidence that the Windows one-click playtest
    already records, so packaging cannot accidentally bypass the fullscreen
    requirement.
    """
    base = audit_release_candidate(
        Path(pack_dir),
        Path(capture_manifest),
        Path(art_queue),
        Path(art_qa),
        Path(regression_manifest),
        Path(visual_review),
    )
    fullscreen = fullscreen_evidence_status(Path(pack_dir), Path(fullscreen_evidence))

    capture = base["capture"]
    queue = base["art_queue"]
    context = base["visual_context"]
    qa = base["art_qa"]
    regression = base["regression"]
    validator_errors = base["validator"]["errors"]
    missing_images = base["pack"]["missing_images"]

    structure_pass = not validator_errors and not missing_images and base["pack"]["scale"] >= 4
    art_pass = bool(queue["exists"] and queue["rows"] and queue["todo"] == 0 and queue["unassigned"] == 0)

    stages = [
        _stage(
            "HD PACK STRUCTURE",
            "PASS" if structure_pass else "BLOCKED",
            (
                f"scale={base['pack']['scale']} · missing_images={len(missing_images)} · "
                f"validator_errors={len(validator_errors)}"
            ),
            "Fix hires.txt/runtime PNG structure, missing references and 4x scale before continuing.",
        ),
        _stage(
            "CAPTURE COVERAGE",
            capture["release_capture_gate"],
            f"{capture['done']}/{capture['total']} capture missions complete",
            "Complete the next unfinished Capture Mission Control mission in local MesenCE.",
        ),
        _stage(
            "FINAL ART",
            "PASS" if art_pass else "BLOCKED",
            (
                f"done={queue['done']}/{queue['rows']} · todo={queue['todo']} · "
                f"unassigned={queue['unassigned']}"
            ),
            "Finish/classify the highest-priority remaining Final Art Sprint items.",
        ),
        _stage(
            "VISUAL CONTEXT",
            context["gate"],
            (
                f"reviewed={context['reviewed']}/{context['review_required']} · "
                f"pending={context['pending']} · stale={context['stale']}"
            ),
            "Resolve pending/stale high-risk palette, condition and variant families.",
        ),
        _stage(
            "PIXEL QA",
            qa["gate"],
            (
                "exact-build PASS"
                if qa["gate"] == "PASS"
                else "missing, failed or stale against the current runtime fingerprint"
            ),
            "Run Finish Sprint + Pixel QA (or Apply full workspace + QA) on this exact build.",
        ),
        _stage(
            "VERIFIED FULLSCREEN",
            fullscreen["gate"],
            (
                f"verified={fullscreen['fullscreen_verified']} · "
                f"fingerprint_matches={fullscreen['fingerprint_matches']} · "
                f"method={fullscreen.get('method') or 'none'}"
            ),
            "Run the one-click HD playtest and keep MesenCE in verified fullscreen on this exact build.",
        ),
        _stage(
            "FINAL REGRESSION",
            regression["gate"],
            (
                f"PASS={regression['counts']['PASS']}/{regression['total']} · "
                f"FAIL={regression['counts']['FAIL']} · STALE={regression['counts']['STALE']} · "
                f"PENDING={regression['counts']['PENDING']}"
            ),
            "Drive Final Regression Cockpit to 10/10 current-build PASS in real MesenCE gameplay.",
        ),
    ]

    blockers = list(base["blockers"])
    if fullscreen["gate"] != "PASS":
        if not fullscreen["exists"]:
            blockers.append("Verified fullscreen playtest evidence is missing")
        elif not fullscreen["fullscreen_verified"]:
            blockers.append("Latest fullscreen playtest was not verified")
        else:
            blockers.append("Fullscreen playtest evidence is stale for the current HD-pack fingerprint")

    next_stage = next((item for item in stages if item["gate"] != "PASS"), None)
    ready = not blockers

    return {
        "schema": 1,
        "generated_utc": _now(),
        "release_gate": "PASS" if ready else "BLOCKED",
        "release_ready": ready,
        "pack_fingerprint": base["pack_fingerprint"],
        "base_release_gate": base["release_gate"],
        "important_note": (
            "Public packaging is authorized only when structure, capture coverage, final art, Visual Context, "
            "Pixel QA, verified fullscreen and all ten Final Regression Cockpit cases PASS for the exact same "
            "HD-pack fingerprint. No ROM, save state or emulator binary belongs in the release ZIP."
        ),
        "stages": stages,
        "next_stage": next_stage,
        "fullscreen": fullscreen,
        "release_candidate": base,
        "blockers": blockers,
    }


def write_final_dashboard(result: dict, output_dir: Path) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "FINAL_RELEASE_READINESS.json"
    html_path = output / "FINAL_RELEASE_READINESS.html"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    stage_rows = "".join(
        "<tr>"
        f"<td class='{stage['gate'].lower()}'>{html.escape(stage['gate'])}</td>"
        f"<td><b>{html.escape(stage['name'])}</b></td>"
        f"<td>{html.escape(stage['summary'])}</td>"
        f"<td>{html.escape(stage['action'])}</td>"
        "</tr>"
        for stage in result["stages"]
    )
    blockers = "".join(f"<li>{html.escape(item)}</li>" for item in result["blockers"]) or "<li>None</li>"
    gate_class = "pass" if result["release_gate"] == "PASS" else "blocked"
    next_stage = result.get("next_stage")
    next_text = "Everything is green. Build the gated ZIP."
    if next_stage:
        next_text = f"{next_stage['name']}: {next_stage['action']}"

    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Project #002 Final Release Readiness</title>
<style>body{{font:16px system-ui;max-width:1250px;margin:34px auto;padding:0 22px;background:#0d1117;color:#e6edf3}}.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:18px;margin:14px 0}}.pass{{color:#3fb950}}.blocked,.fail{{color:#f85149}}table{{width:100%;border-collapse:collapse}}td,th{{padding:10px;border-bottom:1px solid #30363d;text-align:left;vertical-align:top}}code{{color:#79c0ff}}small{{color:#8b949e}}</style></head><body>
<h1>Tiny Toon Visual Remaster — Final Release Readiness Director</h1>
<div class='card'><h2 class='{gate_class}'>FINAL RELEASE GATE: {result['release_gate']}</h2><p>{html.escape(result['important_note'])}</p><p><small>Exact build fingerprint: <code>{result['pack_fingerprint']}</code></small></p><h3>DO THIS NEXT</h3><p>{html.escape(next_text)}</p></div>
<div class='card'><h2>Production gates</h2><table><tr><th>Gate</th><th>Stage</th><th>Evidence</th><th>Required action</th></tr>{stage_rows}</table></div>
<div class='card'><h2>Blocking reasons</h2><ul>{blockers}</ul></div>
</body></html>"""
    html_path.write_text(document, encoding="utf-8")
    return html_path


def audit_and_write(
    pack: Path,
    capture: Path,
    queue: Path,
    art_qa: Path,
    regression: Path,
    visual_review: Path,
    fullscreen: Path,
    output: Path,
) -> dict:
    result = final_release_audit(pack, capture, queue, art_qa, regression, visual_review, fullscreen)
    write_final_dashboard(result, output)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 exact-build final release readiness director")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("audit", "package"):
        cmd = commands.add_parser(name)
        cmd.add_argument("pack", type=Path)
        cmd.add_argument("--capture", type=Path, required=True)
        cmd.add_argument("--queue", type=Path, required=True)
        cmd.add_argument("--visual-review", type=Path, required=True)
        cmd.add_argument("--art-qa", type=Path, required=True)
        cmd.add_argument("--regression", type=Path, required=True)
        cmd.add_argument("--fullscreen", type=Path, required=True)
        cmd.add_argument("--output", type=Path, required=True)
        if name == "package":
            cmd.add_argument("--zip", type=Path, required=True)
    args = parser.parse_args()

    result = audit_and_write(
        args.pack,
        args.capture,
        args.queue,
        args.art_qa,
        args.regression,
        args.visual_review,
        args.fullscreen,
        args.output,
    )
    print(json.dumps(result, indent=2))
    if result["release_gate"] != "PASS":
        return 2
    if args.command == "package":
        print(package_hd_pack(args.pack, args.zip))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
