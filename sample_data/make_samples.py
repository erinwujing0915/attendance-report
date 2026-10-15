"""Run once to generate sample Excel files."""
import pandas as pd
from pathlib import Path

Path(__file__).parent.mkdir(exist_ok=True)
here = Path(__file__).parent

attendance = [
    ("2PI", "Present",      "2026-08-03 09:00", "HUI Ka Chun"),
    ("2PI", "Present",      "2026-08-03 09:00", "LEUNG Charis,HUI Ting Him (Mack)"),
    ("2PI", "Casual Leave", "2026-08-04 09:00", "HUI Ka Chun"),
    ("2PI", "Late",         "2026-08-04 09:30", "LEUNG Charis"),
    ("2PI", "Sick Leave",   "2026-08-05 09:00", "HUI Ting Him (Mack)"),
    ("2PI", "Present",      "2026-08-05 09:00", "HUI Ka Chun,LEUNG Charis"),
    ("2PI", "Present",      "2026-08-06 09:00", "HUI Ka Chun,LEUNG Charis,HUI Ting Him (Mack)"),
    ("2P2", "Present",      "2026-08-03 09:05", "WONG Siu Ming"),
]
pd.DataFrame(attendance, columns=["Class","Status","Date Time","Student"]
             ).to_excel(here / "attendance_sample.xlsx", index=False)

calendar = [
    ("2026-08-19", "Half-Term Break", "No", "Half-Term Break", "Green"),
    ("2026-08-25", "Typhoon Closure", "No", "Typhoon Closure", "Red"),
    ("2026-08-31", "Public Holiday",  "No", "Public Holiday",  "Red"),
]
pd.DataFrame(calendar, columns=["Date","Event Type","Is School Day","Display Text","Colour"]
             ).to_excel(here / "school_calendar_sample.xlsx", index=False)

print(f"✅ Samples generated in {here}")