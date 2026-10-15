"""Load Excel files, preserving source row numbers."""
import pandas as pd
from pathlib import Path

def load_excel(path: str, sheet_name=0) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    try:
        df = pd.read_excel(p, sheet_name=sheet_name, dtype=object)
    except Exception as e:
        raise RuntimeError(f"Cannot read Excel file: {e}")
    df["__source_row__"] = range(2, len(df) + 2)
    return df

def list_sheet_names(path: str):
    try:
        return pd.ExcelFile(path).sheet_names
    except Exception:
        return []