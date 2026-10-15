"""Build the monthly student×date matrix and statistics."""
from datetime import date
from config import (
    ORDER_FIRST_APPEARANCE, ORDER_ALPHABETICAL,
    STATUSES_COUNTED_AS_PRESENT, STATUSES_AS_SCHOOL_DAY,
)
from calendar_processor import get_date_status
from utils import days_in_month

def extract_students(norm_df, year, month, selected_class, order):
    if norm_df.empty: return []
    mask = ((norm_df["Class"] == selected_class) &
            (norm_df["Attendance Date"].apply(lambda d: d.year == year and d.month == month)))
    sub = norm_df[mask]
    if sub.empty: return []
    if order == ORDER_ALPHABETICAL:
        return sorted(sub["Student Name"].unique().tolist())
    seen, result = set(), []
    sub_sorted = sub.sort_values(["Submitted Time", "Source Row"], na_position="last")
    for name in sub_sorted["Student Name"]:
        if name not in seen:
            seen.add(name); result.append(name)
    return result

def build_matrix(norm_df, year, month, selected_class, students, calendar_dict):
    n_days = days_in_month(year, month)
    matrix = {s: {} for s in students}
    att_map = {}
    if not norm_df.empty:
        for _, r in norm_df.iterrows():
            if r["Class"] != selected_class: continue
            d = r["Attendance Date"]
            if d.year != year or d.month != month: continue
            att_map[(r["Student Name"], d)] = r["Status"]

    day_info = []
    for day in range(1, n_days + 1):
        d = date(year, month, day)
        wd = d.weekday()
        code, display, is_school = get_date_status(d, calendar_dict)
        day_info.append({
            "day": day, "date": d, "weekday": wd,
            "weekday_name": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][wd],
            "is_school_day": is_school,
            "code": code if code else ("" if is_school else "H"),
            "display": display or "",
        })
        for stu in students:
            if not is_school:
                matrix[stu][day] = {"code": code or "H", "display": display or ""}
            else:
                status = att_map.get((stu, d))
                matrix[stu][day] = {"code": status if status else "M", "display": ""}

    stats = {}
    for stu in students:
        cnt = {k:0 for k in ("P","L","EL","CL","SL","A","M","H","TC","SC","WE")}
        for day in range(1, n_days + 1):
            c = matrix[stu][day]["code"]
            if c in cnt: cnt[c] += 1
        attended = sum(cnt[c] for c in STATUSES_COUNTED_AS_PRESENT)
        denom    = sum(cnt[c] for c in STATUSES_AS_SCHOOL_DAY)
        rate     = (attended / denom) if denom else 0.0
        stats[stu] = {
            "Present":        cnt["P"],
            "Late":           cnt["L"],
            "Early Leave":    cnt["EL"],
            "Casual Leave":   cnt["CL"],
            "Sick Leave":     cnt["SL"],
            "Other Absence":  cnt["A"],
            "Missing Record": cnt["M"],
            "Attendance Rate": rate,
        }
    return matrix, day_info, stats

def summary_counts(day_info):
    return {
        "school_days": sum(1 for d in day_info if d["is_school_day"]),
        "weekends":    sum(1 for d in day_info if d["code"] == "WE"),
        "holidays":    sum(1 for d in day_info if d["code"] == "H"),
        "typhoons":    sum(1 for d in day_info if d["code"] == "TC"),
        "closures":    sum(1 for d in day_info if d["code"] == "SC"),
    }