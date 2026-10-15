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

def write_monthly_report(output_path, year, month, selected_class,
                         students, matrix, day_info, stats, summary):
    wb = Workbook()
    ws = wb.active
    ws.title = f"{selected_class} {MONTH_NAMES[month]} {year}"[:31]

    ws.cell(row=1, column=1, value="Monthly Student Attendance Report").font = Font(size=14, bold=True)
    ws.cell(row=2, column=1, value=f"Month: {MONTH_NAMES[month]} {year}").font = Font(bold=True)
    ay = year if month >= 8 else year - 1
    ws.cell(row=2, column=4, value=f"Academic Year: {ay}-{ay+1}")
    ws.cell(row=2, column=7, value=f"Class: {selected_class}")
    ws.cell(row=3, column=1,
            value=f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ).font = Font(italic=True, size=9)

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
            if info:
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

    DATA_START = HDR2 + 1
    for idx, stu in enumerate(students):
        r = DATA_START + idx
        ws.cell(row=r, column=1, value=idx + 1).alignment = Alignment(horizontal="center")
        ws.cell(row=r, column=2, value=stu)
        ws.cell(row=r, column=3, value=selected_class).alignment = Alignment(horizontal="center")
        for i in range(len(STUDENT_INFO_FIELDS)):
            ws.cell(row=r, column=4 + i, value="")
        for i in range(len(left_cols)):
            ws.cell(row=r, column=i+1).border = THIN

        for di in day_info:
            col = DAY_START + di["day"] - 1
            data = matrix[stu][di["day"]]
            code = data["code"]
            c = ws.cell(row=r, column=col, value=code or "")
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = THIN
            info = STATUS_INFO.get(code)
            if info:
                c.fill = PatternFill("solid", fgColor=info["color"])
                c.font = Font(color=info["font_color"], size=10)

        st = stats[stu]
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

    legend_row = DATA_START + len(students) + 2
    ws.cell(row=legend_row, column=1, value="Legend:").font = Font(bold=True)
    col = 2
    for code, info in STATUS_INFO.items():
        c = ws.cell(row=legend_row, column=col, value=f"{code} = {info['label']}")
        c.fill = PatternFill("solid", fgColor=info["color"])
        c.font = Font(color=info["font_color"], size=9)
        c.border = THIN
        c.alignment = Alignment(horizontal="center")
        col += 1

    s_row = legend_row + 2
    ws.cell(row=s_row, column=1, value="Monthly Summary:").font = Font(bold=True)
    ws.cell(row=s_row+1, column=1, value=f"School Days: {summary['school_days']}")
    ws.cell(row=s_row+1, column=3, value=f"Weekends: {summary['weekends']}")
    ws.cell(row=s_row+1, column=5, value=f"Holidays: {summary['holidays']}")
    ws.cell(row=s_row+1, column=7, value=f"Typhoon Closures: {summary['typhoons']}")
    ws.cell(row=s_row+1, column=9, value=f"School Closures: {summary['closures']}")

    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 8
    for i in range(len(STUDENT_INFO_FIELDS)):
        ws.column_dimensions[get_column_letter(4 + i)].width = 14
    for di in day_info:
        ws.column_dimensions[get_column_letter(DAY_START + di["day"] - 1)].width = 4.5
    for i in range(len(stats_cols)):
        ws.column_dimensions[get_column_letter(STATS_START + i)].width = 11

    ws.row_dimensions[HDR1].height = 25
    ws.row_dimensions[HDR2].height = 55
    for idx in range(len(students)):
        ws.row_dimensions[DATA_START + idx].height = 20

    ws.freeze_panes = ws.cell(row=DATA_START, column=DAY_START)

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

def write_normalized(output_path, norm_df):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    out = norm_df.copy()
    if not out.empty:
        out["Attendance Date"] = out["Attendance Date"].astype(str)
        out["Submitted Time"]  = out["Submitted Time"].astype(str)
    out.to_excel(output_path, index=False)