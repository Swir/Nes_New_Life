from __future__ import annotations

import json
import subprocess
import sys
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from rom_probe import export_chr, human, parse_rom
from validate_hdpack import validate


class Studio(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("NES New Life — Tiny Toon Visual Remaster Studio")
        self.geometry("900x620")
        self.minsize(760, 520)
        self.rom_path: Path | None = None
        self.workspace: Path | None = None
        self.info = None
        self.data: bytes | None = None
        self._build()

    def _build(self) -> None:
        bar = ttk.Frame(self, padding=10); bar.pack(fill="x")
        ttk.Button(bar, text="1. Open ROM", command=self.open_rom).pack(side="left", padx=4)
        ttk.Button(bar, text="2. Prepare workspace", command=self.prepare).pack(side="left", padx=4)
        ttk.Button(bar, text="3. Export CHR reference", command=self.export).pack(side="left", padx=4)
        ttk.Button(bar, text="4. Validate HD Pack", command=self.validate_pack).pack(side="left", padx=4)
        ttk.Button(bar, text="Open workspace", command=self.open_workspace).pack(side="right", padx=4)
        controls = ttk.LabelFrame(self, text="Recommended controls", padding=8); controls.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Label(controls, text="Arrows = D-pad     Z = A     X = B     Enter = Start     Right Shift = Select     Esc = Menu").pack(anchor="w")
        self.status = tk.StringVar(value="Open your user-supplied NES ROM. The ROM is never copied to the repository.")
        ttk.Label(self, textvariable=self.status, padding=(10, 2)).pack(fill="x")
        self.text = tk.Text(self, wrap="word", padx=12, pady=12); self.text.pack(fill="both", expand=True, padx=10, pady=10)
        self._write("Project #002 — Tiny Toon Visual Remaster\n\nPreserve the original ROM-driven gameplay and levels; replace presentation through a Mesen HD Pack.\n")

    def _write(self, text: str) -> None:
        self.text.delete("1.0", "end"); self.text.insert("1.0", text)

    def open_rom(self) -> None:
        value = filedialog.askopenfilename(title="Open NES ROM", filetypes=[("NES ROM", "*.nes"), ("All files", "*.*")])
        if not value: return
        try: info, data = parse_rom(value)
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
        (target / "MesenPack").mkdir(parents=True, exist_ok=True); (target / "Artwork").mkdir(parents=True, exist_ok=True)
        metadata = asdict(self.info); metadata["rom_copied_to_workspace"] = False
        (target / "ROM_INFO.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        (target / "CONTROLS.txt").write_text("Arrows = D-pad\nZ = A\nX = B\nEnter = Start\nRight Shift = Select\nEsc = menu\n", encoding="utf-8")
        (target / "MesenPack" / "README_FIRST.txt").write_text("Run Mesen HD Pack Builder with your local ROM and place generated hires.txt + PNG files here.\n", encoding="utf-8")
        self.workspace = target
        self.status.set(f"Workspace ready: {target}")
        self._write(f"Workspace created:\n{target}\n\nROM copied: NO\n\nNext: record the game with Mesen HD Pack Builder or export CHR references.")

    def export(self) -> None:
        if not self.info or self.data is None:
            messagebox.showinfo("Open ROM first", "Choose the ROM before exporting CHR reference graphics."); return
        if self.workspace:
            out = self.workspace / "reference_chr"
        else:
            folder = filedialog.askdirectory(title="Choose output folder")
            if not folder: return
            out = Path(folder) / "reference_chr"
        try: manifest = export_chr(self.info, self.data, out, scale=4)
        except Exception as exc:
            messagebox.showerror("CHR export failed", str(exc)); return
        self.status.set(f"CHR reference exported: {out}")
        self._write(f"Exported {self.info.chr_tile_count} ROM CHR tiles to:\n{out}\n\nManifest:\n{manifest}\n\nIMPORTANT: these are ROM-derived reference images; keep them local and do not commit them.")

    def validate_pack(self) -> None:
        start = self.workspace / "MesenPack" if self.workspace else None
        folder = filedialog.askdirectory(title="Choose Mesen HD Pack folder", initialdir=str(start) if start else None)
        if not folder: return
        errors, warnings, stats = validate(Path(folder))
        lines = [f"Images: {stats['images']}", f"Tile mappings: {stats['tiles']}", f"Conditional mappings: {stats['conditions']}", ""]
        lines.extend("WARNING: " + x for x in warnings); lines.extend("ERROR: " + x for x in errors)
        if not errors: lines.append("\nHD pack validation: OK")
        self._write("\n".join(lines)); self.status.set("Validation failed" if errors else "HD pack validation OK")

    def open_workspace(self) -> None:
        if not self.workspace:
            messagebox.showinfo("No workspace", "Prepare a workspace first."); return
        try:
            if sys.platform.startswith("win"): subprocess.Popen(["explorer", str(self.workspace)])
            elif sys.platform == "darwin": subprocess.Popen(["open", str(self.workspace)])
            else: subprocess.Popen(["xdg-open", str(self.workspace)])
        except Exception as exc: messagebox.showerror("Open folder failed", str(exc))


if __name__ == "__main__":
    Studio().mainloop()
