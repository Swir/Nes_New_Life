from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = ROOT / "windows"
TOOLS = ROOT / "tools"


class GateAEvidenceWindowsIntegrationTests(unittest.TestCase):
    def test_next_best_loop_generates_matrix_after_single_session(self) -> None:
        source = (WINDOWS / "Capture_Next_Best_Loop.ps1").read_text(encoding="utf-8")
        self.assertIn("gate_a_evidence_matrix.py", source)
        self.assertIn("gate_a_review_attestation.py", source)
        self.assertIn("CAPTURE_COVERAGE_ACCEPTANCE.json", source)
        self.assertIn("GATE_A_EVIDENCE_MATRIX.html", source)
        self.assertIn("GATE_A_REVIEW_HANDOFF.html", source)
        session_pos = source.index("& $SingleSession")
        matrix_pos = source.index("Invoke-PythonTool $GateATool")
        review_pos = source.index("Invoke-PythonTool $ReviewTool")
        self.assertLess(session_pos, matrix_pos)
        self.assertLess(matrix_pos, review_pos)

    def test_gate_a_tool_is_metadata_only_and_never_edits_roadmap(self) -> None:
        source = (TOOLS / "gate_a_evidence_matrix.py").read_text(encoding="utf-8")
        self.assertNotIn("ROADMAP.md\").write", source)
        self.assertNotIn("update_file", source)
        self.assertNotIn("copyfile", source)
        self.assertNotIn("shutil", source)
        self.assertNotIn("PIL", source)

    def test_review_handoff_is_metadata_only_and_never_edits_roadmap(self) -> None:
        source = (TOOLS / "gate_a_review_attestation.py").read_text(encoding="utf-8")
        self.assertNotIn("ROADMAP.md\").write", source)
        self.assertNotIn("update_file", source)
        self.assertNotIn("copyfile", source)
        self.assertNotIn("shutil", source)
        self.assertNotIn("PIL", source)
        self.assertIn("VERIFIED_GATE_A", source)

    def test_wrapper_preserves_single_session_exit_code(self) -> None:
        source = (WINDOWS / "Capture_Next_Best_Loop.ps1").read_text(encoding="utf-8")
        self.assertIn("$SessionRc = $LASTEXITCODE", source)
        self.assertTrue(source.rstrip().endswith("exit $SessionRc"))


if __name__ == "__main__":
    unittest.main()
