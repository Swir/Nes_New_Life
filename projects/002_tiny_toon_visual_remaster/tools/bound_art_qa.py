from __future__ import annotations

import argparse
import json
from pathlib import Path

from art_qa import audit_art_apply
from release_candidate import pack_fingerprint


def audit_bound_art_apply(source_pack: Path, output_pack: Path, workspace: Path, report_dir: Path) -> dict:
    """Run existing pixel QA and bind PASS/BLOCKED evidence to the exact output pack.

    The original Art QA proves edits stayed inside authorized master regions. This
    wrapper additionally fingerprints hires.txt plus every referenced runtime PNG,
    so a later art or mapping change automatically makes that evidence stale.
    """
    result = audit_art_apply(source_pack, output_pack, workspace, report_dir)
    result["output_pack_fingerprint"] = pack_fingerprint(output_pack)
    report = report_dir / "ART_QA_RESULT.json"
    report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Project #002 build-bound pixel Art QA")
    parser.add_argument("source_pack", type=Path)
    parser.add_argument("output_pack", type=Path)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("report_dir", type=Path)
    args = parser.parse_args()
    result = audit_bound_art_apply(args.source_pack, args.output_pack, args.workspace, args.report_dir)
    print(json.dumps(result, indent=2))
    return 0 if result["qa_gate"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
