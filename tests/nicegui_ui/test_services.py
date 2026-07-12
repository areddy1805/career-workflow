import pandas as pd

from career_ui_legacy.services.control_center import records, run_count


def test_records_normalizes_dataframe():
    assert records(pd.DataFrame([{"a": 1}])) == [{"a": 1}]


def test_run_count_reads_top_level_and_counts():
    assert run_count({"submitted": 3}, "submitted") == 3
    assert run_count({"counts": {"selected": 7}}, "selected") == 7
