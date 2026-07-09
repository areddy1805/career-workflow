from __future__ import annotations

import json

from control_center import runner


def test_unknown_dead_runtime_normalizes_to_idle(
    tmp_path,
    monkeypatch,
):
    state_path = tmp_path / "pipeline_state.json"
    exit_path = tmp_path / "pipeline_exit.json"

    state_path.write_text(
        json.dumps(
            {
                "status": "UNKNOWN",
                "pid": 99999999,
                "started_at": "2026-07-09T11:27:25+00:00",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        runner,
        "STATE_PATH",
        state_path,
    )

    monkeypatch.setattr(
        runner,
        "EXIT_PATH",
        exit_path,
    )

    monkeypatch.setattr(
        runner,
        "RUNTIME_DIR",
        tmp_path,
    )

    monkeypatch.setattr(
        runner,
        "process_is_running",
        lambda pid: False,
    )

    state = runner.read_process_state()

    assert state["status"] == "IDLE"
    assert state["pid"] is None


def test_running_dead_runtime_becomes_orphaned(
    tmp_path,
    monkeypatch,
):
    state_path = tmp_path / "pipeline_state.json"
    exit_path = tmp_path / "pipeline_exit.json"

    state_path.write_text(
        json.dumps(
            {
                "status": "RUNNING",
                "pid": 99999999,
                "started_at": "2026-07-09T11:27:25+00:00",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        runner,
        "STATE_PATH",
        state_path,
    )

    monkeypatch.setattr(
        runner,
        "EXIT_PATH",
        exit_path,
    )

    monkeypatch.setattr(
        runner,
        "RUNTIME_DIR",
        tmp_path,
    )

    monkeypatch.setattr(
        runner,
        "process_is_running",
        lambda pid: False,
    )

    state = runner.read_process_state()

    assert state["status"] == "ORPHANED"
