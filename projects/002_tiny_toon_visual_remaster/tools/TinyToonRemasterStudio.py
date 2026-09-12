from __future__ import annotations

import json
import subprocess
import sys
import webbrowser
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from art_workspace import apply_workspace, init_workspace, scan_workspace
from capture_mission_control import mission_status
from hd_readiness import ensure_checklist, write_grouped_art_queue
from hdpack_pipeline import analyze, build_preview, write_report
from rom_probe import export_chr, human, parse_rom
from studio_command_center import (
    animation_family_dashboard,
    capture_dashboard,
    capture_gap_dashboard,
    create_final_art_sprint,
    final_art_priority_dashboard,
    finish_final_art_sprint,
    gated_release_package,
    initialize_project_evidence,
    production_sprint_dashboard,
    record_capture_progress,
    release_audit,
    run_bound_art_qa,
    run_playtest_build,
    visual_context_dashboard,
)
from validate_hdpack import validate


class Studio(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("NES New Life — Tiny Toon Visual Remaster Studio")
        self.geometry("1380x940")
        self.minsize(1120, 760)
        self.rom_path: Path | None = None
        self.workspace: Path | None = None
        self.pack_path: Path | None = None
        self.preview_path: Path | None = None
        self.info = None
        self.data: bytes | None = None
        self.style = tk.StringVar(value="vibrant")
        self.sprint_top = tk.IntVar(value=20)
        self._build()

    def _button_row(self, parent, buttons: list[tuple[str, object]]) -> ttk.Frame:
        row = ttk.Frame(parent, padding=(10, 0, 10, 6))
        row.pack(fill="x")
        for label, command in buttons:
            ttk.Button(row, text=label, command=command).pack(side="left", padx=3)
        return row

    def _build(self) -> None:
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="PROJECT #002", font=("Segoe UI", 15, "bold")).pack(side="left")
        ttk.Label(top, text="  Tiny Toon Visual Remaster — Production Sprint Control Center").pack(side="left")
        ttk.Button(top, text="Open workspace", command=self.open_workspace).pack(side="right", padx=3)

        self._button_row(self, [
            ("1. Open ROM", self.open_rom),
            ("2. Prepare workspace", self.prepare),
            ("3. Export CHR reference", self.export),
            ("4. Select Mesen capture", self.select_capture),
        ])

        row2 = ttk.Frame(self, padding=(10, 0, 10, 6)); row2.pack(fill="x")
        ttk.Label(row2, text="Preview style:").pack(side="left", padx=(0, 5))
        ttk.Combobox(row2, textvariable=self.style, state="readonly", width=13,
                     values=("clean", "vibrant", "smooth", "illustrated")).pack(side="left")
        ttk.Button(row2, text="5. Instant HD Preview", command=self.preview).pack(side="left", padx=5)
        ttk.Button(row2, text="6. Validate", command=self.validate_pack).pack(side="left", padx=3)
        ttk.Button(row2, text="7. Capture report", command=self.report).pack(side="left", padx=3)

        capture_frame = ttk.LabelFrame(self, text="CAPTURE — prove coverage before art", padding=(6, 8))
        capture_frame.pack(fill="x", padx=10, pady=(0, 6))
        self._button_row(capture_frame, [
            ("8. Capture Mission Control", self.capture_mission_control),
            ("9. Record capture session", self.record_capture_session),
            ("10. Capture Gap Planner", self.capture_gap_planner),
            ("11. PRODUCTION SPRINT", self.production_sprint_control),
        ])

        art_frame = ttk.LabelFrame(self, text="ART — classify, review and finish highest-impact captured graphics", padding=(6, 8))
        art_frame.pack(fill="x", padx=10, pady=(0, 6))
        self._button_row(art_frame, [
            ("12. Group art queue", self.group_art),
            ("13. Create master workspace", self.create_art_workspace),
            ("14. Scan art progress", self.scan_art_progress),
            ("15. Visual Context", self.visual_context_review),
            ("16. Animation Families", self.animation_family_review),
            ("17. Final Art Priority", self.final_art_priority),
        ])

        sprint_row = ttk.Frame(art_frame, padding=(10, 0, 10, 4)); sprint_row.pack(fill="x")
        ttk.Label(sprint_row, text="Sprint size:").pack(side="left", padx=(0, 4))
        ttk.Spinbox(sprint_row, from_=1, to=100, textvariable=self.sprint_top, width=5).pack(side="left")
        ttk.Button(sprint_row, text="18. Create Top-N Art Sprint", command=self.create_art_sprint).pack(side="left", padx=5)
        ttk.Button(sprint_row, text="Open CurrentArtSprint", command=self.open_art_sprint).pack(side="left", padx=3)
        ttk.Button(sprint_row, text="19. Finish Sprint + Pixel QA", command=self.finish_art_sprint).pack(side="left", padx=3)
        ttk.Button(sprint_row, text="20. Apply full workspace + QA", command=self.apply_art_edits).pack(side="left", padx=3)

        release_frame = ttk.LabelFrame(self, text="PLAYTEST / RELEASE — exact-build evidence", padding=(6, 8))
        release_frame.pack(fill="x", padx=10, pady=(0, 8))
        self._button_row(release_frame, [
            ("21. One-click HD Playtest", self.one_click_playtest),
            ("22. Release Candidate Audit", self.release_candidate_audit),
            ("23. GATED release ZIP", self.package_release),
        ])

        controls = ttk.LabelFrame(self, text="Recommended MesenCE controls", padding=8)
        controls.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Label(controls, text="Keyboard: Arrows = D-pad · Z = A · X = B · Enter = Start · Right Shift = Select · Esc = Menu").pack(anchor="w")
        ttk.Label(controls, text="Gamepad: configure in MesenCE. The original ROM remains the gameplay/physics/timing source of truth.").pack(anchor="w")

        self.status = tk.StringVar(value="Open your user-supplied NES ROM. The ROM is never copied to the repository.")
        ttk.Label(self, textvariable=self.status, padding=(10, 2)).pack(fill="x")
        self.text = tk.Text(self, wrap="word", padx=12, pady=12, font=("Consolas", 10))
        self.text.pack(fill="both", expand=True, padx=10, pady=10)
        self._write(
            "Project #002 — Tiny Toon Visual Remaster\n\n"
            "The original ROM remains the gameplay source of truth.\n"
            "Recommended loop: capture → Production Sprint → Top-N art sprint → Pixel QA → MesenCE playtest.\n\n"
            "Production Sprint combines Capture Gap, review gates, MasterWorkspace progress and Final Art Priority into one DO THIS NEXT dashboard.\n"
            "Release packaging cannot bypass Capture Mission Control, Visual Context Review, current-build Pixel QA, finished art queue or full-game regression."
        )

    def _write(self, text: str) -> None:
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)

    def _active_pack(self) -> Path | None:
        if self.preview_path and (self.preview_path / "hires.txt").is_file():
            return self.preview_path
        if self.workspace:
            for relative in (Path("ModernizedPack/final_art"), Path("ModernizedPack/playtest_current")):
                candidate = self.workspace / relative
                if (candidate / "hires.txt").is_file():
                    return candidate
        return self.pack_path

    def _art_workspace(self) -> Path | None:
        return self.workspace / "Artwork" / "MasterWorkspace" if self.workspace else None

    def _require_workspace(self) -> bool:
        if self.workspace:
            return True
        messagebox.showinfo("Prepare workspace first", "Create the local Project #002 workspace first.")
        return False

    def _require_capture(self) -> Path | None:
        if self.pack_path and (self.pack_path / "hires.txt").is_file():
            return self.pack_path
        self.select_capture()
        return self.pack_path

    def open_rom(self) -> None:
        value = filedialog.askopenfilename(title="Open NES ROM", filetypes=[("NES ROM", "*.nes"), ("All files", "*.*")])
        if not value:
            return
        try:
            info, data = parse_rom(value)
        except Exception as exc:
            messagebox.showerror("ROM error", str(exc)); return
        self.rom_path, self.info, self.data = Path(value), info, data
        self.status.set("ROM loaded. Project fingerprint match: " + ("YES" if info.known_project_rom else "NO"))
        self._write(human(info) + "\n\nThe ROM stays local. Next: Prepare workspace.")

    def prepare(self) -> None:
        if not self.rom_path or not self.info:
            messagebox.showinfo("Open ROM first", "Choose the ROM before creating a workspace."); return
        root = filedialog.askdirectory(title="Choose parent folder for local remaster workspace")
        if not root:
            return
        target = Path(root) / Path(self.info.filename).stem
        for name in ("MesenCapture", "ModernizedPack", "Artwork", "Release", "Reports", "reference_chr"):
            (target / name).mkdir(parents=True, exist_ok=True)
        metadata = asdict(self.info)
        metadata["rom_copied_to_workspace"] = False
        (target / "ROM_INFO.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        (target / "CONTROLS.txt").write_text(
            "Keyboard\nArrows = D-pad\nZ = A\nX = B\nEnter = Start\nRight Shift = Select\nEsc = menu\n\n"
            "Gamepad\nConfigure your controller in MesenCE Input settings.\n", encoding="utf-8")
        (target / "WORKFLOW.txt").write_text(
            "1. Run the local ROM in MesenCE and capture at 4x Prescale.\n"
            "2. Record Capture Mission Control progress.\n"
            "3. Run Production Sprint / Capture Gap and resolve regressions.\n"
            "4. Sync/group art and create MasterWorkspace.\n"
            "5. Clear Visual Context / Animation reviews.\n"
            "6. Create a Top-N Final Art Sprint and edit CurrentArtSprint/editable PNGs only.\n"
            "7. Finish Sprint + Pixel QA, then deploy One-click HD Playtest.\n"
            "8. Complete exact-build full-game regression.\n"
            "9. Release Candidate Audit must PASS before GATED release ZIP.\n", encoding="utf-8")
        ensure_checklist(target / "HD_READINESS_CHECKLIST.json")
        initialize_project_evidence(target)
        self.workspace = target
        self.status.set(f"Workspace ready: {target}")
        self._write(f"Workspace created:\n{target}\n\nROM copied: NO\n\nProduction evidence manifests are initialized.")

    def export(self) -> None:
        if not self.info or self.data is None:
            messagebox.showinfo("Open ROM first", "Choose the ROM before exporting CHR reference graphics."); return
        if self.workspace:
            out = self.workspace / "reference_chr"
        else:
            folder = filedialog.askdirectory(title="Choose output folder")
            if not folder: return
            out = Path(folder) / "reference_chr"
        try:
            manifest = export_chr(self.info, self.data, out, scale=4)
        except Exception as exc:
            messagebox.showerror("CHR export failed", str(exc)); return
        self.status.set(f"CHR reference exported: {out}")
        self._write(f"Exported {self.info.chr_tile_count} ROM CHR tiles to:\n{out}\n\nManifest:\n{manifest}\n\nKeep these ROM-derived reference images local.")

    def select_capture(self) -> None:
        initial = self.workspace / "MesenCapture" if self.workspace else None
        folder = filedialog.askdirectory(title="Choose Mesen HD Pack capture folder", initialdir=str(initial) if initial else None)
        if not folder: return
        pack = Path(folder)
        try:
            stats = analyze(pack)
        except Exception as exc:
            messagebox.showerror("Capture error", str(exc)); return
        self.pack_path = pack
        self.preview_path = None
        self.status.set(f"Capture selected: {stats.tile_rules} tile rules, {len(stats.images)} PNG sheets")
        self._write(self._stats_text(stats, pack))

    def preview(self) -> None:
        if not self.pack_path:
            self.select_capture()
            if not self.pack_path: return
        if self.workspace:
            out = self.workspace / "ModernizedPack" / self.style.get()
        else:
            folder = filedialog.askdirectory(title="Choose output folder for HD preview")
            if not folder: return
            out = Path(folder) / f"NES_New_Life_{self.style.get()}"
        if out.exists() and not messagebox.askyesno("Replace preview?", f"The preview folder already exists:\n{out}\n\nReplace it?"):
            return
        try:
            manifest = build_preview(self.pack_path, out, self.style.get(), overwrite=True)
            errors, warnings, _ = validate(out)
        except Exception as exc:
            messagebox.showerror("Preview failed", str(exc)); return
        self.preview_path = out
        self.status.set(f"Instant HD Preview ready: {out}")
        self._write("\n".join(["INSTANT HD PREVIEW READY", "", f"Style: {self.style.get()}", f"Output: {out}", f"PNG sheets processed: {len(manifest['images'])}", f"Tile mappings preserved: {manifest['stats']['tile_rules']}", f"Validation errors: {len(errors)}", f"Warnings: {len(warnings)}", "", "Next: Production Sprint → highest-impact art."]))

    def validate_pack(self) -> None:
        start = self._active_pack() or (self.workspace / "MesenCapture" if self.workspace else None)
        if start and (start / "hires.txt").is_file():
            folder = start
        else:
            value = filedialog.askdirectory(title="Choose Mesen HD Pack folder", initialdir=str(start) if start else None)
            if not value: return
            folder = Path(value)
        errors, warnings, stats = validate(folder)
        lines = [f"Images: {stats['images']}", f"Tile mappings: {stats['tiles']}", f"Conditional mappings: {stats['conditions']}", ""]
        lines.extend("WARNING: " + item for item in warnings)
        lines.extend("ERROR: " + item for item in errors)
        if not errors: lines.append("\nHD pack validation: OK")
        self._write("\n".join(lines)); self.status.set("Validation failed" if errors else "HD pack validation OK")

    def report(self) -> None:
        pack = self._active_pack()
        if not pack:
            self.select_capture(); pack = self.pack_path
        if not pack: return
        try: output = write_report(pack)
        except Exception as exc:
            messagebox.showerror("Report failed", str(exc)); return
        webbrowser.open(output.as_uri()); self.status.set(f"Capture report generated: {output}")

    def group_art(self) -> None:
        pack = self.pack_path or self._active_pack()
        if not pack:
            self.select_capture(); pack = self.pack_path
        if not pack: return
        output = self.workspace / "Artwork" / "ART_QUEUE.csv" if self.workspace else pack / "NES_NEW_LIFE_ART_QUEUE.csv"
        try: write_grouped_art_queue(pack, output)
        except Exception as exc:
            messagebox.showerror("Art queue failed", str(exc)); return
        self.status.set(f"Grouped art queue ready: {output}")
        self._write(f"ART QUEUE GENERATED\n\n{output}\n\nUNASSIGNED remains explicit and blocks final release until classified.")

    def create_art_workspace(self) -> None:
        pack = self.pack_path or self._active_pack()
        if not pack:
            self.select_capture(); pack = self.pack_path
        if not pack or not self._require_workspace(): return
        queue = self.workspace / "Artwork" / "ART_QUEUE.csv"
        if not queue.is_file(): write_grouped_art_queue(pack, queue)
        target = self._art_workspace()
        overwrite = bool(target and target.exists() and any(target.iterdir()))
        if overwrite and not messagebox.askyesno("Rebuild master workspace?", "This replaces the existing master workspace. Continue?"): return
        try: info = init_workspace(pack, target, queue, overwrite=overwrite)
        except Exception as exc:
            messagebox.showerror("Master workspace failed", str(exc)); return
        self.status.set(f"Master workspace ready: {info['master_count']} unique graphics")
        self._write(f"MASTER WORKSPACE READY\n\nUnique master graphics: {info['master_count']}\nFolder: {target}\n\nUse Final Art Priority / Top-N Sprint instead of hunting files manually.")

    def scan_art_progress(self) -> None:
        target = self._art_workspace()
        if not target or not (target / "MASTER_TILES.json").is_file():
            messagebox.showinfo("No master workspace", "Create the master workspace first."); return
        try: result = scan_workspace(target)
        except Exception as exc:
            messagebox.showerror("Art scan failed", str(exc)); return
        self.status.set(f"Art progress: {result['edited']}/{result['masters']} masters edited")
        self._write(f"ART PROGRESS\n\nMasters: {result['masters']}\nEdited: {result['edited']}\nTODO: {result['todo']}\nInvalid: {result['invalid']}\nEdited: {result['percent_edited']}%\n\nART_STATE.csv refreshed.")

    def capture_mission_control(self) -> None:
        if not self._require_workspace(): return
        try: result = capture_dashboard(self.workspace)
        except Exception as exc:
            messagebox.showerror("Mission Control failed", str(exc)); return
        status = result["status"]; dashboard = Path(result["dashboard"]); webbrowser.open(dashboard.as_uri())
        next_lines = [f"{item['key']}: {item['label']}" for item in status["next_missions"]]
        self.status.set(f"Capture gate: {status['release_capture_gate']} · {status['done']}/{status['total']}")
        self._write(f"CAPTURE MISSION CONTROL\n\nGate: {status['release_capture_gate']}\nCompleted: {status['done']}/{status['total']} ({status['percent']}%)\nStagnating: {status['stagnating']}\n\nNEXT HIGH-IMPACT MISSIONS:\n" + "\n".join(next_lines))

    def record_capture_session(self) -> None:
        if not self._require_workspace(): return
        if not self.pack_path:
            self.select_capture()
            if not self.pack_path: return
        paths = initialize_project_evidence(self.workspace); status = mission_status(paths.capture_manifest); pending = status["next_missions"]
        hint = "\n".join(f"{item['key']} — {item['label']}" for item in pending)
        raw = simpledialog.askstring("Record capture session", "Enter completed mission keys separated by commas. Leave blank to record capture growth only.\n\nHighest priority pending:\n" + hint, parent=self)
        if raw is None: return
        completed = [item.strip() for item in raw.split(",") if item.strip()]
        notes = simpledialog.askstring("Session notes", "Optional notes for this capture pass:", parent=self) or ""
        try: result = record_capture_progress(self.workspace, self.pack_path, completed=completed, notes=notes)
        except Exception as exc:
            messagebox.showerror("Capture session failed", str(exc)); return
        session = result["session"]; state = result["status"]
        self.status.set(f"Capture session #{session['id']} recorded · gate {state['release_capture_gate']}")
        self._write(f"CAPTURE SESSION #{session['id']}\n\nCompleted missions: {', '.join(session['completed_missions']) or 'none'}\nΔ tile rules: {session['delta']['tile_rules']:+d}\nΔ unique tiles: {session['delta']['unique_tile_ids']:+d}\nΔ palettes: {session['delta']['unique_palettes']:+d}\nΔ images: {session['delta']['images']:+d}\n\nCapture gate: {state['release_capture_gate']} ({state['done']}/{state['total']})")

    def capture_gap_planner(self) -> None:
        if not self._require_workspace(): return
        current = self._require_capture()
        if not current: return
        previous = None
        if messagebox.askyesno("Compare captures?", "Select a previous Mesen capture to detect coverage regressions?\n\nChoose No for a current-capture-only gap plan."):
            value = filedialog.askdirectory(title="Choose previous Mesen capture")
            if value: previous = Path(value)
        try: result = capture_gap_dashboard(self.workspace, current, previous_capture=previous)
        except Exception as exc:
            messagebox.showerror("Capture Gap Planner failed", str(exc)); return
        dashboard = Path(result["outputs"]["html"]); webbrowser.open(dashboard.as_uri())
        rows = result.get("queue", [])[:8]
        self.status.set(f"Capture Gap plan ready · {len(result.get('queue', []))} targets")
        self._write("CAPTURE NEXT\n\n" + "\n".join(f"{r.get('priority','?')} · {r.get('kind','')} · {r.get('label') or r.get('family') or r.get('state') or ''}" for r in rows) + f"\n\nDashboard: {dashboard}")

    def production_sprint_control(self) -> None:
        if not self._require_workspace(): return
        current = self._require_capture()
        if not current: return
        pack = self._active_pack() or current
        try: result = production_sprint_dashboard(self.workspace, current, pack, top=max(1, int(self.sprint_top.get())))
        except Exception as exc:
            messagebox.showerror("Production Sprint failed", str(exc)); return
        dashboard = Path(result["outputs"]["dashboard"]); webbrowser.open(dashboard.as_uri())
        self.status.set("Production Sprint dashboard refreshed")
        self._write("PRODUCTION SPRINT — DO THIS NEXT\n\n" + "\n".join(f"{item['priority']} · {item['stage']} · {item['action']}" for item in result["actions"]) + f"\n\nDashboard: {dashboard}")

    def visual_context_review(self) -> None:
        if not self._require_workspace(): return
        pack = self._active_pack() or self._require_capture()
        if not pack: return
        try: result = visual_context_dashboard(self.workspace, pack)
        except Exception as exc:
            messagebox.showerror("Visual Context failed", str(exc)); return
        dashboard = Path(result["dashboard"]); webbrowser.open(dashboard.as_uri())
        self.status.set(f"Visual Context: {result['gate']} · pending {result['pending']} · stale {result['stale']}")
        self._write(f"VISUAL CONTEXT REVIEW\n\nGate: {result['gate']}\nRequired: {result['review_required']}\nPending: {result['pending']}\nStale: {result['stale']}\n\nReview file: {result['review']}\nDashboard: {dashboard}")

    def animation_family_review(self) -> None:
        if not self._require_workspace(): return
        pack = self._active_pack() or self._require_capture()
        if not pack: return
        contact = messagebox.askyesno("Animation contact sheets", "Create LOCAL contact sheets for animation-family review?\n\nThey may contain ROM-derived captured graphics and stay inside local Reports only.")
        try: result = animation_family_dashboard(self.workspace, pack, create_contact_sheets=contact)
        except Exception as exc:
            messagebox.showerror("Animation Workbench failed", str(exc)); return
        dashboard = Path(result["dashboard"]); webbrowser.open(dashboard.as_uri())
        self.status.set(f"Animation families: {result['gate']} · pending {result['pending']}")
        self._write(f"ANIMATION FAMILY WORKBENCH\n\nGate: {result['gate']}\nRequired: {result['review_required']}\nPending: {result['pending']}\nStale: {result['stale']}\n\nDashboard: {dashboard}")

    def final_art_priority(self) -> None:
        if not self._require_workspace(): return
        pack = self._active_pack() or self._require_capture()
        if not pack: return
        try: result = final_art_priority_dashboard(self.workspace, pack, top=max(1, int(self.sprint_top.get())))
        except Exception as exc:
            messagebox.showerror("Final Art Priority failed", str(exc)); return
        dashboard = Path(result["dashboard"]); webbrowser.open(dashboard.as_uri())
        self.status.set(f"Final Art Priority: {result['unfinished_candidates']} unfinished captured candidates")
        lines = [f"#{r['priority']} score={r['priority_score']} {r['group']} tile={r['tile_id']} {', '.join(r['reasons'])}" for r in result["items"][:10]]
        self._write("FINAL ART NEXT\n\n" + "\n".join(lines) + f"\n\nDashboard: {dashboard}")

    def create_art_sprint(self) -> None:
        if not self._require_workspace(): return
        pack = self._active_pack() or self._require_capture()
        if not pack: return
        try: result = create_final_art_sprint(self.workspace, pack, top=max(1, int(self.sprint_top.get())), overwrite=True)
        except Exception as exc:
            messagebox.showerror("Create Art Sprint failed", str(exc)); return
        kit = self.workspace / "Artwork" / "CurrentArtSprint"
        self.status.set(f"Art Sprint ready: {result.get('items', result.get('count', '?'))} prioritized items")
        self._write(f"FINAL ART SPRINT READY\n\nFolder: {kit}\n\nEdit only CurrentArtSprint/editable/*.png. Keep every image at exactly the same dimensions.\nWhen finished, click Finish Sprint + Pixel QA.")
        self._open_path(kit)

    def open_art_sprint(self) -> None:
        if not self._require_workspace(): return
        target = self.workspace / "Artwork" / "CurrentArtSprint"
        if not target.exists():
            messagebox.showinfo("No current sprint", "Create a Top-N Art Sprint first."); return
        self._open_path(target)

    def finish_art_sprint(self) -> None:
        if not self._require_workspace(): return
        source = self.pack_path or self._active_pack()
        if not source:
            messagebox.showinfo("No source pack", "Select the accepted Mesen capture first."); return
        out = self.workspace / "ModernizedPack" / "final_art"
        try: result = finish_final_art_sprint(self.workspace, source, out, overwrite=True)
        except Exception as exc:
            messagebox.showerror("Finish Art Sprint failed", str(exc)); return
        self.preview_path = out
        self.status.set(f"Art Sprint finished · Pixel QA {result['qa_gate']}")
        self._write(f"ART SPRINT FINISHED SAFELY\n\nOutput: {out}\nImported edits: {result.get('imported', result.get('changed_masters', '?'))}\nMapping preserved: {result['mapping_preserved']}\nPixel QA: {result['qa_gate']}\n\nNext: refresh Production Sprint / Final Art Priority, then One-click HD Playtest.")

    def apply_art_edits(self) -> None:
        source = self.pack_path; target = self._art_workspace()
        if not source or not target or not (target / "MASTER_TILES.json").is_file() or not self._require_workspace():
            messagebox.showinfo("Missing input", "Select the original Mesen capture and create the master workspace first."); return
        out = self.workspace / "ModernizedPack" / "final_art"
        try:
            result = apply_workspace(source, target, out, overwrite=True)
            qa = run_bound_art_qa(self.workspace, source, out)
        except Exception as exc:
            messagebox.showerror("Batch apply / QA failed", str(exc)); return
        self.preview_path = out
        self.status.set(f"Final-art pack: {result['changed_masters']} masters · build-bound QA {qa['qa_gate']}")
        self._write(f"BATCH ART + BUILD-BOUND QA COMPLETE\n\nChanged masters: {result['changed_masters']}\nTile targets updated: {result['targets_updated']}\nMapping preserved: {result['mapping_preserved']}\nPixel QA: {qa['qa_gate']}\nOutput: {out}\n\nAny later PNG/hires.txt change makes this exact-build QA evidence stale.")

    def one_click_playtest(self) -> None:
        if not self._require_workspace(): return
        if not self.pack_path:
            self.select_capture()
            if not self.pack_path: return
        deploy = messagebox.askyesno("MesenCE deployment", "Build the QA-gated current HD pack and install it into your MesenCE HdPacks folder?\n\nChoose No to build only. Existing installed pack is backed up when deploying.")
        try: result = run_playtest_build(self.workspace, self.pack_path, rom_name=self.rom_path.name if self.rom_path else None, deploy=deploy and self.rom_path is not None)
        except Exception as exc:
            messagebox.showerror("HD playtest build failed", str(exc)); return
        self.preview_path = Path(result["output_pack"]); deployment = result.get("deployment"); deployed = deployment.get("destination") if deployment else "not deployed"
        self.status.set("QA-gated HD playtest ready")
        self._write(f"ONE-CLICK HD PLAYTEST READY\n\nPack: {result['output_pack']}\nMesenCE: {deployed}\nValidation errors: {len(result['validation']['errors'])}\nPixel QA: {result['apply']['pixel_qa']['qa_gate']}\n\nThis proves only currently captured content. Capture missions and exact-build regression still control release readiness.")

    def release_candidate_audit(self) -> None:
        if not self._require_workspace(): return
        pack = self._active_pack()
        if not pack:
            messagebox.showinfo("No final pack", "Build/apply the HD pack first."); return
        try: result = release_audit(self.workspace, pack)
        except Exception as exc:
            messagebox.showerror("Release audit failed", str(exc)); return
        webbrowser.open(Path(result["dashboard"]).as_uri()); self.status.set(f"Unified Release Candidate Gate: {result['release_gate']}")
        blockers = "No blockers." if not result["blockers"] else "\n".join("BLOCKER: " + item for item in result["blockers"])
        self._write(f"UNIFIED RELEASE CANDIDATE GATE: {result['release_gate']}\n\nBuild fingerprint: {result['pack_fingerprint']}\n\n{blockers}\n\nOnly a PASS for this exact runtime fingerprint permits Studio packaging.")

    def package_release(self) -> None:
        if not self._require_workspace(): return
        pack = self._active_pack()
        if not pack:
            messagebox.showinfo("No final pack", "Build/apply the HD pack first."); return
        output = self.workspace / "Release" / "TinyToon_Visual_Remaster_HD_Pack.zip"
        try: result = gated_release_package(self.workspace, pack, output)
        except Exception as exc:
            messagebox.showerror("Packaging blocked", str(exc)); return
        self.status.set(f"GATED release ZIP ready: {result['zip']}")
        self._write(f"RELEASE ZIP CREATED\n\n{result['zip']}\n\nGate: {result['release_gate']}\nBuild fingerprint: {result['pack_fingerprint']}\n\nThe ZIP was created only after the unified capture + art + QA + exact-build regression gate passed.")

    @staticmethod
    def _stats_text(stats, pack: Path) -> str:
        return (f"HD PACK CAPTURE\n\nFolder: {pack}\nFormat: {stats.version or 'unknown'}\nScale: {stats.scale}x\nPNG sheets: {len(stats.images)}\nTile rules: {stats.tile_rules}\nConditional tile rules: {stats.conditional_tile_rules}\nUnique tile IDs: {stats.unique_tile_ids}\nUnique palettes: {stats.unique_palettes}\nConditions: {stats.conditions}\nMissing images: {len(stats.missing_images)}\n\nNext: Capture Mission Control → Production Sprint.")

    def _open_path(self, target: Path) -> None:
        try:
            if sys.platform.startswith("win"): subprocess.Popen(["explorer", str(target)])
            elif sys.platform == "darwin": subprocess.Popen(["open", str(target)])
            else: subprocess.Popen(["xdg-open", str(target)])
        except Exception as exc: messagebox.showerror("Open folder failed", str(exc))

    def open_workspace(self) -> None:
        target = self.workspace or self.preview_path or self.pack_path
        if not target:
            messagebox.showinfo("No workspace", "Prepare or select a workspace first."); return
        self._open_path(target)


if __name__ == "__main__":
    Studio().mainloop()
