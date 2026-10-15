"""Error / warning report Excel."""
import pandas as pd
from pathlib import Path

def write_error_report(output_path, errors, warnings=None):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if errors:   data["Errors"]   = pd.DataFrame(errors)
    if warnings: data["Warnings"] = pd.DataFrame(warnings)
    if not data:
        data["Info"] = pd.DataFrame([{"message": "No errors or warnings"}])
    with pd.ExcelWriter(output_path, engine="openpyxl") as w:
        for sheet, df in data.items():
            df.to_excel(w, sheet_name=sheet, index=False)