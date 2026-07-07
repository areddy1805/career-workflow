from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

from application_report import build_report_snapshot
from apply_agent import (
    acquire_jobs,
    enrich_application_metadata,
    enrich_jobs_with_details,
    load_applied_jobs,
    print_acquisition_summary,
    print_pipeline_results,
    print_runtime_policy,
    run_application_batch,
)
from config.candidate_profile import CANDIDATE_PROFILE
from monitor_applications import reconcile_application_history
from src.application.adaptive_strategy import (
    AdaptiveStrategyConfig,
    build_adaptive_strategy,
    rank_candidates_adaptively,
    select_candidates_with_exploration,
    strategy_audit_payload,
)
from src.application.diversity import (
    DiversityPolicy,
    diversify_jobs,
)
from src.application.ledger import ApplicationLedger
from src.application.policy import ApplicationPolicy
from src.client.job_classifier import JobFilterPipeline2
from src.client.job_client import NaukriJobClient
from src.client.naukri_client import NaukriLoginClient
from src.llm.client import OMLXClient
from src.llm.question_resolver import LLMQuestionResolver
from src.orchestration.context import PipelineContext
from src.orchestration.result import PipelineResult
from src.orchestration.stages import (
    PIPELINE_STAGES,
    PipelineStatus,
    StageStatus,
)
from src.resolution.hybrid_resolver import HybridQuestionResolver
from src.search.challenge_cooldown import SearchChallengeCooldown
from src.search.job_search_cache import JobSearchCache

load_dotenv()


class CareerWorkflowPipeline:
    def __init__(
        self,
        *,
        dry_run: bool,
        max_applications: int,
        artifacts_root: str | Path = "artifacts/runs",
    ) -> None:
        if max_applications < 0:
            raise ValueError("max_applications must be greater than or equal to zero")

        self.context = PipelineContext(
            run_id=self._generate_run_id(),
            dry_run=dry_run,
            max_applications=max_applications,
        )

        self.artifacts_root = Path(
            artifacts_root,
        )

        self.run_dir = self.artifacts_root / self.context.run_id

        self.stage_statuses = {stage: StageStatus.PENDING for stage in PIPELINE_STAGES}

        self.status = PipelineStatus.RUNNING

    @staticmethod
    def _generate_run_id() -> str:
        return datetime.now(
            timezone.utc,
        ).strftime("%Y%m%dT%H%M%S%fZ")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def initialize_run(self) -> None:
        self.run_dir.mkdir(
            parents=True,
            exist_ok=False,
        )

        self._persist_state()

    def _persist_state(self) -> None:
        payload = {
            "run_id": self.context.run_id,
            "status": self.status.value,
            "dry_run": self.context.dry_run,
            "max_applications": (self.context.max_applications),
            "started_at": (self.context.started_at.isoformat()),
            "counts": {
                "acquired": len(self.context.acquired_jobs),
                "classified": len(self.context.classified_jobs),
                "selected": len(self.context.selected_jobs),
            },
            "stages": {
                name: status.value for name, status in self.stage_statuses.items()
            },
            "errors": self.context.errors,
        }

        target = self.run_dir / "run.json"

        temporary = self.run_dir / "run.json.tmp"

        temporary.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
            encoding="utf-8",
        )

        temporary.replace(
            target,
        )

    def _write_artifact(
        self,
        filename: str,
        payload,
    ) -> None:
        target = self.run_dir / filename

        temporary = target.with_suffix(target.suffix + ".tmp")

        temporary.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
            encoding="utf-8",
        )

        temporary.replace(
            target,
        )

    # ------------------------------------------------------------------
    # Stage execution
    # ------------------------------------------------------------------

    def _run_stage(
        self,
        name: str,
        function: Callable[[], None],
        *,
        fatal: bool,
    ) -> bool:
        self.stage_statuses[name] = StageStatus.RUNNING

        self._persist_state()

        print(f"\n[PIPELINE] {name.upper()} STARTED")

        try:
            function()

        except Exception as error:
            self.stage_statuses[name] = StageStatus.FAILED

            self.context.record_error(
                stage=name,
                error=error,
                fatal=fatal,
            )

            self.status = PipelineStatus.FAILED if fatal else PipelineStatus.PARTIAL

            self._persist_state()

            print(
                f"[PIPELINE] {name.upper()} FAILED: " f"{type(error).__name__}: {error}"
            )

            return False

        self.stage_statuses[name] = StageStatus.SUCCESS

        self._persist_state()

        print(f"[PIPELINE] {name.upper()} SUCCESS")

        return True

    # ------------------------------------------------------------------
    # Preflight
    # ------------------------------------------------------------------

    def preflight(self) -> None:
        username = os.getenv("NAUKRI_USERNAME")

        password = os.getenv("NAUKRI_PASSWORD")

        if not username:
            raise RuntimeError("NAUKRI_USERNAME environment variable is not set")

        if not password:
            raise RuntimeError("NAUKRI_PASSWORD environment variable is not set")

        ledger_path = os.getenv(
            "APPLICATION_LEDGER_PATH",
            "data/application_ledger.db",
        )

        Path(
            ledger_path,
        ).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.context.ledger = ApplicationLedger(
            ledger_path,
        )

        self.context.stage_results["preflight"] = {
            "credentials_present": True,
            "candidate_profile_loaded": bool(CANDIDATE_PROFILE),
            "ledger_path": ledger_path,
        }

    # ------------------------------------------------------------------
    # Acquisition
    # ------------------------------------------------------------------

    def acquire(self) -> None:
        username = os.environ["NAUKRI_USERNAME"]

        password = os.environ["NAUKRI_PASSWORD"]

        login_client = NaukriLoginClient(
            username,
            password,
        )

        login_client.login()

        job_client = NaukriJobClient(
            login_client,
        )

        job_cache = JobSearchCache(
            path=os.getenv(
                "JOB_SEARCH_CACHE_PATH",
                "data/job_search_cache.json",
            ),
            ttl_days=int(
                os.getenv(
                    "JOB_SEARCH_CACHE_TTL_DAYS",
                    "3",
                )
            ),
        )

        search_cooldown = SearchChallengeCooldown(
            path=os.getenv(
                "SEARCH_CHALLENGE_STATE_PATH",
                "data/search_challenge_state.json",
            ),
            cooldown_minutes=int(
                os.getenv(
                    "SEARCH_CHALLENGE_COOLDOWN_MINUTES",
                    "60",
                )
            ),
        )

        jobs, fetch_result = acquire_jobs(
            jc=job_client,
            cache=job_cache,
            cooldown=search_cooldown,
        )

        self.context.login_client = login_client

        self.context.job_client = job_client

        self.context.acquired_jobs = jobs

        self.context.fetch_result = fetch_result

        print_acquisition_summary(
            jobs=jobs,
            fetch_result=fetch_result,
        )

        self.context.stage_results["acquisition"] = {
            "jobs": len(jobs),
            "challenge_encountered": (fetch_result.challenge_encountered),
            "cooldown_suppressed": (fetch_result.search_skipped_due_to_cooldown),
            "search_requests_attempted": (fetch_result.search_requests_attempted),
        }

        self._write_artifact(
            "acquisition.json",
            self.context.stage_results["acquisition"],
        )

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def classify(self) -> None:
        if self.context.job_client is None:
            raise RuntimeError("Job client unavailable")

        classifier = JobFilterPipeline2()

        candidates = classifier.pre_filter(self.context.acquired_jobs)

        enriched_candidates = enrich_jobs_with_details(
            jc=self.context.job_client,
            jobs=candidates,
            detail_cache=(self.context.detail_cache),
        )

        final_jobs = classifier.score_and_select(enriched_candidates)

        for result in final_jobs:
            result["score"] = result.get(
                "ai_score",
                result.get(
                    "score",
                    0,
                ),
            )

            result["ai_detail"] = result.get(
                "ai_reason",
                result.get(
                    "ai_detail",
                    "",
                ),
            )

        final_jobs = enrich_application_metadata(final_jobs)

        self.context.classified_jobs = final_jobs

        self.context.score_map = {
            str(result["job_id"]): result for result in final_jobs
        }

        ledger = self.context.ledger

        for result in final_jobs:
            ledger.update_metadata(
                result["job_id"],
                score=result.get("score"),
                priority=str(result.get("priority") or ""),
                subtrack=str(result.get("subtrack") or ""),
            )

        print_pipeline_results(final_jobs)

        self.context.stage_results["classification"] = {
            "prefiltered": len(candidates),
            "classified": len(final_jobs),
        }

        self._write_artifact(
            "classification.json",
            {
                "summary": (self.context.stage_results["classification"]),
                "jobs": final_jobs,
            },
        )

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def _build_adaptive_strategy(
        self,
    ):
        ledger = self.context.ledger

        return build_adaptive_strategy(
            ledger.analytics_rows(),
            config=AdaptiveStrategyConfig(
                enabled=(
                    os.getenv(
                        "ADAPTIVE_STRATEGY_ENABLED",
                        "true",
                    )
                    .strip()
                    .lower()
                    in {
                        "1",
                        "true",
                        "yes",
                        "on",
                    }
                ),
                minimum_applications=int(
                    os.getenv(
                        "ADAPTIVE_MIN_APPLICATIONS",
                        "30",
                    )
                ),
                minimum_responses=int(
                    os.getenv(
                        "ADAPTIVE_MIN_RESPONSES",
                        "5",
                    )
                ),
                base_minimum_score=int(
                    os.getenv(
                        "MIN_APPLICATION_SCORE",
                        "68",
                    )
                ),
                base_max_applications_per_run=(self.context.max_applications),
                minimum_group_samples=int(
                    os.getenv(
                        "ADAPTIVE_MIN_GROUP_SAMPLES",
                        "5",
                    )
                ),
                exploration_fraction=float(
                    os.getenv(
                        "ADAPTIVE_EXPLORATION_FRACTION",
                        "0.20",
                    )
                ),
                prior_strength=float(
                    os.getenv(
                        "ADAPTIVE_PRIOR_STRENGTH",
                        "8.0",
                    )
                ),
                decay_half_life_days=float(
                    os.getenv(
                        "ADAPTIVE_DECAY_HALF_LIFE_DAYS",
                        "45.0",
                    )
                ),
                response_weight=float(
                    os.getenv(
                        "ADAPTIVE_RESPONSE_WEIGHT",
                        "1.0",
                    )
                ),
                outcome_weight=float(
                    os.getenv(
                        "ADAPTIVE_OUTCOME_WEIGHT",
                        "1.0",
                    )
                ),
            ),
        )

    def select(self) -> None:
        ledger = self.context.ledger

        self.context.applied_job_ids = load_applied_jobs() | ledger.applied_job_ids()

        strategy = self._build_adaptive_strategy()

        self.context.adaptive_strategy = strategy

        jobs_by_id = {str(job.job_id): job for job in self.context.acquired_jobs}

        ranked_jobs = [
            jobs_by_id[str(result["job_id"])]
            for result in self.context.classified_jobs
            if str(result["job_id"]) in jobs_by_id
        ]

        ranked_jobs = rank_candidates_adaptively(
            ranked_jobs,
            score_map=(self.context.score_map),
            strategy=strategy,
        )

        diversified_jobs = diversify_jobs(
            ranked_jobs,
            historical_company_counts=(ledger.company_application_counts()),
            policy=DiversityPolicy(
                max_per_company_per_run=int(
                    os.getenv(
                        "MAX_APPLICATIONS_PER_COMPANY_PER_RUN",
                        "2",
                    )
                ),
                max_per_role_family_per_company=int(
                    os.getenv(
                        "MAX_ROLE_FAMILY_PER_COMPANY",
                        "1",
                    )
                ),
            ),
        )

        selected_jobs = select_candidates_with_exploration(
            diversified_jobs,
            score_map=(self.context.score_map),
            strategy=strategy,
            limit=min(
                strategy.max_applications_per_run,
                self.context.max_applications,
            ),
        )

        self.context.selected_jobs = selected_jobs

        strategy_payload = strategy_audit_payload(strategy)

        self.context.stage_results["selection"] = {
            "classified": len(self.context.classified_jobs),
            "ranked": len(ranked_jobs),
            "diversified": len(diversified_jobs),
            "selected": len(selected_jobs),
            "strategy": strategy_payload,
        }

        self._write_artifact(
            "selection.json",
            self.context.stage_results["selection"],
        )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    def _build_questionnaire_resolver(
        self,
    ) -> HybridQuestionResolver:
        model = os.getenv(
            "QUESTIONNAIRE_LLM_MODEL",
            "qwen3.5-4b",
        )

        client = OMLXClient(
            model=model,
        )

        llm_resolver = LLMQuestionResolver(
            client=client,
        )

        return HybridQuestionResolver(
            llm_resolver=llm_resolver,
        )

    def apply(self) -> None:
        if not self.context.selected_jobs:
            self.context.stage_results["application"] = {
                "message": ("No selected jobs available"),
                "attempted": 0,
                "submitted": 0,
                "failed": 0,
            }

            self._write_artifact(
                "application.json",
                self.context.stage_results["application"],
            )

            return

        questionnaire_resolver = None

        if not self.context.dry_run:
            questionnaire_resolver = self._build_questionnaire_resolver()

        self.context.questionnaire_resolver = questionnaire_resolver

        effective_run_limit = min(
            self.context.adaptive_strategy.max_applications_per_run,
            self.context.max_applications,
        )

        policy = ApplicationPolicy(
            dry_run=self.context.dry_run,
            max_applications_per_run=effective_run_limit,
        )

        print_runtime_policy(policy)

        ledger = self.context.ledger

        ledger_run_id = ledger.start_run(dry_run=policy.dry_run)

        self.context.ledger_run_id = ledger_run_id

        ledger.record_strategy_decision(
            run_id=ledger_run_id,
            strategy=strategy_audit_payload(self.context.adaptive_strategy),
        )

        summary = run_application_batch(
            jc=self.context.job_client,
            jobs=self.context.selected_jobs,
            score_map=self.context.score_map,
            questionnaire_resolver=(questionnaire_resolver),
            applied_jobs_set=(self.context.applied_job_ids),
            policy=policy,
            detail_cache=(self.context.detail_cache),
            ledger=ledger,
        )

        self.context.application_summary = summary

        ledger.finish_run(
            ledger_run_id,
            fetched=len(self.context.acquired_jobs),
            qualified=summary.total_candidates,
            applied=summary.applied,
            already_applied=(summary.already_applied),
            failed=summary.failed,
        )

        attempted = (
            summary.applied
            + summary.already_applied
            + summary.skipped_external
            + summary.failed
        )

        self.context.stage_results["application"] = {
            "total_candidates": (summary.total_candidates),
            "attempted": attempted,
            "submitted": summary.applied,
            "already_applied": (summary.already_applied),
            "skipped_local": (summary.skipped_local),
            "skipped_external": (summary.skipped_external),
            "policy_rejected": (summary.policy_rejected),
            "dry_run_skipped": (summary.dry_run_skipped),
            "run_limit_reached": (summary.run_limit_reached),
            "failed": summary.failed,
        }

        self._write_artifact(
            "application.json",
            self.context.stage_results["application"],
        )

    # ------------------------------------------------------------------
    # Reconciliation
    # ------------------------------------------------------------------

    def reconcile(self) -> None:
        if self.context.login_client is None:
            raise RuntimeError("Authenticated login client unavailable")

        result = reconcile_application_history(
            client=(self.context.login_client),
            ledger=self.context.ledger,
        )

        self.context.server_history = result["history"]

        self.context.reconciliation_changes = result["changed"]

        self.context.stage_results["reconciliation"] = {
            "server_applications_fetched": (result["fetched"]),
            "new_or_changed_records": (result["changed"]),
        }

        self._write_artifact(
            "reconciliation.json",
            self.context.stage_results["reconciliation"],
        )

    # ------------------------------------------------------------------
    # Strategy refresh
    # ------------------------------------------------------------------

    def update_strategy(self) -> None:
        strategy = self._build_adaptive_strategy()

        self.context.updated_strategy = strategy

        payload = strategy_audit_payload(strategy)

        self.context.stage_results["strategy"] = payload

        self._write_artifact(
            "strategy.json",
            payload,
        )

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def report(self) -> None:
        rows = self.context.ledger.analytics_rows()

        snapshot = build_report_snapshot(rows)

        self.context.report_snapshot = snapshot

        self.context.stage_results["report"] = {
            "analytics_rows": len(rows),
            "artifact": "report.json",
        }

        self._write_artifact(
            "report.json",
            snapshot,
        )

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    def run(self) -> PipelineResult:
        self.initialize_run()

        execution_plan = (
            (
                "preflight",
                self.preflight,
                True,
            ),
            (
                "acquisition",
                self.acquire,
                True,
            ),
            (
                "classification",
                self.classify,
                True,
            ),
            (
                "selection",
                self.select,
                True,
            ),
            (
                "application",
                self.apply,
                False,
            ),
            (
                "reconciliation",
                self.reconcile,
                False,
            ),
            (
                "strategy",
                self.update_strategy,
                False,
            ),
            (
                "report",
                self.report,
                False,
            ),
        )

        for (
            name,
            function,
            fatal,
        ) in execution_plan:
            succeeded = self._run_stage(
                name,
                function,
                fatal=fatal,
            )

            if not succeeded and fatal:
                self._skip_remaining_pending_stages()
                break

        if self.status == PipelineStatus.RUNNING:
            self.status = PipelineStatus.SUCCESS

        self._persist_state()

        result = self._build_result()

        self._write_artifact(
            "result.json",
            result.to_dict(),
        )

        return result

    def _skip_remaining_pending_stages(
        self,
    ) -> None:
        for (
            name,
            status,
        ) in self.stage_statuses.items():
            if status == StageStatus.PENDING:
                self.stage_statuses[name] = StageStatus.SKIPPED

        self._persist_state()

    def _build_result(
        self,
    ) -> PipelineResult:
        completed_at = datetime.now(
            timezone.utc,
        )

        summary = self.context.application_summary

        if summary is None:
            attempted = 0
            submitted = 0
            failed = 0
        else:
            attempted = (
                summary.applied
                + summary.already_applied
                + summary.skipped_external
                + summary.failed
            )

            submitted = summary.applied
            failed = summary.failed

        return PipelineResult(
            run_id=self.context.run_id,
            status=self.status.value,
            acquired=len(self.context.acquired_jobs),
            classified=len(self.context.classified_jobs),
            selected=len(self.context.selected_jobs),
            attempted=attempted,
            submitted=submitted,
            failed=failed,
            manual_review=0,
            started_at=(self.context.started_at),
            completed_at=completed_at,
            stage_results={
                name: status.value for name, status in self.stage_statuses.items()
            },
            errors=self.context.errors,
        )
