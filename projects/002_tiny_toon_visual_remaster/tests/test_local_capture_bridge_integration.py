from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


class LocalCaptureBridgeIntegrationTests(unittest.TestCase):
    def test_authoritative_studio_exposes_f4_bridge(self) -> None:
        text = (ROOT / "tools" / "AuthoritativeRemasterStudio.py").read_text(encoding="utf-8")
        self.assertIn('F4  Local Capture Bridge', text)
        self.assertIn('"<F4>"', text)
        self.assertIn('Local_Capture_Bridge.bat', text)

    def test_windows_bridge_and_privacy_guard_exist(self) -> None:
        self.assertTrue((ROOT / "windows" / "Local_Capture_Bridge.bat").is_file())
        ps1 = (ROOT / "windows" / "Local_Capture_Bridge.ps1").read_text(encoding="utf-8")
        self.assertIn("SAFE_CAPTURE_HANDOFF.json", ps1)
        self.assertIn("capture_evidence_validator.py", ps1)
        self.assertIn("gh pr create", ps1)
        workflow = REPO / ".github" / "workflows" / "project-002-capture-evidence.yml"
        self.assertTrue(workflow.is_file())
        workflow_text = workflow.read_text(encoding="utf-8")
        self.assertIn("capture_evidence_validator.py", workflow_text)
        self.assertIn("evidence/capture", workflow_text)


if __name__ == "__main__":
    unittest.main()
