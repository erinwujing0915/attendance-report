"""All constants centralized here."""

APP_NAME = "Monthly Student Attendance Report"
APP_VERSION = "1.2.0"

# ─────── Column auto-detection candidates (ordered by priority) ───────
CLASS_COLUMN_CANDIDATES = [
    "子表单.Class", "子表單.Class",   # ⭐ sub-form (matches students 1-to-1)
    "Student Class", "StudentClass",
    "Class", "class", "CLASS",
    "班级", "班級",
]
STATUS_COLUMN_CANDIDATES = [
    "Attendance",                     # ⭐ real attendance status
    "Attendance Status", "Attendance Type",
    "出勤状态", "出勤狀態",
    "Status", "status",               # last-resort fallback
    "下拉选择框", "Type",
]
DATETIME_COLUMN_CANDIDATES = [
    "Record Date", "record date", "RecordDate",   # ⭐ true attendance date
    "Date Time", "DateTime", "日期时间", "日期時間",
    "Date",
    "Submitted Time", "Submission Date", "提交时间", "提交時間",
    "Created Time", "Created At", "Timestamp",
]
STUDENT_COLUMN_CANDIDATES = [
    "子表单.Student", "子表單.Student",   # ⭐ sub-form student (preferred)
    "子表单.Name",    "子表單.Name",
    "Student", "Student Name", "Name",
    "学生姓名", "學生姓名", "Students",
]

# ─────── Status mapping (raw text → standard code) ───────
STATUS_MAPPING = {
    "present": "P", "attended": "P", "on time": "P", "signed in": "P",
    "casual leave": "CL", "cl": "CL", "personal leave": "CL",
    "sick leave": "SL", "sl": "SL", "sick": "SL",
    "late": "L", "tardy": "L", "l": "L",
    "early leave": "EL", "el": "EL", "left early": "EL",
    "absent": "A", "a": "A",
    "holiday": "H", "h": "H",
    "typhoon closure": "TC", "tc": "TC",
    "school closure": "SC", "sc": "SC",
    "weekend": "WE", "we": "WE",
    "出席": "P", "準時": "P", "准时": "P", "签到": "P", "簽到": "P",
    "事假": "CL", "病假": "SL",
    "迟到": "L", "遲到": "L",
    "早退": "EL", "缺席": "A", "缺勤": "A",
}

# ─────── Status priority (higher wins when same day has multiple records) ───────
STATUS_PRIORITY = {
    "SL": 5, "CL": 4, "EL": 3, "L":  2, "P":  1, "A":  0, "M":  0,
}

# ─────── Status display info ───────
STATUS_INFO = {
    "P":  {"label": "Present",         "color": "C8E6C9", "font_color": "000000", "show_text": True},
    "L":  {"label": "Late",            "color": "FFF59D", "font_color": "000000", "show_text": True},
    "EL": {"label": "Early Leave",     "color": "FFCC80", "font_color": "000000", "show_text": True},
    "CL": {"label": "Casual Leave",    "color": "BBDEFB", "font_color": "000000", "show_text": True},
    "SL": {"label": "Sick Leave",      "color": "90CAF9", "font_color": "000000", "show_text": True},
    "H":  {"label": "Holiday",         "color": "A5D6A7", "font_color": "000000", "show_text": False},
    "TC": {"label": "Typhoon Closure", "color": "FFAB91", "font_color": "000000", "show_text": False},
    "SC": {"label": "School Closure",  "color": "EF9A9A", "font_color": "000000", "show_text": False},
    "WE": {"label": "Weekend",         "color": "E0E0E0", "font_color": "666666", "show_text": False},
    "A":  {"label": "Absent",          "color": None,     "font_color": "000000", "show_text": False},
    "M":  {"label": "Missing Record",  "color": None,     "font_color": "000000", "show_text": False},
}

# ─────── Simplified calendar event type → status code ───────
CALENDAR_TYPE_MAPPING = {
    "holiday": "H", "public holiday": "H", "school holiday": "H",
    "term break": "H", "half-term break": "H", "half term break": "H",
    "break": "H",
    "typhoon": "TC", "typhoon closure": "TC",
    "closure": "SC", "school closure": "SC",
    "假期": "H", "公众假期": "H", "公眾假期": "H",
    "学校假期": "H", "學校假期": "H",
    "学期假期": "H", "學期假期": "H",
    "台风": "TC", "颱風": "TC",
    "台风停课": "TC", "颱風停課": "TC",
    "停课": "SC", "停課": "SC",
}

# ─────── Statistics rules ───────
STATUSES_COUNTED_AS_PRESENT = {"P", "L", "EL"}
STATUSES_AS_SCHOOL_DAY       = {"P", "L", "EL", "CL", "SL", "A", "M"}
STATUSES_NON_SCHOOL          = {"H", "TC", "SC", "WE"}

ORDER_FIRST_APPEARANCE = "First Appearance Order"
ORDER_ALPHABETICAL     = "Alphabetical Order"

DEFAULT_OUTPUT_DIR    = "Output"
STUDENT_SPLIT_PATTERN = r"[,，]"
SETTINGS_FILE         = "settings.json"

MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]