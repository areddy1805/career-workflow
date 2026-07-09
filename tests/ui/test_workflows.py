from __future__ import annotations

from control_center.workflows import WorkflowResult


def test_workflow_result_ok():
    assert WorkflowResult("x", 0, "done").ok is True
    assert WorkflowResult("x", 1, "failed").ok is False
