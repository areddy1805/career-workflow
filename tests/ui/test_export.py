from __future__ import annotations

import pandas as pd

from control_center.export import dataframe_to_csv_bytes


def test_dataframe_to_csv_bytes_empty():
    assert dataframe_to_csv_bytes(pd.DataFrame()) == b""


def test_dataframe_to_csv_bytes_contains_headers_and_rows():
    frame = pd.DataFrame([
        {"title": "AI Engineer", "company": "Example"},
        {"title": "Applied AI Engineer", "company": "Example 2"},
    ])
    payload = dataframe_to_csv_bytes(frame)
    text = payload.decode("utf-8")
    assert "title,company" in text
    assert "AI Engineer,Example" in text
    assert "Applied AI Engineer,Example 2" in text
