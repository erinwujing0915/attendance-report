"""Helper utilities."""
import os, sys, re, platform, subprocess
from pathlib import Path
from datetime import datetime, date
import pandas as pd

def resource_path(relative_path: str) -> Path:
    try:
        base = Path(sys._MEIPASS)  # type: ignore
    except AttributeError:
        base = Path(__file__).parent
    return base / relative_path

def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent

def safe_str(v) -> str:
    if v is None: return ""
    if isinstance(v, float) and pd.isna(v): return ""
    return str(v).strip()

def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def parse_date_value(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, datetime): return v.date()
    if isinstance(v, date): return v
    s = str(v).strip()
    if not s: return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d",
                "%d/%m/%Y", "%m/%d/%Y"):
        try: return datetime.strptime(s, fmt).date()
        except ValueError: continue
    try: return pd.to_datetime(s).date()
    except Exception: return None

def parse_datetime_value(v):
    if v is None or (isinstance(v, float) and pd.isna(v)): return None
    if isinstance(v, datetime): return v
    if isinstance(v, date): return datetime.combine(v, datetime.min.time())
    try: return pd.to_datetime(str(v)).to_pydatetime()
    except Exception: return None

def days_in_month(year: int, month: int) -> int:
    import calendar
    return calendar.monthrange(year, month)[1]

def open_file(path):
    """Cross-platform file opener (Mac/Windows/Linux)."""
    path = str(path)
    system = platform.system()
    if system == "Windows":
        os.startfile(path)
    elif system == "Darwin":
        subprocess.call(["open", path])
    else:
        subprocess.call(["xdg-open", path])