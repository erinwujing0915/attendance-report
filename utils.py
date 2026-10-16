"""Helper utilities."""
import os, sys, re, platform, subprocess
from pathlib import Path
from datetime import datetime, date
import pandas as pd


def resource_path(relative_path: str) -> Path:
    """Resolve path both in dev and PyInstaller frozen mode."""
    try:
        base = Path(sys._MEIPASS)  # type: ignore
    except AttributeError:
        base = Path(__file__).parent
    return base / relative_path


def app_dir() -> Path:
    """Directory where the executable/script lives (may be read-only on Mac)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def user_data_dir() -> Path:
    """
    ⭐ Writable directory for settings/cache. Always safe to write to.
      macOS:   ~/Library/Application Support/AttendanceReport/
      Windows: %LOCALAPPDATA%/AttendanceReport/
      Linux:   ~/.config/attendance-report/
    """
    system = platform.system()
    if system == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "AttendanceReport"
    elif system == "Windows":
        appdata = os.environ.get("LOCALAPPDATA")
        base = Path(appdata) / "AttendanceReport" if appdata \
               else Path.home() / "AppData" / "Local" / "AttendanceReport"
    else:
        base = Path.home() / ".config" / "attendance-report"
    base.mkdir(parents=True, exist_ok=True)
    return base


def default_output_dir() -> Path:
    """
    ⭐ Default output folder (writable). 
    Frozen app → ~/Documents/AttendanceReport/Output/
    Source     → ./Output/
    """
    if getattr(sys, "frozen", False):
        out = Path.home() / "Documents" / "AttendanceReport" / "Output"
    else:
        out = Path(__file__).parent / "Output"
    try:
        out.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return out


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
    """Cross-platform file opener."""
    path = str(path)
    system = platform.system()
    if system == "Windows":
        os.startfile(path)
    elif system == "Darwin":
        subprocess.call(["open", path])
    else:
        subprocess.call(["xdg-open", path])