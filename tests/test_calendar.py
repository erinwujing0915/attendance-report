import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from datetime import date
from calendar_processor import get_date_status

def test_weekend():
    code, _, is_sch = get_date_status(date(2026, 8, 1), {})
    assert code == "WE" and not is_sch

def test_holiday():
    cal = {date(2026, 8, 19): {"event_type":"Half-Term Break",
            "code":"H","is_school_day":False,"display":"Half-Term Break","color":""}}
    code, disp, is_sch = get_date_status(date(2026, 8, 19), cal)
    assert code == "H" and not is_sch

def test_normal_school_day():
    code, _, is_sch = get_date_status(date(2026, 8, 3), {})
    assert is_sch and code is None