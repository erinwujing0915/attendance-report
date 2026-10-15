"""Load Excel files with automatic two-row header detection."""
import pandas as pd
from pathlib import Path

SUBHEADER_PATTERNS = ("子表单.", "子表單.", "子表單 .", "子表单 .")

def load_excel(path: str, sheet_name=0) -> pd.DataFrame:
    """
    Smart loader:
      - Handles single-row header (standard).
      - Auto-detects two-row header where row 1 has a merged label
        (e.g. "子表单") and row 2 has sub-field names
        (e.g. "子表单.Student"). Promotes row 2 to column names.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        df = pd.read_excel(p, sheet_name=sheet_name, dtype=object, header=0)
    except Exception as e:
        raise RuntimeError(f"Cannot read Excel file: {e}")

    data_start_offset = 2

    if len(df) > 0:
        first_row = df.iloc[0].tolist()
        indicator_count = sum(
            1 for v in first_row
            if isinstance(v, str) and any(pat in v for pat in SUBHEADER_PATTERNS)
        )

        if indicator_count >= 1:
            # Promote this row to actual column names
            new_cols = []
            for col, val in zip(df.columns, first_row):
                if isinstance(val, str) and val.strip():
                    new_cols.append(val.strip())
                else:
                    new_cols.append(str(col).strip())

            # De-duplicate names
            seen = {}
            final_cols = []
            for name in new_cols:
                if name in seen:
                    seen[name] += 1
                    final_cols.append(f"{name}_{seen[name]}")
                else:
                    seen[name] = 0
                    final_cols.append(name)
            df.columns = final_cols

            df = df.iloc[1:].reset_index(drop=True)
            data_start_offset = 3

    df["__source_row__"] = range(data_start_offset, data_start_offset + len(df))
    return df


def list_sheet_names(path: str):
    try:
        return pd.ExcelFile(path).sheet_names
    except Exception:
        return []