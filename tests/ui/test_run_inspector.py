from __future__ import annotations

from pathlib import Path

import pytest

from control_center import run_inspector


def test_artifact_files_lists_nested_files(tmp_path):
    run_dir = tmp_path / "run-1"
    nested = run_dir / "nested"
    nested.mkdir(parents=True)
    (run_dir / "run.json").write_text("{}", encoding="utf-8")
    (nested / "notes.txt").write_text("hello", encoding="utf-8")

    rows = run_inspector.artifact_files(run_dir)
    paths = {row["relative_path"] for row in rows}

    assert "run.json" in paths
    assert "nested/notes.txt" in paths


def test_read_text_artifact_blocks_path_escape(tmp_path, monkeypatch):
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    monkeypatch.setattr(
        run_inspector,
        "_find_run",
        lambda run_id: run_dir,
    )

    with pytest.raises(ValueError):
        run_inspector.read_text_artifact("run-1", "../secret.txt")


def test_read_text_artifact_pretty_prints_json(tmp_path, monkeypatch):
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()
    (run_dir / "result.json").write_text(
        '{"status":"SUCCESS","submitted":3}',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        run_inspector,
        "_find_run",
        lambda run_id: run_dir,
    )

    content = run_inspector.read_text_artifact(
        "run-1",
        "result.json",
    )

    assert '"status": "SUCCESS"' in content
    assert '"submitted": 3' in content
