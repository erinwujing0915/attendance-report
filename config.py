"""All constants centralized here."""

APP_NAME = "Monthly Student Attendance Report"
APP_VERSION = "1.0.0"

# ─────── Column auto-detection candidates ───────
CLASS_COLUMN_CANDIDATES = [
    "Class", "class", "CLASS", "班级", "班級",
    "子表单.Class", "Student Class", "StudentClass",
]
STATUS_COLUMN_CANDIDATES = [
    "Status", "status", "Attendance Status", "下拉选择框",
    "出勤状态", "出勤狀態", "Attendance Type", "Type",
]
DATETIME_COLUMN_CANDIDATES = [
    "Date Time", "DateTime", "日期时间", "日期時間",
    "Submitted Time", "Submission Date", "提交时间", "提交時間",
    "Created Time", "Created At", "Timestamp",
]
STUDENT_COLUMN_CANDIDATES = [
    "Student", "Student Name", "Name", "子表单.Student",
    "子表单.Name", "学生姓名", "學生姓名", "Students",
]

# ─────── Status mapping (raw text → standard code) ───────
STATUS_MAPPING = {
    "present": "P", "attended": "P", "on time": "P",
    "casual leave": "CL", "cl": "CL", "personal leave": "CL",
    "sick leave": "SL", "sl": "SL", "sick": "SL",
    "late": "L", "tardy": "L", "l": "L",
    "early leave": "EL", "el": "EL", "left early": "EL",
    "absent": "A", "a": "A",
    "holiday": "H", "h": "H", "school holiday": "H", "public holiday": "H",
    "typhoon closure": "TC", "tc": "TC", "typhoon": "TC",
    "school closure": "SC", "sc": "SC",
    "weekend": "WE", "we": "WE",
    "missing": "M", "missing record": "M",
    "出席": "P", "準時": "P", "准时": "P",
    "事假": "CL", "病假": "SL",
    "迟到": "L", "遲到": "L",
    "早退": "EL", "缺席": "A", "缺勤": "A",
    "放假": "H", "学校假期": "H", "學校假期": "H",
    "台风停课": "TC", "颱風停課": "TC",
    "學校停課": "SC", "学校停课": "SC",
}

# ─────── Status display ───────
STATUS_INFO = {
    "P":  {"label": "Present",         "color": "E8F5E9", "font_color": "000000"},
    "L":  {"label": "Late",            "color": "FFF59D", "font_color": "000000"},
    "EL": {"label": "Early Leave",     "color": "FFCC80", "font_color": "000000"},
    "CL": {"label": "Casual Leave",    "color": "BBDEFB", "font_color": "000000"},
    "SL": {"label": "Sick Leave",      "color": "90CAF9", "font_color": "000000"},
    "A":  {"label": "Absent",          "color": "EF9A9A", "font_color": "000000"},
    "H":  {"label": "Holiday",         "color": "A5D6A7", "font_color": "000000"},
    "TC": {"label": "Typhoon Closure", "color": "FFAB91", "font_color": "000000"},
    "SC": {"label": "School Closure",  "color": "FFAB91", "font_color": "000000"},
    "WE": {"label": "Weekend",         "color": "E0E0E0", "font_color": "666666"},
    "M":  {"label": "Missing Record",  "color": "CE93D8", "font_color": "000000"},
}

# ─────── Calendar event type → status code ───────
CALENDAR_EVENT_MAPPING = {
    "normal school day": None,
    "public holiday": "H", "school holiday": "H",
    "half-term break": "H", "term break": "H",
    "typhoon closure": "TC", "school closure": "SC",
    "examination day": None, "school activity": None,
    "weekend": "WE",
    "公众假期": "H", "公眾假期": "H",
    "学校假期": "H", "學校假期": "H",
    "台风停课": "TC", "颱風停課": "TC",
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