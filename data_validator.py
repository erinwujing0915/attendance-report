"""Validate data."""

def validate_month_class_filter(norm_df, year, month, selected_class):
    warnings = []
    if norm_df.empty: return warnings
    others = norm_df[~((norm_df["Attendance Date"].apply(lambda d: d.year) == year) &
                       (norm_df["Attendance Date"].apply(lambda d: d.month) == month))]
    if not others.empty:
        warnings.append({"type": "OtherMonthData", "count": len(others),
            "message": f"Raw data contains {len(others)} records from other months. "
                       f"They will NOT be included in the report."})
    others_c = norm_df[norm_df["Class"] != selected_class]
    if not others_c.empty:
        warnings.append({"type": "OtherClassData", "count": len(others_c),
            "message": f"Raw data contains {len(others_c)} records from other classes. "
                       f"They will NOT be included in the {selected_class} report."})
    return warnings

def has_blocking_errors(errors):
    blocking = {"StudentClassCountMismatch", "StatusConflict", "DuplicateCalendarDate"}
    return any(e["type"] in blocking for e in errors)