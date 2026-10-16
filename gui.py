"""Simplified one-click GUI with robust error handling."""
import os
import sys
import traceback
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

import pandas as pd

from config import (APP_NAME, MONTH_NAMES,
                    ORDER_FIRST_APPEARANCE, ORDER_ALPHABETICAL)
from file_loader import load_excel
from column_mapper import (
    auto_detect_columns, load_saved_mapping, save_mapping, clear_saved_mapping
)
from attendance_normalizer import (
    normalize_dataframe, deduplicate, resolve_duplicates_by_priority
)
from calendar_processor import load_calendar
from data_validator import validate_month_class_filter, has_blocking_errors
from monthly_report import build_all_classes_data, summary_counts
from excel_formatter import write_monthly_report_all, write_normalized
from error_report import write_error_report
from utils import default_output_dir, open_file

NOTE_ZH = ("⚠ 学生名单由出勤记录自动生成；整月无记录的学生不会显示。"
           "同一天的 Present 会被请假类型（SL/CL/EL）自动覆盖。")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("880x680")
        self.minsize(780, 580)

        self.attendance_path = tk.StringVar()
        self.calendar_path   = tk.StringVar()
        self.year_var  = tk.StringVar(value=str(datetime.now().year))
        self.month_var = tk.StringVar(value=MONTH_NAMES[datetime.now().month])
        self.order_var = tk.StringVar(value=ORDER_FIRST_APPEARANCE)
        # ⭐ Writable default output path
        self.output_dir = tk.StringVar(value=str(default_output_dir()))

        self.raw_df = None
        self.norm_df = None
        self.column_mapping = {}
        self.errors = []
        self.warnings = []
        self.calendar = {}

        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg="#1976D2", height=50); hdr.pack(fill="x")
        tk.Label(hdr, text=APP_NAME, bg="#1976D2", fg="white",
                 font=("Helvetica", 14, "bold")).pack(side="left", padx=12, pady=10)

        note = tk.Frame(self, bg="#FFF3CD"); note.pack(fill="x")
        tk.Label(note, text=NOTE_ZH, bg="#FFF3CD", fg="#856404",
                 wraplength=840, justify="left", font=("Helvetica", 9)
                 ).pack(anchor="w", padx=8, pady=4)

        f1 = ttk.LabelFrame(self, text="📁 Input Files")
        f1.pack(fill="x", padx=8, pady=4)
        self._file_row(f1, "Attendance Excel:",           self.attendance_path, self._browse_attendance, 0)
        self._file_row(f1, "School Calendar (optional):", self.calendar_path, self._browse_calendar, 1)

        f2 = ttk.LabelFrame(self, text="⚙️ Report Parameters")
        f2.pack(fill="x", padx=8, pady=4)
        tk.Label(f2, text="Year:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Combobox(f2, textvariable=self.year_var, width=8,
                     values=[str(y) for y in range(2022, 2036)]
                     ).grid(row=0, column=1, sticky="w", padx=6, pady=6)
        tk.Label(f2, text="Month:").grid(row=0, column=2, sticky="w", padx=6, pady=6)
        ttk.Combobox(f2, textvariable=self.month_var, width=12,
                     values=MONTH_NAMES[1:], state="readonly"
                     ).grid(row=0, column=3, sticky="w", padx=6, pady=6)
        tk.Label(f2, text="Student Order:").grid(row=0, column=4, sticky="w", padx=6, pady=6)
        ttk.Combobox(f2, textvariable=self.order_var, width=20,
                     values=[ORDER_FIRST_APPEARANCE, ORDER_ALPHABETICAL],
                     state="readonly").grid(row=0, column=5, sticky="w", padx=6, pady=6)
        tk.Label(f2, text="Output Folder:").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        tk.Entry(f2, textvariable=self.output_dir
                 ).grid(row=1, column=1, columnspan=4, sticky="we", padx=6, pady=6)
        ttk.Button(f2, text="Browse...", command=self._browse_output
                   ).grid(row=1, column=5, sticky="w", padx=6, pady=6)
        for c in range(6):
            f2.grid_columnconfigure(c, weight=1 if c in (1, 3) else 0)

        f3 = tk.Frame(self); f3.pack(fill="x", padx=8, pady=12)
        tk.Button(f3, text="🚀  Generate Monthly Report",
                  command=self.generate_report,
                  font=("Helvetica", 13, "bold"),
                  bg="#1976D2", fg="white",
                  activebackground="#0D47A1", activeforeground="white",
                  padx=22, pady=12, cursor="hand2", borderwidth=0
                  ).pack(side="left", padx=4)
        ttk.Button(f3, text="📁 Open Output Folder",
                   command=self.open_output_folder).pack(side="left", padx=4)
        ttk.Button(f3, text="⚙️ Advanced",
                   command=self.show_advanced).pack(side="left", padx=4)
        ttk.Button(f3, text="Exit", command=self.destroy).pack(side="right", padx=4)

        f4 = ttk.LabelFrame(self, text="📋 Log")
        f4.pack(fill="both", expand=True, padx=8, pady=4)
        self.log = scrolledtext.ScrolledText(f4, height=14, font=("Menlo", 10))
        self.log.pack(fill="both", expand=True, padx=4, pady=4)
        self._log("Welcome. Select files above and click 🚀 Generate Monthly Report.")

    def _file_row(self, parent, label, var, cmd, row):
        tk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=4)
        tk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="we", padx=6, pady=4)
        ttk.Button(parent, text="Browse...", command=cmd
                   ).grid(row=row, column=2, sticky="w", padx=4, pady=4)
        ttk.Button(parent, text="Clear", command=lambda v=var: v.set("")
                   ).grid(row=row, column=3, sticky="w", padx=4, pady=4)
        parent.grid_columnconfigure(1, weight=1)

    def _browse_attendance(self):
        p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if p: self.attendance_path.set(p)
    def _browse_calendar(self):
        p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if p: self.calendar_path.set(p)
    def _browse_output(self):
        p = filedialog.askdirectory(initialdir=self.output_dir.get())
        if p: self.output_dir.set(p)
    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.insert("end", f"[{ts}] {msg}\n")
        self.log.see("end")
        self.update_idletasks()

    def open_output_folder(self):
        p = Path(self.output_dir.get())
        try:
            p.mkdir(parents=True, exist_ok=True)
            open_file(p)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open folder:\n{e}")

    def show_advanced(self):
        AdvancedDialog(self)

    # ═════════════════════════════════════════════════════════
    # 🚀 One-click pipeline  (ALL wrapped in try/except)
    # ═════════════════════════════════════════════════════════
    def generate_report(self):
        try:
            self._generate_report_impl()
        except Exception as e:
            tb = traceback.format_exc()
            self._log(f"❌ Unexpected error:\n{tb}")
            messagebox.showerror(
                "Unexpected Error",
                f"{type(e).__name__}: {e}\n\n"
                f"Please check the log for details. "
                f"If the problem persists, contact the developer.")

    def _generate_report_impl(self):
        # 1. Validate inputs
        path = self.attendance_path.get()
        if not path:
            messagebox.showerror("Error", "Please select the Attendance Excel first.")
            return
        try:
            year  = int(self.year_var.get())
            month = MONTH_NAMES.index(self.month_var.get())
        except Exception:
            messagebox.showerror("Error", "Invalid year or month."); return

        self._log("─" * 60)
        self._log(f"🔄 Processing: {Path(path).name}")

        # 2. Load Excel
        try:
            self.raw_df = load_excel(path)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot load Excel:\n{e}"); return
        self._log(f"   {len(self.raw_df)} raw records loaded")

        # 3. Auto-detect columns
        detected = auto_detect_columns(self.raw_df)
        saved = load_saved_mapping()
        for k, v in saved.items():
            if detected.get(k) is None and v and v in self.raw_df.columns:
                detected[k] = v

        if any(v is None for v in detected.values()):
            self._log("⚠ Column auto-detection incomplete — showing mapping dialog")
            dlg = ColumnMappingDialog(self, list(self.raw_df.columns), detected)
            self.wait_window(dlg)
            if not dlg.result:
                self._log("❌ Cancelled."); return
            detected = dlg.result

        self.column_mapping = detected
        save_mapping(detected)
        self._log(f"   Columns: {detected}")

        # 4. Normalize
        self.norm_df, self.errors = normalize_dataframe(self.raw_df, detected)
        self._log(f"   Normalized: {len(self.norm_df)} records "
                  f"({len(self.errors)} issues)")
        for e in self.errors[:3]:
            self._log(f"      ❌ Row {e.get('source_row')}: {e.get('message')}")
        if len(self.errors) > 3:
            self._log(f"      ... and {len(self.errors) - 3} more")

        if self.norm_df.empty:
            messagebox.showerror("Error",
                "No valid records could be normalized.\n\n"
                "Check the log for details, then try ⚙️ Advanced → Edit Column Mapping.")
            return

        # 5. Dedup + priority resolution
        self.norm_df = deduplicate(self.norm_df)
        self.norm_df, resolution_log = resolve_duplicates_by_priority(self.norm_df)
        if resolution_log:
            self._log(f"   🔄 Resolved {len(resolution_log)} status conflicts")

        # 6. Calendar
        if self.calendar_path.get():
            try:
                self.calendar, cerr = load_calendar(self.calendar_path.get())
                self._log(f"   📅 Calendar: {len(self.calendar)} dates ({len(cerr)} errors)")
                self.errors.extend(cerr)
            except Exception as e:
                self._log(f"   ⚠ Calendar load failed: {e}")
                self.calendar = {}
        else:
            self.calendar = {}
            self._log("   ⚠ No calendar — only weekends auto-recognized")

        # 7. Warnings
        self.warnings = validate_month_class_filter(
            self.norm_df, year, month, None)
        for w in self.warnings:
            self._log(f"   ⚠ {w['message']}")

        # 8. Output folder (make sure writable)
        try:
            out_dir = Path(self.output_dir.get())
            out_dir.mkdir(parents=True, exist_ok=True)
            # Writable test
            testf = out_dir / ".write_test"
            testf.write_text("x"); testf.unlink()
        except Exception as e:
            # Fallback to default
            fallback = default_output_dir()
            self._log(f"   ⚠ Cannot write to {self.output_dir.get()}: {e}")
            self._log(f"   → Using default output folder: {fallback}")
            self.output_dir.set(str(fallback))
            out_dir = fallback
            out_dir.mkdir(parents=True, exist_ok=True)

        month_name = MONTH_NAMES[month]

        # 9. Blocking errors
        if has_blocking_errors(self.errors):
            err_path = out_dir / f"Attendance_Errors_{month_name}_{year}.xlsx"
            write_error_report(err_path, self.errors, self.warnings)
            messagebox.showerror("Blocking Errors",
                f"Cannot generate report (blocking errors found).\n\n"
                f"Error report saved to:\n{err_path}")
            self._log(f"   ❌ Blocked — see {err_path.name}")
            return

        # 10. Build all-class data
        all_students, matrices, stats, day_info = build_all_classes_data(
            self.norm_df, year, month, self.calendar, self.order_var.get()
        )
        if not all_students:
            messagebox.showwarning("No Data",
                f"No students found in {month_name} {year}.\n"
                "Please verify your source file and the selected year/month.")
            return
        summary = summary_counts(day_info)

        # 11. Write the ONE Excel
        out_path = out_dir / f"Monthly_Attendance_{month_name}_{year}.xlsx"
        write_monthly_report_all(
            out_path, year, month,
            all_students, matrices, stats, day_info, summary
        )

        std_path = out_dir / f"Standardized_Attendance_{month_name}_{year}.xlsx"
        write_normalized(std_path, self.norm_df)
        if self.errors or self.warnings:
            err_path = out_dir / f"Attendance_Errors_{month_name}_{year}.xlsx"
            write_error_report(err_path, self.errors, self.warnings)

        classes_set = sorted(set(c for _, c in all_students))
        self._log("─" * 60)
        self._log(f"✅ DONE")
        self._log(f"   Students: {len(all_students)}  |  "
                  f"Classes: {len(classes_set)} ({', '.join(classes_set)})")
        self._log(f"   Output:   {out_path}")
        self._log("─" * 60)

        if messagebox.askyesno("✅ Success",
                f"Report generated!\n\n"
                f"• Students: {len(all_students)}\n"
                f"• Classes:  {len(classes_set)} ({', '.join(classes_set)})\n"
                f"• File:     {out_path.name}\n\n"
                f"Open it now?"):
            try: open_file(out_path)
            except Exception as e: messagebox.showerror("Error", str(e))


# ═══════════════════════════════════════════════════════════════════
#  Advanced
# ═══════════════════════════════════════════════════════════════════
class AdvancedDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("⚙️ Advanced Options")
        self.parent = parent
        self.resizable(False, False)
        self.lift(); self.focus_force()        # ⭐ force to front on Mac
        self.grab_set()

        tk.Label(self, text="Advanced tools",
                 font=("Helvetica", 12, "bold")).pack(padx=24, pady=(14, 8))
        tk.Label(self, text="Only needed if auto-detection goes wrong.",
                 font=("Helvetica", 9), fg="#666").pack(padx=24, pady=(0, 10))

        ttk.Button(self, text="🔧  Edit Column Mapping",
                   command=self._edit_mapping, width=36).pack(padx=24, pady=4)
        ttk.Button(self, text="👁  Preview Normalized Data",
                   command=self._preview, width=36).pack(padx=24, pady=4)
        ttk.Button(self, text="🧹  Reset Saved Settings",
                   command=self._reset, width=36).pack(padx=24, pady=4)

        ttk.Button(self, text="Close", command=self.destroy, width=18
                   ).pack(padx=24, pady=(16, 14))

    def _edit_mapping(self):
        if self.parent.raw_df is None:
            messagebox.showerror("Error", "Please click 🚀 Generate Monthly Report first.")
            return
        current = (dict(self.parent.column_mapping)
                   if self.parent.column_mapping
                   else auto_detect_columns(self.parent.raw_df))
        dlg = ColumnMappingDialog(self, list(self.parent.raw_df.columns), current)
        self.wait_window(dlg)
        if dlg.result:
            self.parent.column_mapping = dlg.result
            save_mapping(dlg.result)
            self.parent._log(f"🔧 Column mapping updated: {dlg.result}")
            self.parent.norm_df, self.parent.errors = normalize_dataframe(
                self.parent.raw_df, dlg.result)
            self.parent._log(f"   Re-normalized: {len(self.parent.norm_df)} records")
            messagebox.showinfo("Updated",
                "Column mapping updated.\nClick 🚀 Generate Monthly Report again.")

    def _preview(self):
        if self.parent.norm_df is None or self.parent.norm_df.empty:
            messagebox.showerror("Error", "No normalized data to preview.")
            return
        PreviewDialog(self, self.parent.norm_df)

    def _reset(self):
        if messagebox.askyesno("Reset Settings",
                "Clear the saved column mapping?"):
            clear_saved_mapping()
            self.parent._log("🧹 Saved settings cleared.")


# ═══════════════════════════════════════════════════════════════════
#  Column Mapping dialog
# ═══════════════════════════════════════════════════════════════════
class ColumnMappingDialog(tk.Toplevel):
    def __init__(self, parent, columns, detected):
        super().__init__(parent)
        self.title("Column Mapping")
        self.result = None
        self.resizable(False, False)
        # ⭐ Make dialog visible on Mac
        self.lift()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))
        self.focus_force()
        self.grab_set()

        tk.Label(self, text="Pick the correct column for each field.\n\n"
                             "⭐ Reminders for your form system:\n"
                             "   • Status  → 'Attendance' (NOT '状态')\n"
                             "   • Student → '子表单.Student' or '子表单'\n"
                             "   • Class   → '子表单.Class' or 'Class'\n"
                             "   • Date    → 'Record Date'",
                 justify="left", anchor="w"
                 ).grid(row=0, column=0, columnspan=2, padx=14, pady=10, sticky="w")

        self.vars = {}
        cols = [c for c in columns if c != "__source_row__"]
        choices = [""] + list(cols)
        fields = [("class",    "Class Column"),
                  ("status",   "Attendance Status Column"),
                  ("datetime", "Date Column (Record Date)"),
                  ("student",  "Student Column")]
        for i, (k, label) in enumerate(fields, start=1):
            tk.Label(self, text=label).grid(row=i, column=0, sticky="w", padx=14, pady=4)
            v = tk.StringVar(value=detected.get(k) or ""); self.vars[k] = v
            ttk.Combobox(self, textvariable=v, values=choices,
                         state="readonly", width=40
                         ).grid(row=i, column=1, padx=14, pady=4, sticky="w")

        f = tk.Frame(self); f.grid(row=99, column=0, columnspan=2, pady=14)
        ttk.Button(f, text="OK", command=self._ok, width=12).pack(side="left", padx=6)
        ttk.Button(f, text="Cancel", command=self.destroy, width=12).pack(side="left", padx=6)

    def _ok(self):
        res = {k: (v.get() or None) for k, v in self.vars.items()}
        if any(v is None for v in res.values()):
            messagebox.showerror("Error", "All four columns must be selected.")
            return
        self.result = res
        self.destroy()


# ═══════════════════════════════════════════════════════════════════
#  Preview dialog
# ═══════════════════════════════════════════════════════════════════
class PreviewDialog(tk.Toplevel):
    def __init__(self, parent, df):
        super().__init__(parent); self.title("Normalized Data Preview")
        self.geometry("1000x500"); self.df = df
        self.lift(); self.focus_force()
        tk.Label(self, text=f"Showing {min(len(df), 500)} of {len(df)} records"
                 ).pack(anchor="w", padx=8, pady=4)
        cols = ["Student Name", "Class", "Attendance Date", "Status",
                "Raw Status", "Submitted Time", "Source Row"]
        tv = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            tv.heading(c, text=c); tv.column(c, width=120, anchor="w")
        for _, row in df.head(500).iterrows():
            tv.insert("", "end", values=[str(row.get(c, "")) for c in cols])
        tv.pack(fill="both", expand=True, padx=8, pady=4)
        f = tk.Frame(self); f.pack(pady=6)
        ttk.Button(f, text="Save as Excel...", command=self._save).pack(side="left", padx=6)
        ttk.Button(f, text="Close", command=self.destroy).pack(side="left", padx=6)
    def _save(self):
        p = filedialog.asksaveasfilename(defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="Standardized_Attendance.xlsx")
        if p:
            try:
                write_normalized(p, self.df)
                messagebox.showinfo("Saved", f"Saved to {p}")
            except Exception as e:
                messagebox.showerror("Error", str(e))


def main():
    App().mainloop()