from __future__ import annotations

from control_center import manual_jobs


def test_manual_job_create_and_transition(tmp_path, monkeypatch):
    monkeypatch.setattr(manual_jobs, "MANUAL_JOBS_DB", tmp_path / "manual_jobs.db")
    job_id = manual_jobs.add_manual_job(
        title="AI Engineer",
        company="Example",
        location="Remote",
        source="LinkedIn",
        source_url="https://example.com/job",
        priority="TIER_A",
        notes="",
    )
    rows = manual_jobs.read_manual_jobs()
    assert len(rows) == 1
    assert rows.iloc[0]["status"] == "DISCOVERED"

    manual_jobs.update_manual_job_status(job_id, "APPLIED")
    rows = manual_jobs.read_manual_jobs()
    assert rows.iloc[0]["status"] == "APPLIED"
    assert rows.iloc[0]["applied_at"]
