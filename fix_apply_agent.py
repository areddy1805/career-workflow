import re

with open("apply_agent.py", "r") as f:
    code = f.read()

# Update signature
code = code.replace(
    "    metrics: PipelineRunMetrics | None = None,\n) -> ApplicationRunSummary:",
    "    metrics: PipelineRunMetrics | None = None,\n    rejected_jobs: list | None = None,\n) -> ApplicationRunSummary:"
)

# Helper function
helper = """    rejected_jobs_list = rejected_jobs if rejected_jobs is not None else []
    def _record_app_reject(job, code, reason):
        from datetime import datetime, timezone
        rejected_jobs_list.append({
            "job_id": str(getattr(job, "job_id", "")),
            "title": str(getattr(job, "title", "Unknown")),
            "company": str(getattr(job, "company", "Unknown")),
            "stage": "Application",
            "code": code,
            "reason": str(reason),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
"""
code = code.replace("    total_candidates = len(jobs)\n", "    total_candidates = len(jobs)\n" + helper)

def inject(target, append):
    global code
    code = code.replace(target, target + "\n" + append)

# 1. Local idempotency
inject("            skipped_local_count += 1", "            _record_app_reject(job, 'ALREADY_APPLIED', 'Job previously applied (local check)')")

# 2. Static policy
inject("            policy_rejected_count += 1", "            _record_app_reject(job, policy_evaluation.reason.value, policy_evaluation.detail)")

# 3. Run limit (per-run successful submission limit)
# We need to append ALL remaining jobs.
run_limit_block = """        if (
            effective_policy.max_applications_per_run is not None
            and successful_submissions >= effective_policy.max_applications_per_run
        ):
            run_limit_reached_count = total_candidates - index + 1
            logger.info(
                "Per-run successful submission limit reached. "
                "Leaving %s queued candidate(s) for a later run.",
                run_limit_reached_count,
            )
            for remaining_job in jobs[index - 1:]:
                _record_app_reject(remaining_job, 'APPLICATION_QUOTA', 'Per-run successful submission limit reached')
            break"""
code = re.sub(r'        if \(\n\s*effective_policy\.max_applications_per_run is not None\n.*?break', run_limit_block, code, flags=re.DOTALL)

# 5. External application
inject("                skipped_external_count += 1", "                _record_app_reject(job, 'EXTERNAL_REJECTION', 'Job requires applying on external portal')")

# 7. Already applied server
inject("                already_applied_count += 1", "                _record_app_reject(job, 'ALREADY_APPLIED', 'Server reports job already applied')")

# 8. Manual review
inject("            manual_review_count += 1", "            _record_app_reject(job, 'MANUAL_REVIEW', str(exc))")

with open("apply_agent.py", "w") as f:
    f.write(code)
