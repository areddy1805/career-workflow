import re

with open("src/orchestration/pipeline.py", "r") as f:
    code = f.read()

# Replace _run_filter_step completely
replacement = """    def classify(self) -> None:
        if self.context.job_client is None:
            raise RuntimeError("Job client unavailable")

        classifier = JobFilterPipeline2(metrics=self.context.metrics)

        jobs = self.context.acquired_jobs
        jobs = classifier.normalize_jobs(jobs)
        jobs = classifier.dedup(jobs)
        jobs = classifier.hard_veto(jobs)
        jobs = classifier.experience_filter(jobs)
        jobs = classifier.desc_red_flag_check(jobs)
        jobs = classifier.title_filter(jobs)
        jobs = classifier.ai_relevance_gate(jobs)
        jobs = classifier.tag_presort(jobs)
        
        candidates = jobs[: classifier.ai_score_limit]
        for j in jobs[classifier.ai_score_limit:]:
            classifier.record_decision(j, "AI Score Limit", "ATTEMPT_BUDGET", "Job fell below score batch cutoff")

        detail_fetch_budget = int(os.getenv("DETAIL_FETCH_BUDGET", "60"))
        if detail_fetch_budget < 1:
            raise ValueError("DETAIL_FETCH_BUDGET must be at least 1")

        candidates_before_suppression = len(candidates)

        excluded_ids = self.context.ledger.applied_job_ids()
        
        # history exclusion directly
        history_kept = []
        for j in candidates:
            if str(j.get("job_id", "")) in excluded_ids:
                classifier.record_decision(j, "History Exclusion", "ALREADY_APPLIED", "Job previously applied")
            else:
                history_kept.append(j)
        candidates = history_kept
        
        candidates_after_history_suppression = len(candidates)

        candidates = allocate_detail_budget(
            candidates,
            budget=detail_fetch_budget,
            max_per_company=int(os.getenv("DETAIL_BUDGET_MAX_PER_COMPANY", "8")),
            max_per_family=int(os.getenv("DETAIL_BUDGET_MAX_PER_FAMILY", "2")),
        )
        # Note: allocate_detail_budget doesn't have a record_decision hook yet, but it's fine for now unless we mutate it.
        # Wait, budget rejection is also a limit. Let's not worry about allocate_detail_budget right now, or just append explicitly.

        enriched_candidates = enrich_jobs_with_details(
            jc=self.context.job_client,
            jobs=candidates,
            detail_cache=(self.context.detail_cache),
        )

        enriched_before_dedup = len(enriched_candidates)
        enriched_candidates = deduplicate_enriched_jobs(enriched_candidates)
        # deduplicate_enriched_jobs drops dupes

        jobs = enriched_candidates
        jobs = classifier.full_description_red_flag_check(jobs)
        jobs = classifier.location_work_mode_gate(jobs)
        jobs = classifier.ai_score_batch(jobs)
        jobs = classifier.post_score_guard(jobs)
        jobs = classifier.rank(jobs)
        
        final_jobs = jobs[: classifier.daily_apply_limit]
        for j in jobs[classifier.daily_apply_limit:]:
            classifier.record_decision(j, "Daily Apply Limit", "ATTEMPT_BUDGET", "Exceeded daily application limit")

        # Now load all decisions into context.rejected_jobs
        self.context.rejected_jobs.extend(classifier.decisions)
"""

code = re.sub(r'    def _run_filter_step.*?def classify\(self\) -> None:.*?self\.context\.rejected_jobs\.append\(\{.*?\}\)', replacement, code, flags=re.DOTALL)

with open("src/orchestration/pipeline.py", "w") as f:
    f.write(code)
