from __future__ import annotations

import json
import os
import subprocess
import sys
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from capture_coverage_acceptance import build_acceptance_manifest, write_outputs as write_capture_acceptance
from high_impact_art_sprint import prepare_high_impact_sprint
from visual_completion_matrix import build_and_write as build_visual_completion
from final_release_director import audit_and_write as final_release_audit_and_write


HERE = Path(__file__).resolve()
PROJECT_ROOT = HERE.parent.parent
WINDOWS_DIR = PROJECT_ROOT / "windows"


class AuthoritativeRemasterStudio(tk.Tk):
    """Project #002 production UI that exposes only the current authoritative HD path.

    It intentionally does not replace MesenCE or reimplement gameplay. The user's
    local ROM remains the source of gameplay/physics/timing and all ROM-derived
    capture/art stays outside the repository. Only validated metadata evidence may
    cross the Local Capture Bridge into GitHub.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("Tiny Toon Visual Remaster — Authoritative HD Studio")
        self.geometry("1180x850")
        self.minsize(980, 700)
        self.workspace: Path | None = None
        self.capture: Path | None = None
        self.pack: Path | None = None
        self.batch_size = tk.IntVar(value=30)
        self.status = tk.StringVar(value="Select your local workspace and current MesenCE capture.")
        self._build()
        self._bind_shortcuts()

    def _build(self) -> None:
        root = ttk.Frame(self, padding=14)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="PROJECT #002 — TINY TOON VISUAL REMASTER", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        ttk.Label(
            root,
            text="Authoritative path: guided fullscreen capture → safe evidence → coverage acceptance → safe promotion → highest-impact HD art → Pixel QA → 10/10 regression → gated ZIP",
        ).pack(anchor="w", pady=(2, 12))

        paths = ttk.LabelFrame(root, text="Local production inputs", padding=10)
        paths.pack(fill="x")
        ttk.Button(paths, text="F1  Select workspace", command=self.select_workspace).grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(paths, text="F2  Select current capture", command=self.select_capture).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(paths, text="F3  Select current HD pack", command=self.select_pack).grid(row=0, column=2, padx=4, pady=4, sticky="ew")
        self.workspace_label = ttk.Label(paths, text="Workspace: —")
        self.capture_label = ttk.Label(paths, text="Capture: —")
        self.pack_label = ttk.Label(paths, text="HD pack: —")
        self.workspace_label.grid(row=1, column=0, columnspan=3, sticky="w", padx=4)
        self.capture_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=4)
        self.pack_label.grid(row=3, column=0, columnspan=3, sticky="w", padx=4)
        for col in range(3):
            paths.columnconfigure(col, weight=1)

        capture = ttk.LabelFrame(root, text="1 — Capture / safe handoff / acceptance / promotion", padding=10)
        capture.pack(fill="x", pady=(10, 0))
        self._buttons(capture, [
            ("GUIDED CAPTURE MARATHON", lambda: self.run_windows("Guided_Capture_Marathon.bat")),
            ("F4  Local Capture Bridge", lambda: self.run_windows("Local_Capture_Bridge.bat")),
            ("CHECK CAPTURE ACCEPTANCE", self.capture_acceptance),
            ("F5  Promote capture safely", lambda: self.run_windows("Promote_Capture_To_HD.bat")),
        ])

        art = ttk.LabelFrame(root, text="2 — Highest-impact HD art", padding=10)
        art.pack(fill="x", pady=(10, 0))
        line = ttk.Frame(art)
        line.pack(fill="x")
        ttk.Label(line, text="Batch size:").pack(side="left")
        ttk.Spinbox(line, from_=1, to=200, textvariable=self.batch_size, width=6).pack(side="left", padx=(5, 12))
        ttk.Button(line, text="F6  Visual Completion Matrix", command=self.visual_matrix).pack(side="left", padx=3)
        ttk.Button(line, text="F7  Prepare exact High-Impact Sprint", command=self.prepare_impact_sprint).pack(side="left", padx=3)
        ttk.Button(line, text="F8  Finish sprint + Pixel QA", command=lambda: self.run_windows("Finish_High_Impact_Art_Sprint.bat")).pack(side="left", padx=3)

        qa = ttk.LabelFrame(root, text="3 — Exact-build playtest / release", padding=10)
        qa.pack(fill="x", pady=(10, 0))
        self._buttons(qa, [
            ("F9  Verified fullscreen playtest", lambda: self.run_windows("Build_HD_Playtest.bat")),
            ("F10  Final Regression Cockpit", lambda: self.run_windows("Final_Regression_Cockpit.bat")),
            ("F11  Final Release Gate", lambda: self.run_windows("Final_Release_Gate.bat")),
            ("Audit final readiness now", self.final_readiness),
        ])

        info = ttk.LabelFrame(root, text="Safety / controls", padding=10)
        info.pack(fill="x", pady=(10, 0))
        ttk.Label(info, text="Gameplay: original local ROM in MesenCE. Guided capture and final playtest use verified fullscreen.").pack(anchor="w")
        ttk.Label(info, text="Guided Capture Marathon records a mission only after explicit in-game verification; no tile-count heuristic can complete it.").pack(anchor="w")
        ttk.Label(info, text="Coverage Acceptance binds mission provenance, integrity and production-group signals to the exact capture fingerprint before promotion.").pack(anchor="w")
        ttk.Label(info, text="F4 may send only validator-approved metadata JSON to GitHub; capture pixels and local paths stay on this PC.").pack(anchor="w")
        ttk.Label(info, text="Recommended keyboard: arrows = D-pad · Z = A · X = B · Enter = Start · Right Shift = Select. Gamepad is configured in MesenCE.").pack(anchor="w")
        ttk.Label(info, text="Never commit ROMs, save states, emulator binaries, capture PNGs, ripped art/audio or local sprint boards.").pack(anchor="w")

        ttk.Label(root, textvariable=self.status, padding=(0, 8)).pack(fill="x")
        self.output = tk.Text(root, wrap="word", font=("Consolas", 10), height=17)
        self.output.pack(fill="both", expand=True)
        self._write(
            "AUTHORITATIVE REMASTER STUDIO READY\n\n"
            "Start with GUIDED CAPTURE MARATHON when Gate A gameplay coverage is still incomplete.\n"
            "F4 bridges local MesenCE evidence to GitHub as validated metadata only; CHECK CAPTURE ACCEPTANCE shows exact hard blockers before promotion.\n"
            "Tooling milestones do not count as release completion. ROADMAP progress remains evidence-based Gate A–D progress.\n"
        )

    def _buttons(self, parent: ttk.Widget, specs: list[tuple[str, object]]) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x")
        for text, command in specs:
            ttk.Button(row, text=text, command=command).pack(side="left", padx=3, pady=2)

    def _bind_shortcuts(self) -> None:
        binds = {
            "<Control-F4>": lambda: self.run_windows("Guided_Capture_Marathon.bat"),
            "<Control-F5>": self.capture_acceptance,
            "<F1>": self.select_workspace,
            "<F2>": self.select_capture,
            "<F3>": self.select_pack,
            "<F4>": lambda: self.run_windows("Local_Capture_Bridge.bat"),
            "<F5>": lambda: self.run_windows("Promote_Capture_To_HD.bat"),
            "<F6>": self.visual_matrix,
            "<F7>": self.prepare_impact_sprint,
            "<F8>": lambda: self.run_windows("Finish_High_Impact_Art_Sprint.bat"),
            "<F9>": lambda: self.run_windows("Build_HD_Playtest.bat"),
            "<F10>": lambda: self.run_windows("Final_Regression_Cockpit.bat"),
            "<F11>": lambda: self.run_windows("Final_Release_Gate.bat"),
        }
        for key, func in binds.items():
            self.bind(key, lambda event, f=func: f())

    def _write(self, text: str) -> None:
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)

    def select_workspace(self) -> None:
        value = filedialog.askdirectory(title="Select local Project #002 workspace")
        if value:
            self.workspace = Path(value)
            self.workspace_label.configure(text=f"Workspace: {self.workspace}")
            self.status.set("Workspace selected.")

    def select_capture(self) -> None:
        value = filedialog.askdirectory(title="Select current MesenCE HD Pack capture")
        if not value:
            return
        path = Path(value)
        if not (path / "hires.txt").is_file():
            messagebox.showerror("Invalid capture", "Selected folder does not contain hires.txt")
            return
        self.capture = path
        self.capture_label.configure(text=f"Capture: {self.capture}")
        if self.pack is None:
            self.pack = path
            self.pack_label.configure(text=f"HD pack: {self.pack}")
        self.status.set("Current capture selected.")

    def select_pack(self) -> None:
        value = filedialog.askdirectory(title="Select current candidate/final HD pack")
        if not value:
            return
        path = Path(value)
        if not (path / "hires.txt").is_file():
            messagebox.showerror("Invalid HD pack", "Selected folder does not contain hires.txt")
            return
        self.pack = path
        self.pack_label.configure(text=f"HD pack: {self.pack}")
        self.status.set("Current HD pack selected.")

    def capture_acceptance(self) -> None:
        if not self.workspace:
            messagebox.showinfo("Workspace required", "Select your local Project #002 workspace first.")
            return
        if not self.capture:
            self.select_capture()
        if not self.capture:
            return
        try:
            result = build_acceptance_manifest(self.workspace, self.capture)
            outputs = write_capture_acceptance(result, self.workspace / "Reports" / "CaptureCoverageAcceptance")
        except Exception as exc:
            messagebox.showerror("Capture Coverage Acceptance failed", str(exc))
            return
        dashboard = Path(outputs["dashboard"])
        webbrowser.open(dashboard.as_uri())
        summary = result.get("mission_summary", {})
        blockers = result.get("hard_blockers", [])
        self.status.set(f"Capture acceptance: {result['acceptance_gate']} · blockers {len(blockers)}")
        self._write(
            "CAPTURE COVERAGE ACCEPTANCE\n\n"
            f"Gate: {result['acceptance_gate']}\n"
            f"Fingerprint: {result['capture_fingerprint_sha256']}\n"
            f"Verified missions: {summary.get('verified', 0)}/{summary.get('total', 0)}\n"
            f"Hard blockers: {len(blockers)}\n\n"
            f"DO THIS NEXT\n{result.get('next_action', {}).get('action', 'Review the dashboard.')}\n\n"
            f"Dashboard: {dashboard}\n\n"
            "This check never changes ROADMAP Gate A–D. READY_FOR_GATE_A_REVIEW still requires real local gameplay review."
        )

    def _require_workspace_pack(self) -> tuple[Path, Path] | None:
        if not self.workspace:
            messagebox.showinfo("Workspace required", "Select your local Project #002 workspace first.")
            return None
        if not self.pack:
            self.select_pack()
        if not self.pack:
            return None
        return self.workspace, self.pack

    def visual_matrix(self) -> None:
        required = self._require_workspace_pack()
        if not required:
            return
        workspace, pack = required
        master = workspace / "Artwork" / "MasterWorkspace"
        queue = workspace / "Artwork" / "ART_QUEUE.csv"
        try:
            result = build_visual_completion(
                pack,
                workspace / "Reports" / "VisualCompletion",
                queue=queue if queue.is_file() else None,
                workspace=master if (master / "MASTER_TILES.json").is_file() else None,
                batch_size=max(1, int(self.batch_size.get())),
            )
        except Exception as exc:
            messagebox.showerror("Visual Completion Matrix failed", str(exc))
            return
        dashboard = Path(result["outputs"]["dashboard"])
        webbrowser.open(dashboard.as_uri())
        self.status.set(f"Visual completion: {result['overall_weighted_percent']}% captured-art weighted")
        self._write(
            "VISUAL COMPLETION MATRIX\n\n"
            f"Captured-art weighted completion: {result['overall_weighted_percent']}%\n"
            f"Captured unfinished: {result['captured_unfinished']}\n"
            f"Blocking items: {result['blocking_items']}\n"
            f"Next exact batch: {len(result['next_batch'])}\n\n"
            f"Dashboard: {dashboard}\n\n"
            "Important: this percentage is capture-bounded and is NOT the ROADMAP release percentage."
        )

    def prepare_impact_sprint(self) -> None:
        required = self._require_workspace_pack()
        if not required:
            return
        workspace, pack = required
        master = workspace / "Artwork" / "MasterWorkspace"
        queue = workspace / "Artwork" / "ART_QUEUE.csv"
        kit = workspace / "Artwork" / "CurrentImpactSprint"
        if kit.exists() and any(kit.iterdir()):
            if not messagebox.askyesno("Existing sprint", "CurrentImpactSprint already contains work. Replace it with a fresh exact high-impact batch?"):
                return
        try:
            result = prepare_high_impact_sprint(
                pack,
                master,
                kit,
                workspace / "Reports" / "VisualCompletion",
                queue=queue if queue.is_file() else None,
                batch_size=max(1, int(self.batch_size.get())),
                overwrite=True,
            )
        except Exception as exc:
            messagebox.showerror("High-Impact Sprint failed", str(exc))
            return
        self.status.set(f"High-Impact Sprint: {result['status']} · exported {result['exported']}")
        self._write(
            "EXACT HIGH-IMPACT ART SPRINT READY\n\n"
            f"Status: {result['status']}\nExported: {result['exported']}\nMissing workspace matches: {result['missing']}\n"
            f"Matrix captured unfinished: {result['matrix']['captured_unfinished']}\n"
            f"Kit: {result['kit']}\n\n"
            "Edit only CurrentImpactSprint/editable/*.png. Do not rename or resize. Finish with F8 so stale conflicts, hires.txt mapping and Pixel QA remain enforced."
        )
        self._open_path(kit)
        if result.get("board"):
            webbrowser.open(Path(result["board"]).as_uri())

    def final_readiness(self) -> None:
        required = self._require_workspace_pack()
        if not required:
            return
        workspace, pack = required
        try:
            result = final_release_audit_and_write(
                pack,
                workspace / "CAPTURE_MISSIONS.json",
                workspace / "Artwork" / "ART_QUEUE.csv",
                workspace / "Reports" / "ArtQA" / "ART_QA_RESULT.json",
                workspace / "FINAL_REGRESSION.json",
                workspace / "Artwork" / "VISUAL_CONTEXT_REVIEW.csv",
                workspace / "Reports" / "FullscreenPlaytest" / "FULLSCREEN_PLAYTEST.json",
                workspace / "Reports" / "FinalReleaseReadiness",
            )
        except Exception as exc:
            messagebox.showerror("Final readiness audit failed", str(exc))
            return
        dashboard = workspace / "Reports" / "FinalReleaseReadiness" / "FINAL_RELEASE_READINESS.html"
        webbrowser.open(dashboard.as_uri())
        next_stage = result.get("next_stage")
        next_text = "Build gated ZIP." if not next_stage else f"{next_stage['name']}: {next_stage['action']}"
        self.status.set(f"FINAL RELEASE GATE: {result['release_gate']}")
        self._write(
            f"FINAL RELEASE GATE: {result['release_gate']}\n\n"
            f"Exact build fingerprint: {result['pack_fingerprint']}\n"
            f"Blockers: {len(result['blockers'])}\n\nDO THIS NEXT\n{next_text}\n\nDashboard: {dashboard}"
        )

    def run_windows(self, script_name: str) -> None:
        script = WINDOWS_DIR / script_name
        if not script.is_file():
            messagebox.showerror("Missing launcher", f"Launcher not found:\n{script}")
            return
        if not sys.platform.startswith("win"):
            messagebox.showinfo("Windows launcher", f"This one-click launcher is for Windows:\n{script}")
            return
        try:
            subprocess.Popen(["cmd", "/c", "start", "", str(script)], cwd=str(WINDOWS_DIR), shell=False)
            self.status.set(f"Started {script_name}")
        except Exception as exc:
            messagebox.showerror("Launcher failed", str(exc))

    @staticmethod
    def _open_path(path: Path) -> None:
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception:
            pass


def main() -> int:
    AuthoritativeRemasterStudio().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
