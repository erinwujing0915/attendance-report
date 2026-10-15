"""Load and query school calendar (new simplified format)."""
import pandas as pd
from datetime import date
from config import CALENDAR_TYPE_MAPPING
from utils import parse_date_value, safe_str

def load_calendar(path):
    """
    New simplified calendar format:
        | Date | Type | Name |

    Type (case-insensitive):
      - Holiday / Public Holiday / School Holiday  → H
      - Term Break / Half-Term Break               → H
      - Typhoon / Typhoon Closure                  → TC
      - Closure / School Closure                   → SC

    Backward compatible with old format
    (Event Type / Is School Day / Display Text columns).
    """
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
    date_col = cols.get("date") or list(df.columns)[0]
    type_col = cols.get("type") or cols.get("event type")
    name_col = (cols.get("name") or cols.get("display text")
                or cols.get("display") or cols.get("description"))
    isday_col = cols.get("is school day")  # legacy

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
        name  = safe_str(row.get(name_col)) if name_col else ""

        key = etype.lower().strip()
        if key in CALENDAR_TYPE_MAPPING:
            code = CALENDAR_TYPE_MAPPING[key]
            is_school = False
        elif not key:
            # No type given, assume generic holiday
            code = "H"; is_school = False
        else:
            # Unknown type, assume holiday
            code = "H"; is_school = False
            errors.append({"source_row": src_row, "type": "UnknownCalendarType",
                "student": "", "class": "", "date": str(d),
                "message": f"Unknown calendar Type: '{etype}' (treated as Holiday)",
                "details": "Supported: Holiday / Term Break / Typhoon / Closure"})

        # Legacy "Is School Day" column overrides
        if isday_col:
            v = safe_str(row.get(isday_col)).lower()
            if v in ("yes", "true", "1", "是"):
                is_school = True
            elif v in ("no", "false", "0", "否"):
                is_school = False

        display = name or etype or "Holiday"

        if d in cal:
            errors.append({"source_row": src_row, "type": "DuplicateCalendarDate",
                "student": "", "class": "", "date": str(d),
                "message": f"Date {d} appears multiple times in calendar",
                "details": ""})
            continue

        cal[d] = {
            "event_type":    etype,
            "code":          code,
            "is_school_day": is_school,
            "display":       display,
        }
    return cal, errors


def get_date_status(day: date, calendar: dict):
    """Returns (code, display, is_school_day)."""
    if day.weekday() >= 5:  # Saturday / Sunday
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