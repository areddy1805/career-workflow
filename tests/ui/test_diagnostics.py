from __future__ import annotations

from control_center.diagnostics import health_summary, required_health_ok


def test_health_summary_counts_statuses():
    checks = [
        {"status": "PASS", "required": True},
        {"status": "PASS", "required": False},
        {"status": "WARN", "required": False},
        {"status": "FAIL", "required": True},
    ]
    result = health_summary(checks)
    assert result == {"pass": 2, "warn": 1, "fail": 1, "total": 4}


def test_required_health_ok_rejects_required_failure():
    checks = [
        {"status": "PASS", "required": True},
        {"status": "FAIL", "required": True},
    ]
    assert required_health_ok(checks) is False


def test_required_health_ok_allows_optional_failure():
    checks = [
        {"status": "PASS", "required": True},
        {"status": "FAIL", "required": False},
    ]
    assert required_health_ok(checks) is True
