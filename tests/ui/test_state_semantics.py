import json
from control_center import data, runner


def test_dead_ui_pid_becomes_orphaned(tmp_path, monkeypatch):
    state_path = tmp_path / "pipeline_state.json"
    exit_path = tmp_path / "pipeline_exit.json"
    state_path.write_text(json.dumps({"status": "RUNNING", "pid": 99999999}))
    monkeypatch.setattr(runner, "STATE_PATH", state_path)
    monkeypatch.setattr(runner, "EXIT_PATH", exit_path)
    monkeypatch.setattr(runner, "RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(runner, "process_is_running", lambda pid: False)
    assert runner.read_process_state()["status"] == "ORPHANED"


def test_terminal_result_wins(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    assert data._effective_run_status(run_dir, {"status": "RUNNING"}, {"status": "SUCCESS"}, newest=True) == "SUCCESS"


def test_old_running_artifact_is_orphaned(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    assert data._effective_run_status(run_dir, {"status": "RUNNING"}, {}, newest=False) == "ORPHANED"
