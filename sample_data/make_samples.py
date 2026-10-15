"""Generate sample Excel files matching the user's real form export format."""
import pandas as pd
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

here = Path(__file__).parent
here.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════════════
#  Attendance sample — matches user's real export (merged header)
# ═══════════════════════════════════════════════════════════════════
wb = Workbook()
ws = wb.active
ws.title = "Attendance"

# Row 1: top-level headers (last 3 are merged under "子表单")
top_headers = ["状态", "流水号", "当前负责人", "Class", "Attendance", "Record Date",
               "子表单", None, None]
for col, h in enumerate(top_headers, 1):
    if h is not None:
        c = ws.cell(row=1, column=col, value=h)
        c.font = Font(bold=True)
        c.alignment = Alignment(horizontal="center")
# Merge the "子表单" header across 3 columns
ws.merge_cells(start_row=1, start_column=7, end_row=1, end_column=9)

# Row 2: sub-headers (only in sub-form columns)
sub_headers = {7: "子表单.Student", 8: "子表单.Name", 9: "子表单.Class"}
for col, h in sub_headers.items():
    c = ws.cell(row=2, column=col, value=h)
    c.font = Font(bold=True)
    c.alignment = Alignment(horizontal="center")

# Row 3+: data rows
#   Note the 10-15 row where Enzo has BOTH "Present" and "Early Leave" →
#   priority logic should keep "Early Leave"
data = [
    ("已生效", "202610150009", "", "4A", "Early Leave", "2026-10-15 14:37",
     "CHEUNG Sin Hang Enzo",
     "CHEUNG Sin Hang Enzo",
     "4A"),
    ("已生效", "202610150007", "", "4A", "Present", "2026-10-14 14:35",
     "CHEUNG Sin Hang Enzo,YAU Sze Wing Victoria,CHAN Chak Lam (Kalvin),CHU Lucas",
     "CHEUNG Sin Hang Enzo,YAU Sze Wing Victoria,CHAN Chak Lam (Kalvin),CHU Lucas",
     "4A,4A,4A,4A"),
    ("已生效", "202610150006", "", "4H(AM)", "Present", "2026-10-15 14:35",
     "KWUN Chak Him Hemera (Hemera),TSANG Lok Yan (Shanese),CHAM Nathaniel Lennon",
     "KWUN Chak Him Hemera (Hemera),TSANG Lok Yan (Shanese),CHAM Nathaniel Lennon",
     "4H(AM),4H(AM),4H(AM)"),
    ("已生效", "202610150005", "", "4A", "Present", "2026-10-15 14:34",
     "CHEUNG Sin Hang Enzo,YAU Sze Wing Victoria,CHAN Chak Lam (Kalvin),CHU Lucas",
     "CHEUNG Sin Hang Enzo,YAU Sze Wing Victoria,CHAN Chak Lam (Kalvin),CHU Lucas",
     "4A,4A,4A,4A"),
    # ── Extra test records ──
    ("已生效", "202610160001", "", "4A", "Sick Leave", "2026-10-16 09:00",
     "YAU Sze Wing Victoria", "YAU Sze Wing Victoria", "4A"),
    ("已生效", "202610160002", "", "4H(AM)", "Casual Leave", "2026-10-16 09:00",
     "TSANG Lok Yan (Shanese)", "TSANG Lok Yan (Shanese)", "4H(AM)"),
    ("已生效", "202610190001", "", "4A", "Late", "2026-10-19 09:45",
     "CHU Lucas", "CHU Lucas", "4A"),
]
for i, row in enumerate(data, start=3):
    for j, val in enumerate(row, start=1):
        ws.cell(row=i, column=j, value=val)

# Column widths
for col_letter, w in zip("ABCDEFGHI", (10, 15, 12, 10, 14, 20, 60, 60, 20)):
    ws.column_dimensions[col_letter].width = w

attendance_file = here / "attendance_sample.xlsx"
wb.save(attendance_file)
print(f"✅ Attendance sample (with merged 2-row header): {attendance_file}")

# ═══════════════════════════════════════════════════════════════════
#  Calendar sample — simplified 3-column format
# ═══════════════════════════════════════════════════════════════════
calendar = [
    ("2026-10-01", "Holiday",    "National Day"),
    ("2026-10-07", "Holiday",    "Mid-Autumn Festival"),
    ("2026-10-19", "Term Break", "Mid-Term Break (test override)"),
    ("2026-10-23", "Typhoon",    "T8 Signal"),
    ("2026-10-30", "Closure",    "Facility Maintenance"),
]
cal_file = here / "school_calendar_sample.xlsx"
pd.DataFrame(calendar, columns=["Date", "Type", "Name"]
             ).to_excel(cal_file, index=False)
print(f"✅ Calendar sample: {cal_file}")