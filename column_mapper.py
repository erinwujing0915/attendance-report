"""Auto-detect columns, remember user choices."""
import json
from config import (
    CLASS_COLUMN_CANDIDATES, STATUS_COLUMN_CANDIDATES,
    DATETIME_COLUMN_CANDIDATES, STUDENT_COLUMN_CANDIDATES,
    SETTINGS_FILE,
)
from utils import app_dir

def _match(df_columns, candidates):
    cols_lower = {c.lower().strip(): c for c in df_columns if isinstance(c, str)}
    for cand in candidates:
        if cand in df_columns: return cand
        if cand.lower() in cols_lower: return cols_lower[cand.lower()]
    for col in df_columns:
        if not isinstance(col, str): continue
        cl = col.lower().strip()
        for cand in candidates:
            if cand.lower() in cl or cl in cand.lower():
                return col
    return None

def auto_detect_columns(df):
    cols = list(df.columns)
    return {
        "class":    _match(cols, CLASS_COLUMN_CANDIDATES),
        "status":   _match(cols, STATUS_COLUMN_CANDIDATES),
        "datetime": _match(cols, DATETIME_COLUMN_CANDIDATES),
        "student":  _match(cols, STUDENT_COLUMN_CANDIDATES),
    }

def load_saved_mapping():
    p = app_dir() / SETTINGS_FILE
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8")).get("column_mapping", {})
        except Exception:
            return {}
    return {}

def save_mapping(mapping):
    p = app_dir() / SETTINGS_FILE
    data = {}
    if p.exists():
        try: data = json.loads(p.read_text(encoding="utf-8"))
        except Exception: data = {}
    data["column_mapping"] = mapping
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")