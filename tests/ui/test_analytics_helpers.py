from __future__ import annotations

import pandas as pd

from control_center.analytics_helpers import (
    average_time_to_first_response_hours,
    score_band_distribution,
    segment_funnel,
)


def test_score_band_distribution():
    frame = pd.DataFrame({"score": [20, 50, 65, 80, 95]})
    result = score_band_distribution(frame)
    assert result["count"].tolist() == [1, 1, 1, 1, 1]


def test_average_time_to_first_response_hours():
    frame = pd.DataFrame({
        "applied_at": ["2026-01-01T00:00:00Z"],
        "viewed_at": ["2026-01-02T00:00:00Z"],
        "shortlisted_at": [None],
    })
    assert average_time_to_first_response_hours(frame) == 24.0


def test_segment_funnel():
    frame = pd.DataFrame({
        "priority": ["A", "A", "B"],
        "lifecycle_stage": ["VIEWED", "OFFER", "SUBMITTED"],
    })
    result = segment_funnel(frame, "priority")
    row_a = result.loc[result["priority"].eq("A")].iloc[0]
    assert row_a["applications"] == 2
    assert row_a["response_rate"] == 100.0
    assert row_a["offer_rate"] == 50.0
