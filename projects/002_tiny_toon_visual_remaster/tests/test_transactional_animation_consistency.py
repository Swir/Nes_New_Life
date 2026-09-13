from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


class TransactionalAnimationConsistencyContractTests(unittest.TestCase):
    def test_animation_gate_runs_before_candidate_composition(self) -> None:
        text = (TOOLS / "transactional_art_commit.py").read_text(encoding="utf-8")
        animation_call = text.index("audit_animation_consistency(staged_workspace")
        apply_call = text.index("apply_workspace(pack_dir, staged_workspace")
        self.assertLess(animation_call, apply_call)

    def test_animation_failure_is_fail_closed(self) -> None:
        text = (TOOLS / "transactional_art_commit.py").read_text(encoding="utf-8")
        self.assertIn('"transaction_status": "BLOCKED_ANIMATION_CONSISTENCY"', text)
        self.assertIn('"workspace_committed": False', text)
        self.assertIn('"output_committed": False', text)
        self.assertIn("ART_ANIMATION_CONSISTENCY_GATE.json", text)

    def test_transaction_schema_carries_family_gate(self) -> None:
        text = (TOOLS / "transactional_art_commit.py").read_text(encoding="utf-8")
        self.assertIn("swir.project002.transactional-art-commit.v3", text)
        self.assertIn('"animation_consistency_gate": animation_consistency', text)


if __name__ == "__main__":
    unittest.main()
