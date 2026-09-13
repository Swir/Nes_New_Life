from __future__ import annotations

import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from AuthoritativeRemasterStudio import AuthoritativeRemasterStudio, PROJECT_ROOT
from active_family_workbench import WorkbenchError, resolve_active_family_workbench, write_active_state
from production_cockpit import build_cockpit, write_outputs
from roadmap_evidence_readiness import assess as assess_roadmap_evidence
from roadmap_evidence_readiness import write_outputs as write_evidence_outputs


class AuthoritativeProductionStudio(AuthoritativeRemasterStudio):
    """Authoritative Remaster Studio with one-click production autopilot controls."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Tiny Toon Visual Remaster — Authoritative HD Production Cockpit")
        self.after(150, self.refresh_production_cockpit)

    def _build(self) -> None:
        super()._build()
        panel = ttk.LabelFrame(self, text="AUTHORITATIVE PRODUCTION AUTOPILOT", padding=10)
        panel.pack(fill="x", padx=14, pady=(0, 12))
        ttk.Button(
            panel,
            text="CTRL+F6  FULL CAPTURE → HD AUTOPILOT",
            command=lambda: self.run_windows("Full_Capture_To_HD_Autopilot.bat"),
        ).pack(side="left", padx=4)
        ttk.Button(
            panel,
            text="CTRL+F7  CONTINUE QA-GATED ART SESSION",
            command=lambda: self.run_windows("Continue_HD_Art_Session.bat"),
        ).pack(side="left", padx=4)
        ttk.Button(
            panel,
            text="CTRL+F8  REFRESH PRODUCTION COCKPIT",
            command=self.refresh_production_cockpit,
        ).pack(side="left", padx=4)
        ttk.Button(
            panel,
            text="CTRL+F9  ROADMAP EVIDENCE READINESS",
            command=self.refresh_roadmap_evidence,
        ).pack(side="left", padx=4)
        ttk.Button(
            panel,
            text="CTRL+F10  OPEN ACTIVE FAMILY WORKBENCH",
            command=self.open_active_family_workbench,
        ).pack(side="left", padx=4)
        ttk.Button(
            panel,
            text="CTRL+F11  COMMIT + QA + FULLSCREEN PLAYTEST",
            command=lambda: self.run_windows("Finish_Family_And_Playtest.bat"),
        ).pack(side="left", padx=4)
        ttk.Button(
            panel,
            text="CTRL+F12  NEXT-BEST CAPTURE LOOP",
            command=lambda: self.run_windows("Capture_Next_Best_Loop.bat"),
        ).pack(side="left", padx=4)
        ttk.Button(panel, text="Open cockpit report", command=self.open_cockpit_report).pack(side="left", padx=4)

    def _bind_shortcuts(self) -> None:
        super()._bind_shortcuts()
        self.bind("<Control-F6>", lambda event: self.run_windows("Full_Capture_To_HD_Autopilot.bat"))
        self.bind("<Control-F7>", lambda event: self.run_windows("Continue_HD_Art_Session.bat"))
        self.bind("<Control-F8>", lambda event: self.refresh_production_cockpit())
        self.bind("<Control-F9>", lambda event: self.refresh_roadmap_evidence())
        self.bind("<Control-F10>", lambda event: self.open_active_family_workbench())
        self.bind("<Control-F11>", lambda event: self.run_windows("Finish_Family_And_Playtest.bat"))
        self.bind("<Control-F12>", lambda event: self.run_windows("Capture_Next_Best_Loop.bat"))

    def refresh_production_cockpit(self) -> None:
        root = self.workspace if self.workspace else PROJECT_ROOT
        try:
            result = build_cockpit(root)
            outputs = write_outputs(result, root / "Reports" / "ProductionCockpit")
        except Exception as exc:
            self.status.set(f"Production Cockpit refresh failed: {exc}")
            return
        self.status.set(f"Production Cockpit: {result['stage']}")
        capture = result.get("capture_to_hd") or {}
        autopilot = result.get("hd_art_autopilot") or {}
        art = result.get("art_session") or {}
        release = result.get("final_release") or {}
        self._write(
            "AUTHORITATIVE PRODUCTION COCKPIT\n\n"
            f"Stage: {result['stage']}\n"
            f"Recommended launcher: {result['launcher']}\n\n"
            f"Capture decision: {capture.get('capture_decision', '—')}\n"
            f"Production decision: {capture.get('production_decision', '—')}\n"
            f"HD Art Autopilot: {autopilot.get('status', '—')}\n"
            f"Art Session: {art.get('status', '—')}\n"
            f"Final Release Gate: {release.get('release_gate', '—')}\n\n"
            f"DO THIS NEXT\n{result['next_action']}\n\n"
            f"Dashboard: {outputs['dashboard']}\n\n"
            "This cockpit never changes ROADMAP Gate A–D. Tooling status is not completion evidence."
        )

    def refresh_roadmap_evidence(self) -> None:
        root = self.workspace if self.workspace else PROJECT_ROOT
        try:
            result = assess_roadmap_evidence(root)
            outputs = write_evidence_outputs(result, root / "Reports" / "RoadmapEvidenceReadiness")
        except Exception as exc:
            self.status.set(f"ROADMAP Evidence Readiness failed: {exc}")
            return
        counts = result.get("counts", {})
        ready = int(counts.get("READY_FOR_HUMAN_REVIEW", 0) or 0)
        blocked = int(counts.get("BLOCKED", 0) or 0)
        waiting = int(counts.get("WAITING_LOCAL_EVIDENCE", 0) or 0)
        self.status.set(f"ROADMAP evidence: review={ready} blocked={blocked} waiting={waiting}")
        self._write(
            "ROADMAP EVIDENCE READINESS — READ ONLY\n\n"
            f"Authoritative items: {result['roadmap_items']}\n"
            f"Ready for human review: {ready}\n"
            f"Blocked: {blocked}\n"
            f"Waiting for local evidence: {waiting}\n\n"
            f"DO THIS NEXT\n{result['next_action']}\n\n"
            f"Dashboard: {outputs['dashboard']}\n\n"
            "READY_FOR_HUMAN_REVIEW is not completion. Inspect real local gameplay/art/QA evidence before manually changing any ROADMAP checkbox."
        )

    def open_active_family_workbench(self) -> None:
        root = self.workspace if self.workspace else PROJECT_ROOT
        kit = root / "Artwork" / "CurrentImpactSprint"
        try:
            result = resolve_active_family_workbench(kit)
            state = write_active_state(result, kit)
        except WorkbenchError as exc:
            messagebox.showinfo(
                "No active family workbench",
                f"{exc}\n\nPrepare or continue the High-Impact Art Sprint first.",
            )
            return
        board = kit / result["board"]
        editable = kit / result["editable_dir"]
        self._open_path(board)
        self._open_path(editable)
        self.status.set(
            f"Active family: {result['family']} · priority #{result['priority']} · {result['members']} members"
        )
        self._write(
            "ACTIVE FAMILY ART WORKBENCH\n\n"
            f"Family: {result['family']}\n"
            f"Highest priority: #{result['priority']}\n"
            f"Family members: {result['members']}\n"
            f"Contact board: {board}\n"
            f"Editable folder: {editable}\n"
            f"State: {state}\n\n"
            f"DO THIS NEXT\n{result['next_action']}\n\n"
            "When the family redraw is ready, use CTRL+F11. The one-click handoff refuses to start the fullscreen playtest if transactional visual/family/Pixel QA does not commit successfully."
        )

    def open_cockpit_report(self) -> None:
        root = self.workspace if self.workspace else PROJECT_ROOT
        report = root / "Reports" / "ProductionCockpit" / "PRODUCTION_COCKPIT.html"
        if not report.is_file():
            self.refresh_production_cockpit()
        if report.is_file():
            webbrowser.open(report.as_uri())


def main() -> int:
    AuthoritativeProductionStudio().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
