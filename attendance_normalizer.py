"""Split multi-student rows and normalize data."""
import re
import pandas as pd
from config import STATUS_MAPPING, STUDENT_SPLIT_PATTERN
from utils import safe_str, normalize_whitespace, parse_date_value, parse_datetime_value

def split_cell(s: str):
    if not s: return []
    parts = re.split(STUDENT_SPLIT_PATTERN, s)
    return [normalize_whitespace(p) for p in parts if normalize_whitespace(p)]

def normalize_status(raw):
    s = safe_str(raw).lower()
    if not s: return (None, False)
    if s in STATUS_MAPPING: return (STATUS_MAPPING[s], True)
    key = re.sub(r"[^\w\s]", "", s).strip()
    if key in STATUS_MAPPING: return (STATUS_MAPPING[key], True)
    return (safe_str(raw), False)

def normalize_dataframe(df, mapping):
    class_col = mapping["class"]
    status_col = mapping["status"]
    dt_col = mapping["datetime"]
    stu_col = mapping["student"]

    records, errors = [], []
    for _, row in df.iterrows():
        src = int(row["__source_row__"])
        stu_raw = safe_str(row.get(stu_col, ""))
        cls_raw = safe_str(row.get(class_col, ""))
        sts_raw = safe_str(row.get(status_col, ""))
        dt_raw  = row.get(dt_col, None)

        students = split_cell(stu_raw)
        classes  = split_cell(cls_raw)

        if not students:
            errors.append({"source_row": src, "type": "EmptyStudent",
                "student": "", "class": cls_raw, "date": "",
                "message": "Student field is empty",
                "details": f"Status={sts_raw}, Class={cls_raw}"})
            continue

        if not classes:
            errors.append({"source_row": src, "type": "EmptyClass",
                "student": stu_raw, "class": "", "date": "",
                "message": "Class field is empty",
                "details": f"Students={stu_raw}"})
            continue
        elif len(classes) == 1:
            assigned_classes = classes * len(students)
        elif len(classes) == len(students):
            assigned_classes = classes
        else:
            errors.append({"source_row": src, "type": "StudentClassCountMismatch",
                "student": stu_raw, "class": cls_raw, "date": "",
                "message": (f"Student count ({len(students)}) does not match "
                            f"class count ({len(classes)})"),
                "details": f"Students={stu_raw} | Classes={cls_raw}"})
            continue

        attendance_date = parse_date_value(dt_raw)
        submitted_dt    = parse_datetime_value(dt_raw)
        if attendance_date is None:
            errors.append({"source_row": src, "type": "InvalidDate",
                "student": stu_raw, "class": cls_raw, "date": str(dt_raw),
                "message": "Date is empty or cannot be parsed",
                "details": f"Raw value: {dt_raw}"})
            continue

        code, is_known = normalize_status(sts_raw)
        if not sts_raw:
            errors.append({"source_row": src, "type": "EmptyStatus",
                "student": stu_raw, "class": cls_raw, "date": str(attendance_date),
                "message": "Status is empty", "details": ""})
            continue
        if not is_known:
            errors.append({"source_row": src, "type": "UnknownStatus",
                "student": stu_raw, "class": cls_raw, "date": str(attendance_date),
                "message": f"Unknown status: {sts_raw}",
                "details": f"Raw status: {sts_raw}"})
            continue

        for i, name in enumerate(students):
            records.append({
                "Student Name":    name,
                "Class":           assigned_classes[i].strip(),
                "Attendance Date": attendance_date,
                "Status":          code,
                "Raw Status":      sts_raw,
                "Submitted Time":  submitted_dt,
                "Source Row":      src,
            })

    norm_df = pd.DataFrame(records)
    return norm_df, errors

def find_conflicts(norm_df):
    conflicts = []
    if norm_df.empty: return conflicts
    grp = norm_df.groupby(["Student Name", "Class", "Attendance Date"])
    for (name, cls, dt), g in grp:
        statuses = sorted(g["Status"].unique().tolist())
        if len(statuses) > 1:
            rows = g["Source Row"].tolist()
            conflicts.append({
                "source_row": ",".join(map(str, rows)),
                "type":       "StatusConflict",
                "student":    name, "class": cls, "date": str(dt),
                "message":    f"Multiple different statuses on same day: {statuses}",
                "details":    f"Source rows: {rows}",
            })
    return conflicts

def deduplicate(norm_df):
    if norm_df.empty: return norm_df
    return norm_df.drop_duplicates(
        subset=["Student Name", "Class", "Attendance Date", "Status"]
    ).reset_index(drop=True)