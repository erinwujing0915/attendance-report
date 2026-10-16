"""Auto-detect columns, remember user choices."""
import json
from config import (
    CLASS_COLUMN_CANDIDATES, STATUS_COLUMN_CANDIDATES,
    DATETIME_COLUMN_CANDIDATES, STUDENT_COLUMN_CANDIDATES,
    SETTINGS_FILE,
)
from utils import user_data_dir  # ⭐ writable location

STATUS_BLACKLIST = {"状态", "狀態", "record status", "record state"}


def _match(df_columns, candidates, blacklist=None):
    blacklist = {b.lower().strip() for b in (blacklist or set())}
    cols_lower = {c.lower().strip(): c for c in df_columns if isinstance(c, str)}

    for cand in candidates:
        if cand in df_columns and cand.lower().strip() not in blacklist:
            return cand
        key = cand.lower().strip()
        if key in cols_lower and key not in blacklist:
            return cols_lower[key]

    for col in df_columns:
        if not isinstance(col, str):
            continue
        cl = col.lower().strip()
        if cl in blacklist:
            continue
        for cand in candidates:
            ck = cand.lower().strip()
            if ck and (ck in cl or cl in ck):
                return col
    return None


def auto_detect_columns(df):
    cols = list(df.columns)
    return {
        "class":    _match(cols, CLASS_COLUMN_CANDIDATES),
        "status":   _match(cols, STATUS_COLUMN_CANDIDATES, blacklist=STATUS_BLACKLIST),
        "datetime": _match(cols, DATETIME_COLUMN_CANDIDATES),
        "student":  _match(cols, STUDENT_COLUMN_CANDIDATES),
    }


def _settings_path():
    return user_data_dir() / SETTINGS_FILE


def load_saved_mapping():
    p = _settings_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8")).get("column_mapping", {})
        except Exception:
            return {}
    return {}


def save_mapping(mapping):
    p = _settings_path()
    data = {}
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    data["column_mapping"] = mapping
    try:
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass  # non-critical


def clear_saved_mapping():
    p = _settings_path()
    if p.exists():
        try:
            p.unlink(); return True
        except Exception:
            return False
    return True