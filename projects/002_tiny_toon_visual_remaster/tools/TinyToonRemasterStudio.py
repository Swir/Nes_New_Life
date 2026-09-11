from __future__ import annotations

import json
import subprocess
import sys
import webbrowser
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from hdpack_pipeline import analyze, build_preview, write_report
from rom_probe import export_chr, human, parse_rom
from validate_hdpack import validate


class Studio(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("NES New Life — Tiny Toon Visual Remaster Studio")
        self.geometry("1080x720")
        self.minsize(880, 600)
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

        row1 = ttk.Frame(self, padding=(10, 0, 10, 6))
        row1.pack(fill="x")
        for label, command in [
            ("1. Open ROM", self.open_rom),
            ("2. Prepare workspace", self.prepare),
            ("3. Export CHR reference", self.export),
            ("4. Select Mesen capture", self.select_capture),
        ]:
            ttk.Button(row1, text=label, command=command).pack(side="left", padx=3)

        row2 = ttk.Frame(self, padding=(10, 0, 10, 6))
        row2.pack(fill="x")
        ttk.Label(row2, text="Preview style:").pack(side="left", padx=(0, 5))
        ttk.Combobox(
            row2,
            textvariable=self.style,
            state="readonly",
            width=13,
            values=("clean", "vibrant", "smooth", "illustrated"),
        ).pack(side="left")
        ttk.Button(row2, text="5. Build Instant HD Preview", command=self.preview).pack(side="left", padx=5)
        ttk.Button(row2, text="6. Validate pack", command=self.validate_pack).pack(side="left", padx=3)
        ttk.Button(row2, text="7. HTML report", command=self.report).pack(side="left", padx=3)
        ttk.Button(row2, text="Open workspace", command=self.open_workspace).pack(side="right", padx=3)

        controls = ttk.LabelFrame(self, text="Recommended controls", padding=8)
        controls.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Label(
            controls,
            text="Arrows = D-pad     Z = A     X = B     Enter = Start     Right Shift = Select     Esc = Menu",
        ).pack(anchor="w")

        self.status = tk.StringVar(
            value="Open your user-supplied NES ROM. The ROM is never copied to the repository."
        )
        ttk.Label(self, textvariable=self.status, padding=(10, 2)).pack(fill="x")
        self.text = tk.Text(self, wrap="word", padx=12, pady=12, font=("Consolas", 10))
        self.text.pack(fill="both", expand=True, padx=10, pady=10)
        self._write(
            "Project #002 — Tiny Toon Visual Remaster\n\n"
            "The ROM remains responsible for gameplay, level layout, scrolling and timing.\n"
            "Our tools only prepare and validate the presentation layer.\n\n"
            "Fast path: Open ROM → Prepare workspace → record with MesenCE HD Pack Builder → "
            "Select capture → Instant HD Preview."
        )

    def _write(self, text: str) -> None:
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)

    def open_rom(self) -> None:
        value = filedialog.askopenfilename(
            title="Open NES ROM",
            filetypes=[("NES ROM", "*.nes"), ("All files", "*.*")],
        )
        if not value:
            return
        try:
            info, data = parse_rom(value)
        except Exception as exc:
            messagebox.showerror("ROM error", str(exc))
            return
        self.rom_path, self.info, self.data = Path(value), info, data
        self.status.set("ROM loaded. Project fingerprint match: " + ("YES" if info.known_project_rom else "NO"))
        self._write(human(info) + "\n\nThe ROM stays local. Next: Prepare workspace.")

    def prepare(self) -> None:
        if not self.rom_path or not self.info:
            messagebox.showinfo("Open ROM first", "Choose the ROM before creating a workspace.")
            return
        root = filedialog.askdirectory(title="Choose parent folder for local remaster workspace")
        if not root:
            return
        target = Path(root) / Path(self.info.filename).stem
        for name in ("MesenCapture", "ModernizedPack", "Artwork", "reference_chr"):
            (target / name).mkdir(parents=True, exist_ok=True)

        metadata = asdict(self.info)
        metadata["rom_copied_to_workspace"] = False
        (target / "ROM_INFO.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        (target / "CONTROLS.txt").write_text(
            "Arrows = D-pad\nZ = A\nX = B\nEnter = Start\nRight Shift = Select\nEsc = menu\n",
            encoding="utf-8",
        )
        (target / "WORKFLOW.txt").write_text(
            "1. Run the local ROM in MesenCE.\n"
            "2. Open Tools > HD Pack Builder.\n"
            "3. Use scale 4 and a Prescale filter.\n"
            "4. Record gameplay and trigger every animation/effect.\n"
            "5. Put the resulting hires.txt + PNGs in MesenCapture.\n"
            "6. Run Instant HD Preview from Studio.\n",
            encoding="utf-8",
        )
        self.workspace = target
        self.status.set(f"Workspace ready: {target}")
        self._write(
            f"Workspace created:\n{target}\n\nROM copied: NO\n\n"
            "Recommended capture: MesenCE HD Pack Builder, 4x Prescale.\n"
            "Then select the capture folder and build an Instant HD Preview."
        )

    def export(self) -> None:
        if not self.info or self.data is None:
            messagebox.showinfo("Open ROM first", "Choose the ROM before exporting CHR reference graphics.")
            return
        if self.workspace:
            out = self.workspace / "reference_chr"
        else:
            folder = filedialog.askdirectory(title="Choose output folder")
            if not folder:
                return
            out = Path(folder) / "reference_chr"
        try:
            manifest = export_chr(self.info, self.data, out, scale=4)
        except Exception as exc:
            messagebox.showerror("CHR export failed", str(exc))
            return
        self.status.set(f"CHR reference exported: {out}")
        self._write(
            f"Exported {self.info.chr_tile_count} ROM CHR tiles to:\n{out}\n\nManifest:\n{manifest}\n\n"
            "Keep these ROM-derived reference images local."
        )

    def select_capture(self) -> None:
        initial = self.workspace / "MesenCapture" if self.workspace else None
        folder = filedialog.askdirectory(
            title="Choose Mesen HD Pack capture folder",
            initialdir=str(initial) if initial else None,
        )
        if not folder:
            return
        pack = Path(folder)
        try:
            stats = analyze(pack)
        except Exception as exc:
            messagebox.showerror("Capture error", str(exc))
            return
        self.pack_path = pack
        self.status.set(f"Capture selected: {stats.tile_rules} tile rules, {len(stats.images)} PNG sheets")
        self._write(self._stats_text(stats, pack))

    def preview(self) -> None:
        if not self.pack_path:
            self.select_capture()
            if not self.pack_path:
                return

        if self.workspace:
            out = self.workspace / "ModernizedPack" / self.style.get()
        else:
            folder = filedialog.askdirectory(title="Choose output folder for HD preview")
            if not folder:
                return
            out = Path(folder) / f"NES_New_Life_{self.style.get()}"

        if out.exists() and not messagebox.askyesno(
            "Replace preview?",
            f"The preview folder already exists:\n{out}\n\nReplace it?",
        ):
            return

        try:
            manifest = build_preview(self.pack_path, out, self.style.get(), overwrite=True)
            errors, warnings, _ = validate(out)
        except Exception as exc:
            messagebox.showerror("Preview failed", str(exc))
            return

        self.preview_path = out
        self.status.set(f"Instant HD Preview ready: {out}")
        self._write(
            "\n".join(
                [
                    "INSTANT HD PREVIEW READY",
                    "",
                    f"Style: {self.style.get()}",
                    f"Output: {out}",
                    f"PNG sheets processed: {len(manifest['images'])}",
                    f"Tile mappings preserved: {manifest['stats']['tile_rules']}",
                    f"Validation errors: {len(errors)}",
                    f"Warnings: {len(warnings)}",
                    "",
                    "This is a fast automated visual baseline. Final artwork can replace the PNGs later "
                    "without changing the ROM or level logic.",
                ]
            )
        )

    def validate_pack(self) -> None:
        start = self.preview_path or self.pack_path or (self.workspace / "MesenCapture" if self.workspace else None)
        if start and (start / "hires.txt").is_file():
            folder = start
        else:
            value = filedialog.askdirectory(
                title="Choose Mesen HD Pack folder",
                initialdir=str(start) if start else None,
            )
            if not value:
                return
            folder = Path(value)

        errors, warnings, stats = validate(folder)
        lines = [
            f"Images: {stats['images']}",
            f"Tile mappings: {stats['tiles']}",
            f"Conditional mappings: {stats['conditions']}",
            "",
        ]
        lines.extend("WARNING: " + item for item in warnings)
        lines.extend("ERROR: " + item for item in errors)
        if not errors:
            lines.append("\nHD pack validation: OK")
        self._write("\n".join(lines))
        self.status.set("Validation failed" if errors else "HD pack validation OK")

    def report(self) -> None:
        pack = self.preview_path or self.pack_path
        if not pack:
            self.select_capture()
            pack = self.pack_path
        if not pack:
            return
        try:
            output = write_report(pack)
        except Exception as exc:
            messagebox.showerror("Report failed", str(exc))
            return
        webbrowser.open(output.as_uri())
        self.status.set(f"Report generated: {output}")

    @staticmethod
    def _stats_text(stats, pack: Path) -> str:
        return (
            f"HD PACK CAPTURE\n\nFolder: {pack}\nFormat: {stats.version or 'unknown'}\nScale: {stats.scale}x\n"
            f"PNG sheets: {len(stats.images)}\nTile rules: {stats.tile_rules}\n"
            f"Conditional tile rules: {stats.conditional_tile_rules}\nUnique tile IDs: {stats.unique_tile_ids}\n"
            f"Unique palettes: {stats.unique_palettes}\nConditions: {stats.conditions}\n"
            f"Missing images: {len(stats.missing_images)}\n\nNext: Build Instant HD Preview."
        )

    def open_workspace(self) -> None:
        target = self.workspace or self.preview_path or self.pack_path
        if not target:
            messagebox.showinfo("No workspace", "Prepare or select a workspace first.")
            return
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
