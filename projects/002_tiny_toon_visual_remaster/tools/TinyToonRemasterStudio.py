from __future__ import annotations

import json
import subprocess
import sys
import webbrowser
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from art_workspace import apply_workspace, init_workspace, scan_workspace
from hd_readiness import ensure_checklist, package_hd_pack, write_grouped_art_queue, write_readiness_dashboard
from hdpack_pipeline import analyze, build_preview, write_report
from rom_probe import export_chr, human, parse_rom
from validate_hdpack import validate


class Studio(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("NES New Life — Tiny Toon Visual Remaster Studio")
        self.geometry("1220x820")
        self.minsize(980, 680)
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
        ttk.Label(top, text="  Original NES gameplay + modern HD presentation").pack(side="left")

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
        ttk.Combobox(row2, textvariable=self.style, state="readonly", width=13,
                     values=("clean", "vibrant", "smooth", "illustrated")).pack(side="left")
        ttk.Button(row2, text="5. Instant HD Preview", command=self.preview).pack(side="left", padx=5)
        ttk.Button(row2, text="6. Validate", command=self.validate_pack).pack(side="left", padx=3)
        ttk.Button(row2, text="7. Capture report", command=self.report).pack(side="left", padx=3)

        row3 = ttk.Frame(self, padding=(10, 0, 10, 6)); row3.pack(fill="x")
        ttk.Button(row3, text="8. Group art queue", command=self.group_art).pack(side="left", padx=3)
        ttk.Button(row3, text="9. Create master workspace", command=self.create_art_workspace).pack(side="left", padx=3)
        ttk.Button(row3, text="10. Scan art progress", command=self.scan_art_progress).pack(side="left", padx=3)
        ttk.Button(row3, text="11. Apply all master edits", command=self.apply_art_edits).pack(side="left", padx=3)

        row4 = ttk.Frame(self, padding=(10, 0, 10, 8)); row4.pack(fill="x")
        ttk.Button(row4, text="12. HD readiness dashboard", command=self.readiness_dashboard).pack(side="left", padx=3)
        ttk.Button(row4, text="13. Package release ZIP", command=self.package_release).pack(side="left", padx=3)
        ttk.Button(row4, text="Open workspace", command=self.open_workspace).pack(side="right", padx=3)

        controls = ttk.LabelFrame(self, text="Recommended controls", padding=8); controls.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Label(controls, text="Arrows = D-pad     Z = A     X = B     Enter = Start     Right Shift = Select     Esc = Menu").pack(anchor="w")

        self.status = tk.StringVar(value="Open your user-supplied NES ROM. The ROM is never copied to the repository.")
        ttk.Label(self, textvariable=self.status, padding=(10, 2)).pack(fill="x")
        self.text = tk.Text(self, wrap="word", padx=12, pady=12, font=("Consolas", 10)); self.text.pack(fill="both", expand=True, padx=10, pady=10)
        self._write(
            "Project #002 — Tiny Toon Visual Remaster\n\n"
            "The original ROM remains responsible for gameplay, level layout, scrolling and timing.\n"
            "The Studio accelerates capture → art queue → master workspace → batch apply → readiness → release.\n\n"
            "A PASS on the release dashboard requires structural validation plus explicit full-game evidence."
        )

    def _write(self, text: str) -> None:
        self.text.delete("1.0", "end"); self.text.insert("1.0", text)

    def _active_pack(self) -> Path | None:
        return self.preview_path or self.pack_path

    def _art_workspace(self) -> Path | None:
        return self.workspace / "Artwork" / "MasterWorkspace" if self.workspace else None

    def open_rom(self) -> None:
        value = filedialog.askopenfilename(title="Open NES ROM", filetypes=[("NES ROM", "*.nes"), ("All files", "*.*")])
        if not value: return
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
        if not root: return
        target = Path(root) / Path(self.info.filename).stem
        for name in ("MesenCapture", "ModernizedPack", "Artwork", "Release", "reference_chr"):
            (target / name).mkdir(parents=True, exist_ok=True)
        metadata = asdict(self.info); metadata["rom_copied_to_workspace"] = False
        (target / "ROM_INFO.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        (target / "CONTROLS.txt").write_text("Arrows = D-pad\nZ = A\nX = B\nEnter = Start\nRight Shift = Select\nEsc = menu\n", encoding="utf-8")
        (target / "WORKFLOW.txt").write_text(
            "1. Run the local ROM in MesenCE.\n2. Open Tools > HD Pack Builder and capture at 4x Prescale.\n"
            "3. Trigger every menu, route, animation, enemy, boss and effect.\n4. Put hires.txt + PNGs in MesenCapture.\n"
            "5. Select capture and generate the grouped art queue.\n6. Create MasterWorkspace and edit PNGs only in editable/.\n"
            "7. Scan art progress, then Apply all master edits to build one combined pack.\n"
            "8. Mark HD_READINESS_CHECKLIST.json only after real local verification.\n9. Run readiness and package only after validation.\n",
            encoding="utf-8",
        )
        ensure_checklist(target / "HD_READINESS_CHECKLIST.json")
        self.workspace = target
        self.status.set(f"Workspace ready: {target}")
        self._write(f"Workspace created:\n{target}\n\nROM copied: NO\n\nMaster art workflow and readiness checklist are ready.")

    def export(self) -> None:
        if not self.info or self.data is None:
            messagebox.showinfo("Open ROM first", "Choose the ROM before exporting CHR reference graphics."); return
        if self.workspace: out = self.workspace / "reference_chr"
        else:
            folder = filedialog.askdirectory(title="Choose output folder")
            if not folder: return
            out = Path(folder) / "reference_chr"
        try: manifest = export_chr(self.info, self.data, out, scale=4)
        except Exception as exc:
            messagebox.showerror("CHR export failed", str(exc)); return
        self.status.set(f"CHR reference exported: {out}")
        self._write(f"Exported {self.info.chr_tile_count} ROM CHR tiles to:\n{out}\n\nManifest:\n{manifest}\n\nKeep these ROM-derived reference images local.")

    def select_capture(self) -> None:
        initial = self.workspace / "MesenCapture" if self.workspace else None
        folder = filedialog.askdirectory(title="Choose Mesen HD Pack capture folder", initialdir=str(initial) if initial else None)
        if not folder: return
        pack = Path(folder)
        try: stats = analyze(pack)
        except Exception as exc:
            messagebox.showerror("Capture error", str(exc)); return
        self.pack_path = pack; self.preview_path = None
        self.status.set(f"Capture selected: {stats.tile_rules} tile rules, {len(stats.images)} PNG sheets")
        self._write(self._stats_text(stats, pack))

    def preview(self) -> None:
        if not self.pack_path:
            self.select_capture()
            if not self.pack_path: return
        if self.workspace: out = self.workspace / "ModernizedPack" / self.style.get()
        else:
            folder = filedialog.askdirectory(title="Choose output folder for HD preview")
            if not folder: return
            out = Path(folder) / f"NES_New_Life_{self.style.get()}"
        if out.exists() and not messagebox.askyesno("Replace preview?", f"The preview folder already exists:\n{out}\n\nReplace it?"): return
        try:
            manifest = build_preview(self.pack_path, out, self.style.get(), overwrite=True); errors, warnings, _ = validate(out)
        except Exception as exc:
            messagebox.showerror("Preview failed", str(exc)); return
        self.preview_path = out
        self.status.set(f"Instant HD Preview ready: {out}")
        self._write("\n".join(["INSTANT HD PREVIEW READY", "", f"Style: {self.style.get()}", f"Output: {out}",
                                f"PNG sheets processed: {len(manifest['images'])}", f"Tile mappings preserved: {manifest['stats']['tile_rules']}",
                                f"Validation errors: {len(errors)}", f"Warnings: {len(warnings)}", "", "Next: Group art queue → master workspace → batch apply."]))

    def validate_pack(self) -> None:
        start = self._active_pack() or (self.workspace / "MesenCapture" if self.workspace else None)
        if start and (start / "hires.txt").is_file(): folder = start
        else:
            value = filedialog.askdirectory(title="Choose Mesen HD Pack folder", initialdir=str(start) if start else None)
            if not value: return
            folder = Path(value)
        errors, warnings, stats = validate(folder)
        lines = [f"Images: {stats['images']}", f"Tile mappings: {stats['tiles']}", f"Conditional mappings: {stats['conditions']}", ""]
        lines.extend("WARNING: " + item for item in warnings); lines.extend("ERROR: " + item for item in errors)
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
        pack = self._active_pack()
        if not pack:
            self.select_capture(); pack = self.pack_path
        if not pack: return
        output = self.workspace / "Artwork" / "ART_QUEUE.csv" if self.workspace else pack / "NES_NEW_LIFE_ART_QUEUE.csv"
        try: write_grouped_art_queue(pack, output)
        except Exception as exc:
            messagebox.showerror("Art queue failed", str(exc)); return
        self.status.set(f"Grouped art queue ready: {output}")
        self._write(f"ART QUEUE GENERATED\n\n{output}\n\nKnown condition names are grouped. UNASSIGNED remains explicit for local inspection.")

    def create_art_workspace(self) -> None:
        pack = self._active_pack()
        if not pack:
            self.select_capture(); pack = self.pack_path
        if not pack: return
        if not self.workspace:
            messagebox.showinfo("Prepare workspace first", "Create the project workspace before building master art files."); return
        queue = self.workspace / "Artwork" / "ART_QUEUE.csv"
        if not queue.is_file(): write_grouped_art_queue(pack, queue)
        target = self._art_workspace()
        overwrite = bool(target and target.exists() and any(target.iterdir()))
        if overwrite and not messagebox.askyesno("Rebuild master workspace?", "This replaces the existing master workspace. Continue?"): return
        try: info = init_workspace(pack, target, queue, overwrite=overwrite)
        except Exception as exc:
            messagebox.showerror("Master workspace failed", str(exc)); return
        self.status.set(f"Master workspace ready: {info['master_count']} unique graphics")
        self._write(f"MASTER WORKSPACE READY\n\nUnique master graphics: {info['master_count']}\nFolder: {target}\n\nEdit only Artwork/MasterWorkspace/editable/*.png and keep dimensions unchanged.")

    def scan_art_progress(self) -> None:
        target = self._art_workspace()
        if not target or not (target / "MASTER_TILES.json").is_file():
            messagebox.showinfo("No master workspace", "Create the master workspace first."); return
        try: result = scan_workspace(target)
        except Exception as exc:
            messagebox.showerror("Art scan failed", str(exc)); return
        self.status.set(f"Art progress: {result['edited']}/{result['masters']} masters edited")
        self._write(f"ART PROGRESS\n\nMasters: {result['masters']}\nEdited: {result['edited']}\nTODO: {result['todo']}\nInvalid: {result['invalid']}\nEdited: {result['percent_edited']}%\n\nART_STATE.csv has been refreshed.")

    def apply_art_edits(self) -> None:
        pack = self.pack_path or self._active_pack()
        target = self._art_workspace()
        if not pack or not target or not (target / "MASTER_TILES.json").is_file():
            messagebox.showinfo("Missing input", "Select the original Mesen capture and create the master workspace first."); return
        out = self.workspace / "ModernizedPack" / "final_art" if self.workspace else None
        if out is None: return
        try: result = apply_workspace(pack, target, out, overwrite=True)
        except Exception as exc:
            messagebox.showerror("Batch apply failed", str(exc)); return
        self.preview_path = out
        self.status.set(f"Combined HD art pack ready: {result['changed_masters']} masters applied")
        self._write(f"BATCH ART APPLY COMPLETE\n\nChanged masters: {result['changed_masters']}\nTile targets updated: {result['targets_updated']}\nMapping preserved: {result['mapping_preserved']}\nOutput: {out}\n\nAll edited masters were composed into one pack in a single pass.")

    def readiness_dashboard(self) -> None:
        pack = self._active_pack()
        if not pack:
            self.select_capture(); pack = self.pack_path
        if not pack: return
        checklist = self.workspace / "HD_READINESS_CHECKLIST.json" if self.workspace else None
        queue = self.workspace / "Artwork" / "ART_QUEUE.csv" if self.workspace else pack / "NES_NEW_LIFE_ART_QUEUE.csv"
        if checklist: ensure_checklist(checklist)
        if not queue.is_file(): write_grouped_art_queue(pack, queue)
        output = self.workspace / "Release" / "HD_READINESS.html" if self.workspace else pack / "NES_NEW_LIFE_READINESS.html"
        try:
            dashboard = write_readiness_dashboard(pack, checklist, queue, output); result = json.loads(dashboard.with_suffix(".json").read_text(encoding="utf-8"))
        except Exception as exc:
            messagebox.showerror("Readiness failed", str(exc)); return
        webbrowser.open(dashboard.as_uri()); self.status.set(f"Release gate: {result['release_gate']}")
        self._write(f"HD READINESS: {result['release_gate']}\n\n" + ("No blockers.\n" if not result["blockers"] else "\n".join("BLOCKER: " + item for item in result["blockers"])) + "\n\nThis is evidence-based and does not claim coverage for unseen game content.")

    def package_release(self) -> None:
        pack = self._active_pack()
        if not pack:
            self.select_capture(); pack = self.pack_path
        if not pack: return
        if self.workspace: output = self.workspace / "Release" / "TinyToon_Visual_Remaster_HD_Pack.zip"
        else:
            value = filedialog.asksaveasfilename(title="Save release ZIP", defaultextension=".zip", filetypes=[("ZIP archive", "*.zip")])
            if not value: return
            output = Path(value)
        try: package_hd_pack(pack, output)
        except Exception as exc:
            messagebox.showerror("Packaging blocked", str(exc)); return
        self.status.set(f"HD Pack ZIP ready: {output}")
        self._write(f"RELEASE ZIP CREATED\n\n{output}\n\nThe packager validates hires.txt/PNG references and refuses ROM/save/patch files.\nRun the HD readiness dashboard before calling this a complete release.")

    @staticmethod
    def _stats_text(stats, pack: Path) -> str:
        return (f"HD PACK CAPTURE\n\nFolder: {pack}\nFormat: {stats.version or 'unknown'}\nScale: {stats.scale}x\n"
                f"PNG sheets: {len(stats.images)}\nTile rules: {stats.tile_rules}\nConditional tile rules: {stats.conditional_tile_rules}\n"
                f"Unique tile IDs: {stats.unique_tile_ids}\nUnique palettes: {stats.unique_palettes}\nConditions: {stats.conditions}\n"
                f"Missing images: {len(stats.missing_images)}\n\nNext: Group art queue → Create master workspace.")

    def open_workspace(self) -> None:
        target = self.workspace or self.preview_path or self.pack_path
        if not target:
            messagebox.showinfo("No workspace", "Prepare or select a workspace first."); return
        try:
            if sys.platform.startswith("win"): subprocess.Popen(["explorer", str(target)])
            elif sys.platform == "darwin": subprocess.Popen(["open", str(target)])
            else: subprocess.Popen(["xdg-open", str(target)])
        except Exception as exc: messagebox.showerror("Open folder failed", str(exc))


if __name__ == "__main__":
    Studio().mainloop()
