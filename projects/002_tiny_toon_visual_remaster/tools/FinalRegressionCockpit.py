from __future__ import annotations

import subprocess
import sys
import webbrowser
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from final_regression_cockpit import FAILURE_CATEGORIES, build_and_write, record_case_result


class RegressionCockpit(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Project #002 — Final Regression Cockpit")
        self.geometry("1040x720")
        self.minsize(900, 620)
        self.workspace: Path | None = None
        self.pack: Path | None = None
        self.status_data: dict | None = None
        self.workspace_var = tk.StringVar(value="No workspace selected")
        self.pack_var = tk.StringVar(value="No exact HD pack selected")
        self.next_var = tk.StringVar(value="Select workspace and exact pack, then Refresh")
        self._build()

    def _build(self) -> None:
        top = ttk.Frame(self, padding=12); top.pack(fill="x")
        ttk.Label(top, text="FINAL REGRESSION COCKPIT", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(top, text="Manual MesenCE visual verification bound to the exact current HD-pack fingerprint.").pack(anchor="w", pady=(2, 8))

        choose = ttk.Frame(self, padding=(12, 0)); choose.pack(fill="x")
        ttk.Button(choose, text="1. Select workspace", command=self.choose_workspace).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
        ttk.Label(choose, textvariable=self.workspace_var).grid(row=0, column=1, sticky="w")
        ttk.Button(choose, text="2. Select exact HD pack", command=self.choose_pack).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
        ttk.Label(choose, textvariable=self.pack_var).grid(row=1, column=1, sticky="w")

        actions = ttk.Frame(self, padding=12); actions.pack(fill="x")
        ttk.Button(actions, text="3. Refresh cockpit", command=self.refresh).pack(side="left", padx=3)
        ttk.Button(actions, text="4. Test NEXT case", command=self.test_next).pack(side="left", padx=3)
        ttk.Button(actions, text="Open dashboard", command=self.open_dashboard).pack(side="left", padx=3)
        ttk.Button(actions, text="Open workspace", command=self.open_workspace).pack(side="left", padx=3)

        current = ttk.LabelFrame(self, text="DO THIS NEXT", padding=12); current.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Label(current, textvariable=self.next_var, wraplength=980, font=("Segoe UI", 11, "bold")).pack(anchor="w")

        self.tree = ttk.Treeview(self, columns=("status", "case", "scope", "details"), show="headings", height=18)
        self.tree.heading("status", text="Status"); self.tree.column("status", width=90, anchor="center")
        self.tree.heading("case", text="Case"); self.tree.column("case", width=180)
        self.tree.heading("scope", text="What to verify in MesenCE"); self.tree.column("scope", width=470)
        self.tree.heading("details", text="Notes / failure"); self.tree.column("details", width=250)
        self.tree.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        foot = ttk.LabelFrame(self, text="Rules", padding=10); foot.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Label(foot, text="PASS only after real in-game verification. FAIL stays blocking until re-tested. Any PNG/hires.txt runtime change makes old PASS evidence STALE.", wraplength=980).pack(anchor="w")

    def choose_workspace(self) -> None:
        value = filedialog.askdirectory(title="Select local Project #002 workspace")
        if value:
            self.workspace = Path(value); self.workspace_var.set(str(self.workspace))

    def choose_pack(self) -> None:
        value = filedialog.askdirectory(title="Select exact HD pack to regression-test")
        if value:
            candidate = Path(value)
            if not (candidate / "hires.txt").is_file():
                messagebox.showerror("Invalid HD pack", "Selected folder does not contain hires.txt"); return
            self.pack = candidate; self.pack_var.set(str(self.pack))

    def _require(self) -> bool:
        if not self.workspace or not self.pack:
            messagebox.showinfo("Select inputs", "Select the local workspace and the exact HD pack first."); return False
        return True

    def refresh(self) -> None:
        if not self._require(): return
        manifest = self.workspace / "FINAL_REGRESSION.json"
        output = self.workspace / "Reports" / "FinalRegressionCockpit"
        try:
            self.status_data = build_and_write(manifest, self.pack, output)
        except Exception as exc:
            messagebox.showerror("Regression cockpit failed", str(exc)); return
        for item in self.tree.get_children(): self.tree.delete(item)
        for row in self.status_data["cases"]:
            details = row.get("notes") or ""
            if row["state"] == "FAIL":
                details = " · ".join(x for x in (row.get("failure_category"), row.get("failure_notes"), details) if x)
            self.tree.insert("", "end", values=(row["state"], row["key"], row["label"], details))
        counts = self.status_data["counts"]
        nxt = self.status_data.get("next_case")
        if nxt:
            self.next_var.set(f"{nxt['order']}. {nxt['label']} — current state {nxt['state']} | PASS {counts['PASS']}/{self.status_data['total']} · FAIL {counts['FAIL']} · STALE {counts['STALE']}")
        else:
            self.next_var.set(f"ALL {self.status_data['total']} CASES PASS for this exact build. Run Release Candidate Audit.")

    def test_next(self) -> None:
        if not self._require(): return
        self.refresh()
        if not self.status_data: return
        case = self.status_data.get("next_case")
        if case is None:
            messagebox.showinfo("Regression complete", "All regression cases PASS for this exact HD pack fingerprint."); return
        answer = messagebox.askyesnocancel(
            "Test NEXT case",
            f"Verify in MesenCE:\n\n{case['label']}\n\nDid this case PASS visually on the exact current HD pack?",
        )
        if answer is None: return
        notes = simpledialog.askstring("Test notes", "Optional notes:", parent=self) or ""
        kwargs = {}
        result = "PASS" if answer else "FAIL"
        if not answer:
            category = simpledialog.askstring(
                "Failure category",
                "Enter failure category:\n" + "\n".join(FAILURE_CATEGORIES),
                initialvalue="OTHER",
                parent=self,
            ) or "OTHER"
            category = category.strip().upper()
            if category not in FAILURE_CATEGORIES:
                messagebox.showerror("Unknown category", "Use one of: " + ", ".join(FAILURE_CATEGORIES)); return
            failure_notes = simpledialog.askstring("Failure details", "Describe the visible failure so the art/capture sprint can fix it:", parent=self) or ""
            kwargs = {"failure_category": category, "failure_notes": failure_notes}
        try:
            record_case_result(self.workspace / "FINAL_REGRESSION.json", case["key"], self.pack, result, notes=notes, **kwargs)
        except Exception as exc:
            messagebox.showerror("Could not record result", str(exc)); return
        self.refresh()

    def open_dashboard(self) -> None:
        if not self.status_data: self.refresh()
        if self.status_data:
            webbrowser.open(Path(self.status_data["outputs"]["dashboard"]).as_uri())

    def open_workspace(self) -> None:
        if not self.workspace: return
        try:
            if sys.platform.startswith("win"): subprocess.Popen(["explorer", str(self.workspace)])
            elif sys.platform == "darwin": subprocess.Popen(["open", str(self.workspace)])
            else: subprocess.Popen(["xdg-open", str(self.workspace)])
        except Exception as exc:
            messagebox.showerror("Open workspace failed", str(exc))


if __name__ == "__main__":
    RegressionCockpit().mainloop()
