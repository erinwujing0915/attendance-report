"""Write formatted Excel reports."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from pathlib import Path
from datetime import datetime
from config import STATUS_INFO, MONTH_NAMES

THIN = Border(left=Side(style="thin", color="888888"),
              right=Side(style="thin", color="888888"),
              top=Side(style="thin", color="888888"),
              bottom=Side(style="thin", color="888888"))

STUDENT_INFO_FIELDS = [
    "Student Family Name", "Student Given Name(s)", "Student Preferred Name",
    "Chinese Name", "Date of Birth", "Gender",
    "The first day of school", "Date of Withdrawal", "Remarks",
]


def _display_text(code):
    return code if code in ("P", "L", "EL", "CL", "SL") else ""


def _apply_cell_style(cell, code):
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = THIN
    info = STATUS_INFO.get(code)
    if info and info["color"]:
        cell.fill = PatternFill("solid", fgColor=info["color"])
        cell.font = Font(color=info["font_color"], size=10,
                         bold=bool(info.get("show_text")))


# ─────────────────────────────────────────────────────────────────────
# ⭐ NEW: single sheet containing ALL classes
# ─────────────────────────────────────────────────────────────────────
def write_monthly_report_all(output_path, year, month,
                              all_students, matrices, stats,
                              day_info, summary):
    """
    all_students: list of (name, class) tuples
    matrices:     dict (name, class) -> {day: {code, display}}
    stats:        dict (name, class) -> stat_dict
    """
    wb = Workbook()
    ws = wb.active
    ws.title = f"All {MONTH_NAMES[month]} {year}"[:31]

    # Title / metadata rows
    ws.cell(row=1, column=1, value="Monthly Student Attendance Report (All Classes)"
            ).font = Font(size=14, bold=True)
    ws.cell(row=2, column=1, value=f"Month: {MONTH_NAMES[month]} {year}"
            ).font = Font(bold=True)
    ay = year if month >= 8 else year - 1
    ws.cell(row=2, column=4, value=f"Academic Year: {ay}-{ay+1}")
    classes_set = sorted(set(c for _, c in all_students))
    ws.cell(row=2, column=7,
            value=f"Classes: {', '.join(classes_set)}  |  Students: {len(all_students)}")
    ws.cell(row=3, column=1,
            value=f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ).font = Font(italic=True, size=9)

    # Header rows
    HDR1, HDR2 = 5, 6
    left_cols = ["No.", "Student Name", "Class"] + STUDENT_INFO_FIELDS
    for i, h in enumerate(left_cols, start=1):
        c = ws.cell(row=HDR1, column=i, value=h)
        c.font = Font(bold=True)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.fill = PatternFill("solid", fgColor="BBDEFB")
        c.border = THIN
        ws.merge_cells(start_row=HDR1, start_column=i, end_row=HDR2, end_column=i)

    DAY_START = len(left_cols) + 1
    for di in day_info:
        col = DAY_START + di["day"] - 1
        c1 = ws.cell(row=HDR1, column=col, value=di["day"])
        c1.font = Font(bold=True)
        c1.alignment = Alignment(horizontal="center", vertical="center")
        c1.border = THIN
        c2 = ws.cell(row=HDR2, column=col, value=di["weekday_name"])
        c2.font = Font(size=9)
        c2.alignment = Alignment(horizontal="center", vertical="center", text_rotation=90)
        c2.border = THIN
        if di["code"]:
            info = STATUS_INFO.get(di["code"])
            if info and info["color"]:
                fill = PatternFill("solid", fgColor=info["color"])
                c1.fill = fill; c2.fill = fill

    stats_cols = ["Present Days", "Late Days", "Early Leave Days",
                  "Casual Leave Days", "Sick Leave Days",
                  "Other Absence Days", "Missing Record Days", "Attendance Rate"]
    STATS_START = DAY_START + len(day_info)
    for i, s in enumerate(stats_cols):
        col = STATS_START + i
        c = ws.cell(row=HDR1, column=col, value=s)
        c.font = Font(bold=True)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.fill = PatternFill("solid", fgColor="FFE082")
        c.border = THIN
        ws.merge_cells(start_row=HDR1, start_column=col, end_row=HDR2, end_column=col)

    # Student data rows
    DATA_START = HDR2 + 1
    for idx, (stu, cls) in enumerate(all_students):
        r = DATA_START + idx

        ws.cell(row=r, column=1, value=idx + 1).alignment = Alignment(horizontal="center")
        ws.cell(row=r, column=2, value=stu)
        c3 = ws.cell(row=r, column=3, value=cls)
        c3.alignment = Alignment(horizontal="center")
        c3.font = Font(bold=True)
        c3.fill = PatternFill("solid", fgColor="E3F2FD")

        for i in range(len(STUDENT_INFO_FIELDS)):
            ws.cell(row=r, column=4 + i, value="")
        for i in range(len(left_cols)):
            ws.cell(row=r, column=i + 1).border = THIN

        mat = matrices[(stu, cls)]
        for di in day_info:
            col = DAY_START + di["day"] - 1
            data = mat[di["day"]]
            code = data["code"]
            c = ws.cell(row=r, column=col, value=_display_text(code))
            _apply_cell_style(c, code)

        st = stats[(stu, cls)]
        vals = [st["Present"], st["Late"], st["Early Leave"],
                st["Casual Leave"], st["Sick Leave"], st["Other Absence"],
                st["Missing Record"], st["Attendance Rate"]]
        for i, v in enumerate(vals):
            col = STATS_START + i
            c = ws.cell(row=r, column=col, value=v)
            c.alignment = Alignment(horizontal="center")
            c.border = THIN
            if i == len(vals) - 1:
                c.number_format = "0.00%"

    # Legend
    legend_row = DATA_START + len(all_students) + 2
    ws.cell(row=legend_row, column=1, value="Legend:").font = Font(bold=True)
    col = 2
    for code in ("P", "L", "EL", "CL", "SL", "H", "TC", "SC", "WE"):
        info = STATUS_INFO[code]
        text = f"{code} = {info['label']}" if info["show_text"] else f"■ {info['label']}"
        c = ws.cell(row=legend_row, column=col, value=text)
        if info["color"]:
            c.fill = PatternFill("solid", fgColor=info["color"])
        c.font = Font(color=info["font_color"], size=9)
        c.border = THIN
        c.alignment = Alignment(horizontal="center")
        col += 1
    c = ws.cell(row=legend_row, column=col, value="(blank) = No record")
    c.font = Font(size=9, italic=True)
    c.border = THIN
    c.alignment = Alignment(horizontal="center")

    # Summary
    s_row = legend_row + 2
    ws.cell(row=s_row, column=1, value="Monthly Summary:").font = Font(bold=True)
    ws.cell(row=s_row+1, column=1, value=f"School Days: {summary['school_days']}")
    ws.cell(row=s_row+1, column=3, value=f"Weekends: {summary['weekends']}")
    ws.cell(row=s_row+1, column=5, value=f"Holidays: {summary['holidays']}")
    ws.cell(row=s_row+1, column=7, value=f"Typhoon: {summary['typhoons']}")
    ws.cell(row=s_row+1, column=9, value=f"Closures: {summary['closures']}")
    ws.cell(row=s_row+2, column=1, value=f"Total Students: {len(all_students)}")
    ws.cell(row=s_row+2, column=3, value=f"Total Classes: {len(classes_set)}")

    # Column widths
    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 24
    ws.column_dimensions["C"].width = 10
    for i in range(len(STUDENT_INFO_FIELDS)):
        ws.column_dimensions[get_column_letter(4 + i)].width = 14
    for di in day_info:
        ws.column_dimensions[get_column_letter(DAY_START + di["day"] - 1)].width = 4.5
    for i in range(len(stats_cols)):
        ws.column_dimensions[get_column_letter(STATS_START + i)].width = 11

    # Row heights
    ws.row_dimensions[HDR1].height = 25
    ws.row_dimensions[HDR2].height = 55
    for idx in range(len(all_students)):
        ws.row_dimensions[DATA_START + idx].height = 20

    # Freeze header + first 3 left columns (so Class column stays visible)
    ws.freeze_panes = ws.cell(row=DATA_START, column=DAY_START)

    # ⭐ Auto-filter so user can filter by Class / Student Name
    if all_students:
        last_row = DATA_START + len(all_students) - 1
        last_col = get_column_letter(STATS_START + len(stats_cols) - 1)
        ws.auto_filter.ref = f"A{HDR1}:{last_col}{last_row}"

    # Page setup
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize   = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth  = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_margins.left = 0.3; ws.page_margins.right = 0.3
    ws.page_margins.top  = 0.5; ws.page_margins.bottom = 0.5
    ws.print_options.horizontalCentered = True

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)


# ─────────────────────────────────────────────────────────────────────
# (kept for backward compatibility — not used in current GUI)
# ─────────────────────────────────────────────────────────────────────
def write_monthly_report(output_path, year, month, selected_class,
                         students, matrix, day_info, stats, summary):
    """Legacy per-class writer. Still here in case you need it later."""
    all_students = [(s, selected_class) for s in students]
    matrices = {(s, selected_class): matrix[s] for s in students}
    stats_all = {(s, selected_class): stats[s] for s in students}
    write_monthly_report_all(output_path, year, month,
                              all_students, matrices, stats_all,
                              day_info, summary)


def write_normalized(output_path, norm_df):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    out = norm_df.copy()
    if not out.empty:
        out["Attendance Date"] = out["Attendance Date"].astype(str)
        out["Submitted Time"]  = out["Submitted Time"].astype(str)
    out.to_excel(output_path, index=False)