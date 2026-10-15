import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from attendance_normalizer import (
    normalize_dataframe, find_conflicts, deduplicate, split_cell
)

def _mk(rows):
    df = pd.DataFrame(rows, columns=["Class","Status","Date Time","Student"])
    df["__source_row__"] = range(2, len(df) + 2)
    return df

MAP = {"class":"Class","status":"Status","datetime":"Date Time","student":"Student"}

def test_single_student():
    df = _mk([("2PI","Present","2026-10-15 09:00","HUI Ka Chun")])
    n, err = normalize_dataframe(df, MAP)
    assert len(n) == 1 and not err
    assert n.iloc[0]["Student Name"] == "HUI Ka Chun"
    assert n.iloc[0]["Status"] == "P"

def test_multi_student_single_class():
    df = _mk([("2PI","Present","2026-10-15 09:00",
               "LEUNG Charis,HUI Ting Him (Mack)")])
    n, err = normalize_dataframe(df, MAP)
    assert len(n) == 2 and not err
    assert set(n["Student Name"]) == {"LEUNG Charis", "HUI Ting Him (Mack)"}

def test_count_mismatch_is_error():
    df = pd.DataFrame([{
        "Class":"2PI,2PI,2PI", "Status":"Present",
        "Date Time":"2026-10-15 09:00",
        "Student":"LEUNG Charis,HUI Ting Him (Mack)"
    }])
    df["__source_row__"] = [2]
    n, err = normalize_dataframe(df, MAP)
    assert len(n) == 0
    assert any(e["type"] == "StudentClassCountMismatch" for e in err)

def test_status_conflict():
    df = _mk([
        ("2PI","Present","2026-10-15 09:00","HUI Ka Chun"),
        ("2PI","Casual Leave","2026-10-15 10:00","HUI Ka Chun"),
    ])
    n, _ = normalize_dataframe(df, MAP)
    n = deduplicate(n)
    conflicts = find_conflicts(n)
    assert len(conflicts) == 1

def test_split_preserves_parentheses():
    assert split_cell("HUI Ting Him (Mack)") == ["HUI Ting Him (Mack)"]

def test_chinese_comma():
    assert split_cell("张三，李四") == ["张三","李四"]