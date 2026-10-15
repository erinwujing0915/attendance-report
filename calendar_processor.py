"""Load and query school calendar."""
import pandas as pd
from datetime import date
from config import CALENDAR_EVENT_MAPPING
from utils import parse_date_value, safe_str

def load_calendar(path):
    errors = []
    if not path: return {}, errors
    try:
        df = pd.read_excel(path, dtype=object)
    except Exception as e:
        errors.append({"source_row": 0, "type": "CalendarLoadError",
            "student": "", "class": "", "date": "",
            "message": f"Cannot load calendar file: {e}", "details": str(path)})
        return {}, errors

    cols = {str(c).lower().strip(): c for c in df.columns if isinstance(c, str)}
    date_col    = cols.get("date") or list(df.columns)[0]
    type_col    = cols.get("event type") or cols.get("type")
    isday_col   = cols.get("is school day")
    display_col = cols.get("display text")
    color_col   = cols.get("colour") or cols.get("color")

    cal = {}
    for i, row in df.iterrows():
        src_row = i + 2
        d = parse_date_value(row.get(date_col))
        if d is None:
            errors.append({"source_row": src_row, "type": "InvalidCalendarDate",
                "student": "", "class": "", "date": str(row.get(date_col)),
                "message": "Invalid date in school calendar", "details": ""})
            continue

        etype = safe_str(row.get(type_col)) if type_col else ""
        code  = CALENDAR_EVENT_MAPPING.get(etype.lower(), None)

        if isday_col:
            v = safe_str(row.get(isday_col)).lower()
            if v == "":
                is_school = code is None
            elif v in ("yes", "true", "1", "是"):
                is_school = True
            elif v in ("no", "false", "0", "否"):
                is_school = False
            else:
                is_school = code is None
        else:
            is_school = code is None

        display = safe_str(row.get(display_col)) if display_col else etype
        color   = safe_str(row.get(color_col)) if color_col else ""

        if d in cal:
            errors.append({"source_row": src_row, "type": "DuplicateCalendarDate",
                "student": "", "class": "", "date": str(d),
                "message": f"Date {d} appears multiple times in calendar",
                "details": ""})
            continue

        cal[d] = {
            "event_type":    etype, "code": code,
            "is_school_day": is_school, "display": display or etype,
            "color":         color,
        }
    return cal, errors

def get_date_status(day: date, calendar: dict):
    if day.weekday() >= 5:
        if day in calendar and calendar[day]["is_school_day"]:
            return (None, None, True)
        if day in calendar:
            info = calendar[day]
            return (info["code"] or "WE", info["display"] or "Weekend", False)
        return ("WE", "Weekend", False)
    if day in calendar:
        info = calendar[day]
        if not info["is_school_day"]:
            return (info["code"] or "H", info["display"], False)
    return (None, None, True)