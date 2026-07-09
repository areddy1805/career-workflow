from __future__ import annotations

import pandas as pd

from control_center import data


def test_application_summary_empty(monkeypatch):
    monkeypatch.setattr(data, "read_applications", lambda: pd.DataFrame())
    result = data.application_summary()
    assert result["total"] == 0
    assert result["interview"] == 0
    assert result["offer"] == 0


def test_application_summary_counts_lifecycle(monkeypatch):
    frame = pd.DataFrame({
        "lifecycle_stage": [
            "SUBMITTED", "VIEWED", "SHORTLISTED",
            "INTERVIEW", "REJECTED", "OFFER", None,
        ]
    })
    monkeypatch.setattr(data, "read_applications", lambda: frame)
    result = data.application_summary()
    assert result["total"] == 7
    assert result["submitted"] == 1
    assert result["viewed"] == 1
    assert result["shortlisted"] == 1
    assert result["interview"] == 1
    assert result["rejected"] == 1
    assert result["offer"] == 1


def test_lifecycle_distribution_preserves_order(monkeypatch):
    frame = pd.DataFrame({
        "lifecycle_stage": ["OFFER", "SUBMITTED", "SUBMITTED", None]
    })
    monkeypatch.setattr(data, "read_applications", lambda: frame)
    result = data.lifecycle_distribution()
    assert result["lifecycle_stage"].tolist() == list(data.LIFECYCLE_ORDER)
    submitted = result.loc[
        result["lifecycle_stage"] == "SUBMITTED", "count"
    ].iloc[0]
    assert submitted == 2
