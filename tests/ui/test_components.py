from __future__ import annotations

from control_center.components import metric_row


def test_metric_row_accepts_empty_input():
    metric_row([])
