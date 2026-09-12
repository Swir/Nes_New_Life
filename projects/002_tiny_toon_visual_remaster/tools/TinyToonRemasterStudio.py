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
    capture_dashboard,
    gated_release_package,
    initialize_project_evidence,
    record_capture_progress,
    release_audit,
    run_bound_art_qa,
    run_playtest_build,
)
from validate_hdpack import validate


class Studio(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("NES New Life — Tiny Toon Visual Remaster Studio")
        self.geometry("1280x900")
        self.minsize(1040, 720)
        self.rom_path: Path | None = None
        self.workspace: Path | None = None
        self.pack_path: Path | None = None
        self.preview_path: Path | None = None
        self.info = None
        self.data: bytes | None = None
        self.style = tk.StringVar(value="vibrant")
        self._build()

    def _build(self) -> None:
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="PROJECT #002", font=("Segoe UI", 15, "bold")).pack(side="left")
        ttk.Label(top, text="  Tiny Toon Visual Remaster — HD Production Command Center").pack(side="left")

        row1 = ttk.Frame(self, padding=(10, 0, 10, 6)); row1.pack(fill="x")
        for label, command in [
            ("1. Open ROM", self.open_rom),
            ("2. Prepare workspace", self.prepare),
            ("3. Export CHR reference", self.export),
            ("4. Select Mesen capture", self.select_capture),
        ]:
            ttk.Button(row1, text=label, command=command).pack(side="left", padx=3)

        row2 = ttk.Frame(self, padding=(10, 0, 10, 6)); row2.pack(fill="x")
        ttk.Label(row2, text="Preview style:").pack(side="left", padx=(0, 5))
        ttk.Combobox(
            row2,
            textvariable=self.style,
            state="readonly",
            width=13,
            values=("clean", "vibrant", "smooth", "illustrated"),
        ).pack(side="left")
        ttk.Button(row2, text="5. Instant HD Preview", command=self.preview).pack(side="left", padx=5)
        ttk.Button(row2, text="6. Validate", command=self.validate_pack).pack(side="left", padx=3)
        ttk.Button(row2, text="7. Capture report", command=self.report).pack(side="left", padx=3)

        row3 = ttk.Frame(self, padding=(10, 0, 10, 6)); row3.pack(fill="x")
        ttk.Button(row3, text="8. Group art queue", command=self.group_art).pack(side="left", padx=3)
        ttk.Button(row3, text="9. Create master workspace", command=self.create_art_workspace).pack(side="left", padx=3)
        ttk.Button(row3, text="10. Scan art progress", command=self.scan_art_progress).pack(side="left", padx=3)
        ttk.Button(row3, text="11. Apply + build-bound QA", command=self.apply_art_edits).pack(side="left", padx=3)

        row4 = ttk.Frame(self, padding=(10, 0, 10, 6)); row4.pack(fill="x")
        ttk.Button(row4, text="12. Capture Mission Control", command=self.capture_mission_control).pack(side="left", padx=3)
        ttk.Button(row4, text="13. Record capture session", command=self.record_capture_session).pack(side="left", padx=3)
        ttk.Button(row4, text="14. One-click HD Playtest", command=self.one_click_playtest).pack(side="left", padx=3)

        row5 = ttk.Frame(self, padding=(10, 0, 10, 8)); row5.pack(fill="x")
        ttk.Button(row5, text="15. Release Candidate Audit", command=self.release_candidate_audit).pack(side="left", padx=3)
        ttk.Button(row5, text="16. GATED release ZIP", command=self.package_release).pack(side="left", padx=3)
        ttk.Button(row5, text="Open workspace", command=self.open_workspace).pack(side="right", padx=3)

        controls = ttk.LabelFrame(self, text="Recommended MesenCE controls", padding=8)
        controls.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Label(
            controls,
            text="Keyboard: Arrows = D-pad · Z = A · X = B · Enter = Start · Right Shift = Select · Esc = Menu",
        ).pack(anchor="w")
        ttk.Label(
            controls,
            text="Gamepad: use MesenCE input mapping; the remaster keeps the original ROM gameplay, physics and timing unchanged.",
        ).pack(anchor="w")

        self.status = tk.StringVar(value="Open your user-supplied NES ROM. The ROM is never copied to the repository.")
        ttk.Label(self, textvariable=self.status, padding=(10, 2)).pack(fill="x")
        self.text = tk.Text(self, wrap="word", padx=12, pady=12, font=("Consolas", 10))
        self.text.pack(fill="both", expand=True, padx=10, pady=10)
        self._write(
            "Project #002 — Tiny Toon Visual Remaster\n\n"
            "The original ROM remains the gameplay source of truth.\n"
            "Studio now drives capture missions → incremental art → build-bound QA → MesenCE playtest → unified release gate.\n\n"
            "Release packaging cannot bypass Capture Mission Control, current-build Pixel QA, finished art queue or full-game regression."
        )

    def _write(self, text: str) -> None:
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)

    def _active_pack(self) -> Path | None:
        if self.preview_path and (self.preview_path / "hires.txt").is_file():
            return self.preview_path
        if self.workspace:
            for relative in (
                Path("ModernizedPack/final_art"),
                Path("ModernizedPack/playtest_current"),
            ):
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
            "Gamepad\nConfigure your controller in MesenCE Input settings.\n",
            encoding="utf-8",
        )
        (target / "WORKFLOW.txt").write_text(
            "1. Run the local ROM in MesenCE.\n"
            "2. Capture at 4x Prescale with HD Pack Builder.\n"
            "3. Use Capture Mission Control and explicitly verify every mission.\n"
            "4. Sync/group captured graphics and create MasterWorkspace.\n"
            "5. Edit only MasterWorkspace/editable PNGs; keep dimensions unchanged.\n"
            "6. Apply edits; Studio runs build-bound Pixel QA.\n"
            "7. Build/deploy a one-click MesenCE playtest and complete final regression on that exact build.\n"
            "8. Release Candidate Audit must PASS before GATED release ZIP is allowed.\n",
            encoding="utf-8",
        )
        ensure_checklist(target / "HD_READINESS_CHECKLIST.json")
        initialize_project_evidence(target)
        self.workspace = target
        self.status.set(f"Workspace ready: {target}")
        self._write(
            f"Workspace created:\n{target}\n\nROM copied: NO\n\n"
            "Capture Mission Control and build-bound final regression manifests are initialized."
        )

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
        self._write(
            f"Exported {self.info.chr_tile_count} ROM CHR tiles to:\n{out}\n\nManifest:\n{manifest}\n\n"
            "Keep these ROM-derived reference images local."
        )

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
        self._write("\n".join([
            "INSTANT HD PREVIEW READY", "", f"Style: {self.style.get()}", f"Output: {out}",
            f"PNG sheets processed: {len(manifest['images'])}", f"Tile mappings preserved: {manifest['stats']['tile_rules']}",
            f"Validation errors: {len(errors)}", f"Warnings: {len(warnings)}", "", "Next: Group art queue → master workspace → final art.",
        ]))

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
        if not errors:
            lines.append("\nHD pack validation: OK")
        self._write("\n".join(lines))
        self.status.set("Validation failed" if errors else "HD pack validation OK")

    def report(self) -> None:
        pack = self._active_pack()
        if not pack:
            self.select_capture(); pack = self.pack_path
        if not pack: return
        try:
            output = write_report(pack)
        except Exception as exc:
            messagebox.showerror("Report failed", str(exc)); return
        webbrowser.open(output.as_uri())
        self.status.set(f"Capture report generated: {output}")

    def group_art(self) -> None:
        pack = self.pack_path or self._active_pack()
        if not pack:
            self.select_capture(); pack = self.pack_path
        if not pack: return
        output = self.workspace / "Artwork" / "ART_QUEUE.csv" if self.workspace else pack / "NES_NEW_LIFE_ART_QUEUE.csv"
        try:
            write_grouped_art_queue(pack, output)
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
        if overwrite and not messagebox.askyesno("Rebuild master workspace?", "This replaces the existing master workspace. Continue?"):
            return
        try:
            info = init_workspace(pack, target, queue, overwrite=overwrite)
        except Exception as exc:
            messagebox.showerror("Master workspace failed", str(exc)); return
        self.status.set(f"Master workspace ready: {info['master_count']} unique graphics")
        self._write(
            f"MASTER WORKSPACE READY\n\nUnique master graphics: {info['master_count']}\nFolder: {target}\n\n"
            "Edit only Artwork/MasterWorkspace/editable/*.png and keep dimensions unchanged."
        )

    def scan_art_progress(self) -> None:
        target = self._art_workspace()
        if not target or not (target / "MASTER_TILES.json").is_file():
            messagebox.showinfo("No master workspace", "Create the master workspace first."); return
        try:
            result = scan_workspace(target)
        except Exception as exc:
            messagebox.showerror("Art scan failed", str(exc)); return
        self.status.set(f"Art progress: {result['edited']}/{result['masters']} masters edited")
        self._write(
            f"ART PROGRESS\n\nMasters: {result['masters']}\nEdited: {result['edited']}\nTODO: {result['todo']}\n"
            f"Invalid: {result['invalid']}\nEdited: {result['percent_edited']}%\n\nART_STATE.csv has been refreshed."
        )

    def apply_art_edits(self) -> None:
        source = self.pack_path
        target = self._art_workspace()
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
        self._write(
            f"BATCH ART + BUILD-BOUND QA COMPLETE\n\nChanged masters: {result['changed_masters']}\n"
            f"Tile targets updated: {result['targets_updated']}\nMapping preserved: {result['mapping_preserved']}\n"
            f"Pixel QA: {qa['qa_gate']}\nOutput: {out}\n\n"
            "The QA evidence is fingerprint-bound to this exact runtime pack. Any later PNG/hires.txt change makes it stale."
        )

    def capture_mission_control(self) -> None:
        if not self._require_workspace(): return
        try:
            result = capture_dashboard(self.workspace)
        except Exception as exc:
            messagebox.showerror("Mission Control failed", str(exc)); return
        status = result["status"]
        dashboard = Path(result["dashboard"])
        webbrowser.open(dashboard.as_uri())
        next_lines = [f"{item['key']}: {item['label']}" for item in status["next_missions"]]
        self.status.set(f"Capture gate: {status['release_capture_gate']} · {status['done']}/{status['total']}")
        self._write(
            f"CAPTURE MISSION CONTROL\n\nGate: {status['release_capture_gate']}\nCompleted: {status['done']}/{status['total']} ({status['percent']}%)\n"
            f"Stagnating: {status['stagnating']}\n\nNEXT HIGH-IMPACT MISSIONS:\n" + "\n".join(next_lines)
        )

    def record_capture_session(self) -> None:
        if not self._require_workspace(): return
        if not self.pack_path:
            self.select_capture()
            if not self.pack_path: return
        paths = initialize_project_evidence(self.workspace)
        status = mission_status(paths.capture_manifest)
        pending = status["next_missions"]
        hint = "\n".join(f"{item['key']} — {item['label']}" for item in pending)
        raw = simpledialog.askstring(
            "Record capture session",
            "Enter completed mission keys separated by commas. Leave blank to record capture growth only.\n\nHighest priority pending:\n" + hint,
            parent=self,
        )
        if raw is None: return
        completed = [item.strip() for item in raw.split(",") if item.strip()]
        notes = simpledialog.askstring("Session notes", "Optional notes for this capture pass:", parent=self) or ""
        try:
            result = record_capture_progress(self.workspace, self.pack_path, completed=completed, notes=notes)
        except Exception as exc:
            messagebox.showerror("Capture session failed", str(exc)); return
        session = result["session"]
        state = result["status"]
        self.status.set(f"Capture session #{session['id']} recorded · gate {state['release_capture_gate']}")
        self._write(
            f"CAPTURE SESSION #{session['id']}\n\nCompleted missions: {', '.join(session['completed_missions']) or 'none'}\n"
            f"Δ tile rules: {session['delta']['tile_rules']:+d}\nΔ unique tiles: {session['delta']['unique_tile_ids']:+d}\n"
            f"Δ palettes: {session['delta']['unique_palettes']:+d}\nΔ images: {session['delta']['images']:+d}\n\n"
            f"Capture gate: {state['release_capture_gate']} ({state['done']}/{state['total']})"
        )

    def one_click_playtest(self) -> None:
        if not self._require_workspace(): return
        if not self.pack_path:
            self.select_capture()
            if not self.pack_path: return
        deploy = messagebox.askyesno(
            "MesenCE deployment",
            "Build the QA-gated current HD pack and install it into your MesenCE HdPacks folder?\n\n"
            "Choose No to build only. Existing installed pack is backed up when deploying.",
        )
        try:
            result = run_playtest_build(
                self.workspace,
                self.pack_path,
                rom_name=self.rom_path.name if self.rom_path else None,
                deploy=deploy and self.rom_path is not None,
            )
        except Exception as exc:
            messagebox.showerror("HD playtest build failed", str(exc)); return
        self.preview_path = Path(result["output_pack"])
        deployment = result.get("deployment")
        deployed = deployment.get("destination") if deployment else "not deployed"
        self.status.set("QA-gated HD playtest ready")
        self._write(
            f"ONE-CLICK HD PLAYTEST READY\n\nPack: {result['output_pack']}\nMesenCE: {deployed}\n"
            f"Validation errors: {len(result['validation']['errors'])}\nPixel QA: {result['apply']['pixel_qa']['qa_gate']}\n\n"
            "This proves only currently captured content. Capture missions and final build-bound regression still control release readiness."
        )

    def release_candidate_audit(self) -> None:
        if not self._require_workspace(): return
        pack = self._active_pack()
        if not pack:
            messagebox.showinfo("No final pack", "Build/apply the HD pack first."); return
        try:
            result = release_audit(self.workspace, pack)
        except Exception as exc:
            messagebox.showerror("Release audit failed", str(exc)); return
        webbrowser.open(Path(result["dashboard"]).as_uri())
        self.status.set(f"Unified Release Candidate Gate: {result['release_gate']}")
        blockers = "No blockers." if not result["blockers"] else "\n".join("BLOCKER: " + item for item in result["blockers"])
        self._write(
            f"UNIFIED RELEASE CANDIDATE GATE: {result['release_gate']}\n\n"
            f"Build fingerprint: {result['pack_fingerprint']}\n\n{blockers}\n\n"
            "Only a PASS for this exact runtime fingerprint permits Studio packaging."
        )

    def package_release(self) -> None:
        if not self._require_workspace(): return
        pack = self._active_pack()
        if not pack:
            messagebox.showinfo("No final pack", "Build/apply the HD pack first."); return
        output = self.workspace / "Release" / "TinyToon_Visual_Remaster_HD_Pack.zip"
        try:
            result = gated_release_package(self.workspace, pack, output)
        except Exception as exc:
            messagebox.showerror("Packaging blocked", str(exc)); return
        self.status.set(f"GATED release ZIP ready: {result['zip']}")
        self._write(
            f"RELEASE ZIP CREATED\n\n{result['zip']}\n\nGate: {result['release_gate']}\n"
            f"Build fingerprint: {result['pack_fingerprint']}\n\n"
            "The ZIP was created only after the unified capture + art + QA + exact-build regression gate passed."
        )

    @staticmethod
    def _stats_text(stats, pack: Path) -> str:
        return (
            f"HD PACK CAPTURE\n\nFolder: {pack}\nFormat: {stats.version or 'unknown'}\nScale: {stats.scale}x\n"
            f"PNG sheets: {len(stats.images)}\nTile rules: {stats.tile_rules}\nConditional tile rules: {stats.conditional_tile_rules}\n"
            f"Unique tile IDs: {stats.unique_tile_ids}\nUnique palettes: {stats.unique_palettes}\nConditions: {stats.conditions}\n"
            f"Missing images: {len(stats.missing_images)}\n\nNext: Capture Mission Control → Group art queue → Master workspace."
        )

    def open_workspace(self) -> None:
        target = self.workspace or self.preview_path or self.pack_path
        if not target:
            messagebox.showinfo("No workspace", "Prepare or select a workspace first."); return
        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(["explorer", str(target)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(target)])
            else:
                subprocess.Popen(["xdg-open", str(target)])
        except Exception as exc:
            messagebox.showerror("Open folder failed", str(exc))


if __name__ == "__main__":
    Studio().mainloop()
