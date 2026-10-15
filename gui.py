"""Tkinter GUI."""
import os
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

import pandas as pd

from config import (APP_NAME, MONTH_NAMES, DEFAULT_OUTPUT_DIR,
                    ORDER_FIRST_APPEARANCE, ORDER_ALPHABETICAL)
from file_loader import load_excel
from column_mapper import auto_detect_columns, load_saved_mapping, save_mapping
from attendance_normalizer import normalize_dataframe, find_conflicts, deduplicate
from calendar_processor import load_calendar
from data_validator import validate_month_class_filter, has_blocking_errors
from monthly_report import extract_students, build_matrix, summary_counts
from excel_formatter import write_monthly_report, write_normalized
from error_report import write_error_report
from utils import app_dir, open_file

NOTE_EN = ("Student names are generated from the attendance records. "
           "Students with no attendance record during the selected month "
           "cannot be identified or included.")
NOTE_ZH = ("学生名单是根据原始出勤记录生成的。如需显示整班学生，"
           "包括整个月没有任何记录的学生，需要另外提供全班学生名单。")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("920x800")
        self.minsize(820, 720)

        self.attendance_path = tk.StringVar()
        self.calendar_path   = tk.StringVar()
        self.template_path   = tk.StringVar()
        self.year_var  = tk.StringVar(value=str(datetime.now().year))
        self.month_var = tk.StringVar(value=MONTH_NAMES[datetime.now().month])
        self.class_var = tk.StringVar()
        self.order_var = tk.StringVar(value=ORDER_FIRST_APPEARANCE)
        self.output_dir = tk.StringVar(value=str(app_dir() / DEFAULT_OUTPUT_DIR))

        self.raw_df = None; self.column_mapping = {}
        self.norm_df = None; self.errors = []; self.warnings = []
        self.calendar = {}
        self._build()

    def _build(self):
        pad = {"padx": 8, "pady": 4}
        hdr = tk.Frame(self, bg="#1976D2", height=50); hdr.pack(fill="x")
        tk.Label(hdr, text=APP_NAME, bg="#1976D2", fg="white",
                 font=("Helvetica", 14, "bold")).pack(side="left", padx=12, pady=10)

        note = tk.Frame(self, bg="#FFF3CD"); note.pack(fill="x")
        tk.Label(note, text="⚠ " + NOTE_EN, bg="#FFF3CD", fg="#856404",
                 wraplength=880, justify="left", font=("Helvetica", 9)
                 ).pack(anchor="w", padx=8, pady=4)
        tk.Label(note, text="⚠ " + NOTE_ZH, bg="#FFF3CD", fg="#856404",
                 wraplength=880, justify="left", font=("Helvetica", 9)
                 ).pack(anchor="w", padx=8, pady=2)

        f1 = ttk.LabelFrame(self, text="1. Input Files"); f1.pack(fill="x", **pad)
        self._file_row(f1, "Attendance Excel:",           self.attendance_path, self._browse_attendance, 0)
        self._file_row(f1, "School Calendar (Optional):", self.calendar_path, self._browse_calendar, 1)
        self._file_row(f1, "Excel Template (Optional):",  self.template_path, self._browse_template, 2)

        f2 = ttk.LabelFrame(self, text="2. Report Parameters"); f2.pack(fill="x", **pad)
        tk.Label(f2, text="Report Year:").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Combobox(f2, textvariable=self.year_var, width=10,
                     values=[str(y) for y in range(2022, 2036)]
                     ).grid(row=0, column=1, sticky="w", padx=6, pady=4)
        tk.Label(f2, text="Report Month:").grid(row=0, column=2, sticky="w", padx=6, pady=4)
        ttk.Combobox(f2, textvariable=self.month_var, width=12,
                     values=MONTH_NAMES[1:], state="readonly"
                     ).grid(row=0, column=3, sticky="w", padx=6, pady=4)
        tk.Label(f2, text="Class:").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        self.class_cb = ttk.Combobox(f2, textvariable=self.class_var, width=12,
                                     values=[], state="readonly")
        self.class_cb.grid(row=1, column=1, sticky="w", padx=6, pady=4)
        tk.Label(f2, text="Student Order:").grid(row=1, column=2, sticky="w", padx=6, pady=4)
        ttk.Combobox(f2, textvariable=self.order_var, width=22,
                     values=[ORDER_FIRST_APPEARANCE, ORDER_ALPHABETICAL],
                     state="readonly").grid(row=1, column=3, sticky="w", padx=6, pady=4)
        tk.Label(f2, text="Output Folder:").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        tk.Entry(f2, textvariable=self.output_dir, width=60
                 ).grid(row=2, column=1, columnspan=2, sticky="we", padx=6, pady=4)
        ttk.Button(f2, text="Browse...", command=self._browse_output
                   ).grid(row=2, column=3, sticky="w", padx=6, pady=4)

        f3 = ttk.LabelFrame(self, text="3. Actions"); f3.pack(fill="x", **pad)
        for text, cmd in [("Load Excel", self.load_excel),
                           ("Validate Data", self.validate_data),
                           ("Preview Normalized Data", self.preview_normalized),
                           ("Generate Monthly Report", self.generate_report),
                           ("Open Output Folder", self.open_output_folder)]:
            ttk.Button(f3, text=text, command=cmd).pack(side="left", padx=4, pady=6)
        ttk.Button(f3, text="Exit", command=self.destroy).pack(side="right", padx=4, pady=6)

        f4 = ttk.LabelFrame(self, text="4. Results / Log"); f4.pack(fill="both", expand=True, **pad)
        self.log = scrolledtext.ScrolledText(f4, height=16, font=("Menlo", 10))
        self.log.pack(fill="both", expand=True, padx=4, pady=4)
        self._log("Welcome. Please load an attendance Excel file to start.")

    def _file_row(self, parent, label, var, cmd, row):
        tk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=4)
        tk.Entry(parent, textvariable=var, width=70).grid(row=row, column=1, sticky="we", padx=6, pady=4)
        ttk.Button(parent, text="Browse...", command=cmd).grid(row=row, column=2, sticky="w", padx=4, pady=4)
        ttk.Button(parent, text="Clear",   command=lambda v=var: v.set("")
                   ).grid(row=row, column=3, sticky="w", padx=4, pady=4)
        parent.grid_columnconfigure(1, weight=1)

    def _browse_attendance(self):
        p = filedialog.askopenfilename(title="Select Attendance Excel",
            filetypes=[("Excel", "*.xlsx *.xls")])
        if p: self.attendance_path.set(p)
    def _browse_calendar(self):
        p = filedialog.askopenfilename(title="Select School Calendar Excel",
            filetypes=[("Excel", "*.xlsx *.xls")])
        if p: self.calendar_path.set(p)
    def _browse_template(self):
        p = filedialog.askopenfilename(title="Select Excel Template",
            filetypes=[("Excel", "*.xlsx")])
        if p: self.template_path.set(p)
    def _browse_output(self):
        p = filedialog.askdirectory(title="Select Output Folder")
        if p: self.output_dir.set(p)

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.insert("end", f"[{ts}] {msg}\n"); self.log.see("end")

    def load_excel(self):
        path = self.attendance_path.get()
        if not path:
            messagebox.showerror("Error", "Please select the Attendance Excel first."); return
        try:
            self._log(f"Loading: {path}")
            self.raw_df = load_excel(path)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot load Excel: {e}"); return

        detected = auto_detect_columns(self.raw_df)
        saved = load_saved_mapping()
        for k, v in saved.items():
            if v and v in self.raw_df.columns: detected[k] = v

        if any(v is None for v in detected.values()):
            dlg = ColumnMappingDialog(self, list(self.raw_df.columns), detected)
            self.wait_window(dlg)
            if not dlg.result:
                self._log("Column mapping cancelled."); return
            detected = dlg.result

        self.column_mapping = detected
        save_mapping(detected)
        self._log(f"Column mapping: {detected}")

        self.norm_df, self.errors = normalize_dataframe(self.raw_df, detected)
        self._log(f"Raw records: {len(self.raw_df)}, Normalized: {len(self.norm_df)}")
        self._log(f"Normalization errors: {len(self.errors)}")

        if not self.norm_df.empty:
            classes = sorted(self.norm_df["Class"].unique().tolist())
            self.class_cb["values"] = classes
            if classes and not self.class_var.get():
                self.class_var.set(classes[0])

            dates = pd.Series(self.norm_df["Attendance Date"].tolist())
            yrs = dates.apply(lambda d: d.year).mode()
            mts = dates.apply(lambda d: d.month).mode()
            if len(yrs) > 0: self.year_var.set(str(int(yrs.iloc[0])))
            if len(mts) > 0: self.month_var.set(MONTH_NAMES[int(mts.iloc[0])])

        if self.calendar_path.get():
            self.calendar, cerr = load_calendar(self.calendar_path.get())
            self._log(f"Loaded {len(self.calendar)} calendar dates. "
                      f"Calendar errors: {len(cerr)}")
            self.errors.extend(cerr)
        else:
            self.calendar = {}
            self._log("⚠ No School Calendar loaded. Only weekends will be "
                      "recognized as non-school days.")
        self._log("Load complete.")

    def validate_data(self):
        if self.norm_df is None:
            messagebox.showerror("Error", "Please load Excel first."); return
        before = len(self.norm_df)
        self.norm_df = deduplicate(self.norm_df)
        after = len(self.norm_df)
        self._log(f"Deduplication: {before} → {after}")
        conflicts = find_conflicts(self.norm_df)
        self.errors = [e for e in self.errors if e["type"] != "StatusConflict"] + conflicts
        self._log(f"Conflicts: {len(conflicts)}")

        try:
            year  = int(self.year_var.get())
            month = MONTH_NAMES.index(self.month_var.get())
        except Exception:
            messagebox.showerror("Error", "Invalid year/month."); return
        if not self.class_var.get():
            messagebox.showerror("Error", "Please select a class."); return

        self.warnings = validate_month_class_filter(
            self.norm_df, year, month, self.class_var.get())
        for w in self.warnings: self._log(f"WARNING: {w['message']}")

        students = extract_students(self.norm_df, year, month,
                                    self.class_var.get(), self.order_var.get())
        _, day_info, _ = build_matrix(self.norm_df, year, month,
                                      self.class_var.get(), students, self.calendar)
        summary = summary_counts(day_info)
        self._log("=" * 60)
        self._log(f"Students in {self.class_var.get()} / {self.month_var.get()} {year}: {len(students)}")
        self._log(f"School days: {summary['school_days']}, Weekends: {summary['weekends']}, "
                  f"Holidays: {summary['holidays']}, Typhoons: {summary['typhoons']}, "
                  f"Closures: {summary['closures']}")
        self._log(f"Errors: {len(self.errors)}, Warnings: {len(self.warnings)}")
        if has_blocking_errors(self.errors):
            self._log("⚠ Blocking errors found. Report generation will be prevented.")
        self._log("=" * 60)

    def preview_normalized(self):
        if self.norm_df is None or self.norm_df.empty:
            messagebox.showerror("Error", "No normalized data. Load Excel first."); return
        PreviewDialog(self, self.norm_df)

    def generate_report(self):
        if self.norm_df is None:
            messagebox.showerror("Error", "Please load Excel first."); return
        if not self.class_var.get():
            messagebox.showerror("Error", "Please select a class."); return
        try:
            year  = int(self.year_var.get())
            month = MONTH_NAMES.index(self.month_var.get())
        except Exception:
            messagebox.showerror("Error", "Invalid year or month."); return

        self.norm_df = deduplicate(self.norm_df)
        conflicts = find_conflicts(self.norm_df)
        base_errors = [e for e in self.errors if e["type"] != "StatusConflict"]
        all_errors = base_errors + conflicts
        self.warnings = validate_month_class_filter(
            self.norm_df, year, month, self.class_var.get())

        out_dir = Path(self.output_dir.get()); out_dir.mkdir(parents=True, exist_ok=True)
        month_name = MONTH_NAMES[month]

        if all_errors or self.warnings:
            err_path = out_dir / f"Attendance_Errors_{month_name}_{year}.xlsx"
            write_error_report(err_path, all_errors, self.warnings)
            self._log(f"Error report saved: {err_path}")

        std_path = out_dir / f"Standardized_Attendance_{month_name}_{year}.xlsx"
        write_normalized(std_path, self.norm_df)
        self._log(f"Standardized data saved: {std_path}")

        if has_blocking_errors(all_errors):
            messagebox.showwarning("Report Not Generated",
                "There are blocking errors. The monthly report was NOT generated.\n"
                f"Please check: {out_dir / f'Attendance_Errors_{month_name}_{year}.xlsx'}")
            return

        students = extract_students(self.norm_df, year, month,
                                    self.class_var.get(), self.order_var.get())
        if not students:
            messagebox.showwarning("No Students",
                f"No students found for {self.class_var.get()} in {month_name} {year}.")
            return

        matrix, day_info, stats = build_matrix(
            self.norm_df, year, month, self.class_var.get(), students, self.calendar)
        summary = summary_counts(day_info)

        out_path = out_dir / f"{self.class_var.get()}_Attendance_{month_name}_{year}.xlsx"
        try:
            write_monthly_report(out_path, year, month, self.class_var.get(),
                                 students, matrix, day_info, stats, summary)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot write report: {e}"); return

        self._log(f"✅ Report generated successfully: {out_path}")
        if messagebox.askyesno("Success",
                f"Report generated successfully.\n\n{out_path}\n\nOpen it now?"):
            try: open_file(out_path)
            except Exception as e: messagebox.showerror("Error", str(e))

    def open_output_folder(self):
        p = Path(self.output_dir.get()); p.mkdir(parents=True, exist_ok=True)
        try: open_file(p)
        except Exception as e: messagebox.showerror("Error", str(e))


class ColumnMappingDialog(tk.Toplevel):
    def __init__(self, parent, columns, detected):
        super().__init__(parent); self.title("Column Mapping"); self.result = None
        self.resizable(False, False); self.grab_set()
        tk.Label(self, text="Some columns could not be auto-detected.\n"
                             "Please select the correct column for each field.",
                 justify="left").grid(row=0, column=0, columnspan=2, padx=10, pady=8)
        self.vars = {}
        choices = [""] + list(columns)
        fields = [("class", "Class Column"), ("status", "Status Column"),
                  ("datetime", "Date/Time Column"), ("student", "Student Column")]
        for i, (k, label) in enumerate(fields, start=1):
            tk.Label(self, text=label).grid(row=i, column=0, sticky="w", padx=10, pady=4)
            v = tk.StringVar(value=detected.get(k) or ""); self.vars[k] = v
            ttk.Combobox(self, textvariable=v, values=choices, state="readonly", width=35
                         ).grid(row=i, column=1, padx=10, pady=4)
        f = tk.Frame(self); f.grid(row=99, column=0, columnspan=2, pady=10)
        ttk.Button(f, text="OK", command=self._ok).pack(side="left", padx=6)
        ttk.Button(f, text="Cancel", command=self.destroy).pack(side="left", padx=6)
    def _ok(self):
        res = {k: (v.get() or None) for k, v in self.vars.items()}
        if any(v is None for v in res.values()):
            messagebox.showerror("Error", "All columns must be selected."); return
        self.result = res; self.destroy()


class PreviewDialog(tk.Toplevel):
    def __init__(self, parent, df):
        super().__init__(parent); self.title("Normalized Data Preview")
        self.geometry("1000x500"); self.df = df
        tk.Label(self, text=f"Showing {min(len(df),500)} of {len(df)} records"
                 ).pack(anchor="w", padx=8, pady=4)
        cols = ["Student Name", "Class", "Attendance Date", "Status",
                "Raw Status", "Submitted Time", "Source Row"]
        tv = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols: tv.heading(c, text=c); tv.column(c, width=120, anchor="w")
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