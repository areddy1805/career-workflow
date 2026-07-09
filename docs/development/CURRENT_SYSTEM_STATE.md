# Career Workflow Current System State

Status: Phase 0 baseline validated and ready for freeze.

Audit date: 2026-07-09.

This document records implemented repository state only. The PRD defines target direction and is not evidence that planned functionality exists.

## 1. Baseline Validation Status

Career Workflow 1.0 is a working local-first Naukri job-search and application system with acquisition, classification, scoring, selection, application execution, questionnaire resolution, persistence, lifecycle reconciliation, analytics, adaptive strategy, and staged orchestration.

Phase 0 corrected two baseline blockers:

1. `apply_agent.py` failed during import because `print_acquisition_summary()` referenced `JobFetchResult` before its definition. The module now uses postponed annotation evaluation.
2. `tests/llm/test_omlx_client.py` performed live oMLX network activity during module import. It now uses deterministic tests and does not require a running inference server during pytest collection.

Validated exit state:

- `apply_agent.py` imports successfully;
- `CareerWorkflowPipeline` imports successfully;
- pytest collection completes;
- focused subsystem tests pass;
- full regression suite passes;
- Python source compilation passes when AppleDouble `._*` metadata files are excluded;
- staged pipeline dry-run passes;
- working tree is clean after committed validation changes.

The baseline can be frozen after this document is committed and the final freeze audit passes on the resulting `main` commit.

## 2. Repository Structure

Primary top-level runtime files:

- `run_pipeline.py` — staged orchestration CLI.
- `apply_agent.py` — legacy monolithic application-cycle CLI and shared implementation module.
- `monitor_applications.py` — server-history reconciliation and lifecycle reporting.
- `application_report.py` — analytics and adaptive-strategy reporting.
- `requirements.txt` — Python dependencies.
- `.env.example` — partial environment template.

Primary packages:

- `config/` — candidate profile and candidate evidence.
- `src/application/` — policy, execution outcomes, failure handling, ledger, lifecycle, analytics, diversity, eligibility, adaptive strategy, response interpretation, and manual queue.
- `src/client/` — Naukri authentication, session, search, detail, application, questionnaire, chatbot, and history behavior.
- `src/llm/` — local OpenAI-compatible oMLX client and questionnaire LLM resolver.
- `src/models/` — current source-oriented dataclasses.
- `src/orchestration/` — staged pipeline, context, result, and stage definitions.
- `src/resolution/` — hybrid questionnaire resolution.
- `src/search/` — search cache, cache codec, and challenge cooldown.
- `src/utils/` — deterministic questionnaire resolver, telemetry, nkparam support, request helpers, and legacy nkparam SQLite storage.
- `tests/` — application, client, LLM, orchestration, resolution, and search tests.
- `tools/` — collection, scoring, inspection, evaluation, diagnostics, and maintenance utilities.
- `docs/` — product, architecture, development, and archived documentation.
- `artifacts/` — orchestration artifact root.

No API package or UI implementation exists.

## 3. Runtime Entry Points

### 3.1 Primary staged pipeline

`run_pipeline.py:main()` constructs `src.orchestration.pipeline.CareerWorkflowPipeline`.

CLI behavior:

- dry-run by default;
- `--live` enables live application execution;
- `--max-applications` limits application attempts;
- `--confirm-live APPLY_LIVE` confirms live execution;
- `--canary` limits a live run to at most one application.

Live execution is blocked unless command-line or environment confirmation equals `APPLY_LIVE`.

### 3.2 Legacy application cycle

`apply_agent.py:main()` calls `run_application_cycle()`.

This remains an independent end-to-end path and duplicates substantial behavior now represented in `CareerWorkflowPipeline`. It remains a compatibility surface until the staged path fully replaces it.

### 3.3 Monitoring

`monitor_applications.py:main()`:

- authenticates to Naukri;
- fetches application history;
- parses server history;
- reconciles history into SQLite;
- prints local status summaries;
- prints lifecycle summaries;
- reports stale applications;
- prints funnel breakdowns.

### 3.4 Reporting

`application_report.py:main()` reads `ApplicationLedger.analytics_rows()` and reports:

- funnel overview;
- adaptive strategy state;
- priority breakdown;
- subtrack breakdown;
- score-band breakdown;
- company breakdown;
- age distribution;
- application velocity;
- response-time summary.

### 3.5 Tools

Operational and diagnostic scripts exist under `tools/`, including collection, analysis, scoring, questionnaire inspection, scoring inspection, unknown-response inspection, LLM resolver evaluation, ledger metadata backfill, and source diagnostics.

These are not the primary staged pipeline.

## 4. Staged Orchestration

`src/orchestration/pipeline.py:CareerWorkflowPipeline` implements eight ordered stages:

1. `preflight`;
2. `acquisition`;
3. `classification`;
4. `selection`;
5. `application`;
6. `reconciliation`;
7. `strategy`;
8. `report`.

`src/orchestration/stages.py` defines stage and pipeline statuses.

The pipeline supports:

- UTC run IDs;
- per-run artifact directories;
- atomic JSON writes through temporary-file replacement;
- stage-level status;
- structured error capture;
- fatal and non-fatal stages;
- partial-run semantics;
- final structured `PipelineResult`.

Fatal stages are preflight, acquisition, classification, and selection.

Application, reconciliation, strategy, and report are non-fatal. Failure in one of these stages can produce a partial pipeline result.

## 5. Execution Flow

The validated primary flow is:

`run_pipeline.py:main()`
→ `CareerWorkflowPipeline.run()`
→ preflight
→ acquisition
→ classification
→ selection
→ application
→ reconciliation
→ strategy
→ report
→ final result artifact.

Preflight validates required credentials and initializes the application ledger.

Acquisition authenticates to Naukri, creates the job client, search cache, and challenge cooldown state, then calls the acquisition functions currently implemented in `apply_agent.py`.

Classification performs cheap filtering before detail fetching and expensive LLM scoring.

Selection suppresses previously applied jobs, builds adaptive strategy when evidence thresholds permit, annotates eligibility, applies diversity ordering, calculates attempt and scan budgets, and selects exploitation and exploration candidates.

Application execution records qualified jobs, enforces local duplicate suppression and policy, routes external applications to the manual queue, applies directly where supported, resolves questionnaires, stores raw responses, and records outcomes.

Reconciliation fetches Naukri application history and updates the ledger using monotonic lifecycle rules.

Strategy rebuilds adaptive strategy from reconciled analytics rows.

Report builds and writes the analytics snapshot.

## 6. Acquisition Behavior

The active acquisition implementation is in `apply_agent.py`.

`fetch_all_jobs()` defines 21 AI-oriented search tracks covering Generative AI, AI Engineer, AI/ML, Machine Learning, LLM, RAG, Agentic AI, GenAI Developer, AI Developer, AI Application Developer, NLP, Prompt Engineering, Computer Vision, Deep Learning, Data Science AI, MLOps AI, Full Stack AI, Python AI, Azure OpenAI, and LangChain.

Each acquired job receives search-track, search-query, and acquisition-source metadata.

Search breadth is configurable through:

- `SEARCH_EXPERIENCE_LEVELS`;
- `SEARCH_MAX_PAGES`;
- `SEARCH_RESULTS_PER_PAGE`;
- `SEARCH_JOB_AGE_DAYS`.

Implemented acquisition behavior includes:

- multiple search tracks;
- multiple experience buckets;
- pagination;
- job-ID deduplication;
- repeated-page detection;
- empty-page termination;
- partial-page termination;
- inter-request delay;
- challenge interruption with partial-result preservation.

`NaukriSearchChallengeError` terminates further search requests while preserving already collected jobs.

`SearchChallengeCooldown` persists challenge state in JSON. During active cooldown, live search is suppressed and fresh cache is used.

## 7. Search Cache

`JobSearchCache` stores versioned JSON.

Current schema version: 2.

Readable versions: 1 and 2.

Each entry stores:

- `cached_at`;
- serialized `Job`.

Freshness is TTL-based.

Acquisition resolution rules:

- normal completion: live results and cache refresh;
- partial challenge: merge live results with fresh cache;
- immediate challenge: fresh cache;
- active cooldown: fresh cache.

Current acquisition provenance values:

- `live`;
- `cache`;
- `live+cache`.

## 8. Current Job Representation

`src/models/models.py:Job` is the active source-oriented dataclass.

Fields:

- `job_id`;
- `title`;
- `company`;
- `location`;
- `experience`;
- `salary`;
- `posted_date`;
- `apply_link`;
- `description`;
- `tags`.

Runtime attributes such as `search_track`, `search_query`, `acquisition_source`, and `_cached_at` are attached dynamically.

This is not a canonical multi-source job model.

The classifier converts `Job` objects to dictionaries. Later orchestration maps selected dictionaries back to original `Job` objects by `job_id`.

## 9. Classification Behavior

`src/client/job_classifier.py:JobFilterPipeline2` is the active classifier.

`pre_filter()` performs:

1. normalization;
2. job-ID deduplication;
3. hard title veto;
4. search-description red-flag filtering;
5. software/AI title filtering;
6. AI relevance gating;
7. stack-overlap and recency presort;
8. candidate limiting before expensive scoring.

Experience filtering exists but is deliberately disabled in the active path.

Company veto support exists but is disabled and the active veto-company set is empty.

Primary-stack conflict filtering exists as a compatibility hook but currently returns all jobs unchanged.

Hard title veto fragments include walk-in variants, tutor, trainer, sales executive, business development executive, recruiter, and talent acquisition.

Search snippets and enriched full descriptions are checked for walk-in language, venue/interview-location language, and resume-carry instructions.

The full-description red-flag check is repeated after detail enrichment.

## 10. AI Relevance and Location Policy

The AI relevance gate retains a job when at least one condition is met:

- explicit AI title signal;
- at least one strong AI signal;
- at least two medium AI signals.

The classifier stores:

- `ai_relevance`;
- `ai_relevance_reason`;
- `ai_signal_count`.

Generic software overlap alone is insufficient.

`location_work_mode_gate()` classifies:

- `remote`;
- `hybrid`;
- `office`;
- `unknown`.

Eligibility behavior:

- remote: eligible regardless of location;
- office: Pune evidence required;
- hybrid: Pune evidence required;
- unknown: Pune evidence required.

Pune detection includes Pune, Pimpri, Chinchwad, and Hinjawadi spelling variants.

The PRD remote-scope taxonomy is not implemented.

## 11. Detail Enrichment and Deduplication

`apply_agent.py:enrich_jobs_with_details()` fetches Naukri detail payloads and enriches classifier dictionaries with:

- full description;
- richer location;
- work mode;
- `is_external_apply`.

Detail-fetch failures retain the candidate and mark `detail_enrichment_failed`.

`src/application/diversity.py:allocate_detail_budget()` allocates detail budget using company round-robin ordering and role-family shaping, then backfills from overflow.

`deduplicate_enriched_jobs()` suppresses exact normalized-description duplicates and fallback vacancy-fingerprint duplicates when descriptions are unavailable.

## 12. Scoring Behavior

`JobFilterPipeline2.ai_score_batch()` uses an OpenAI-compatible chat-completions endpoint configured through:

- `OMLX_BASE_URL`;
- `OMLX_API_KEY`;
- `OMLX_MODEL`.

Scoring is batched.

The implementation:

- reads persistent score cache;
- scores uncached jobs;
- validates returned job IDs and integer scores;
- retries missing or malformed batch results individually;
- assigns zero when individual retry also fails;
- writes successful normalized results to cache.

The model score is bounded by deterministic evidence calibration in `_calibrate_score()`.

`post_score_guard()`:

- rejects incidental VBA automation roles;
- rejects non-engineering content roles;
- caps weak incidental-AI jobs;
- applies floors for strong applied-AI evidence;
- keeps explicit AI engineering titles at or above the classifier minimum apply score.

Final ranking uses AI score, AI signal count, and recency.

Score is a ranking signal, not the broad-coverage eligibility gate.

## 13. Application Metadata and Selection

`apply_agent.py:enrich_application_metadata()` attaches `subtrack` and `priority`.

Current subtracks:

- `AGENTIC_AI`;
- `RAG_SEARCH`;
- `GENAI_LLM`;
- `FULLSTACK_AI`;
- `AI_PLATFORM`;
- `TRADITIONAL_ML`;
- `GENERAL_AI`.

Current priorities:

- `TIER_A`;
- `TIER_B`;
- `TIER_C`.

`CareerWorkflowPipeline.select()` performs:

1. applied-ID union from CSV and SQLite;
2. ledger metadata-coverage measurement;
3. adaptive-strategy construction;
4. adaptive ranking;
5. score-agnostic eligibility annotation;
6. diversity ordering;
7. attempt-budget calculation;
8. candidate scan-budget calculation;
9. exploration/exploitation selection.

`src/application/eligibility.py:evaluate_auto_apply_eligibility()` currently returns every classified candidate as eligible.

`AUTO_APPLY_MIN_SCORE` is retained for audit compatibility but is not enforced by this eligibility function.

Hard eligibility filtering occurs upstream through AI relevance, red-flag, and location/work-mode policy.

## 14. Diversity Controls

`src/application/diversity.py` implements:

- normalized company keys;
- normalized role families;
- normalized locations;
- experience signatures;
- tag signatures;
- vacancy fingerprints;
- vacancy-family fingerprints;
- normalized-description hashes.

`diversify_jobs()` uses historical company application counts, maximum company count per run, maximum role-family count per company, and maximum exact vacancy fingerprint count.

Company and role-family caps shape primary ordering. Overflow candidates are appended rather than discarded.

Exact vacancy-fingerprint duplicates can be discarded.

## 15. Application Policy and Execution

`src/application/policy.py` models:

- minimum score;
- allowed priorities;
- allowed subtracks;
- dry-run;
- maximum applications per run;
- maximum applications per day.

The active staged pipeline constructs policy with dry-run and per-run limit.

The modeled per-day maximum is not enforced by `run_application_batch()`.

`apply_agent.py:run_application_batch()` performs per candidate:

1. ledger qualified record;
2. local duplicate suppression;
3. static policy evaluation;
4. dry-run suppression;
5. per-run attempt limit;
6. external-apply detection;
7. live execution;
8. success or already-applied persistence;
9. failure classification and recording.

External applications are recorded in the ledger and added to `ManualActionQueue`.

The manual queue is JSON-backed and currently supports external-apply work.

## 16. Single-Job Application Flow

`apply_agent.py:process_job_application()`:

1. derives mandatory and optional skills from tags;
2. calls `NaukriJobClient.apply_job()` through bounded safe retry;
3. stores raw response;
4. interprets response;
5. returns for applied or already-applied outcomes;
6. invokes questionnaire resolution when required;
7. logs unresolved questions;
8. fails safely when manual review is required;
9. submits serialized questionnaire answers;
10. stores final raw response;
11. interprets final outcome.

`src/application/response_interpreter.py:interpret_application_response()` recognizes:

- questionnaire required;
- validation failed;
- already applied;
- applied;
- profile data required;
- unknown.

Unknown response shapes are not treated as success.

`src/application/response_classifier.py` contains separate unused classification logic and is not part of the active production path.

## 17. Retry and Failure Handling

`execute_with_safe_retry()` permits bounded retries only for failures classified as `RETRYABLE_SAFE`.

Ambiguous and permanent failures are raised immediately.

Default maximum retries: 2 after the initial attempt.

`src/application/failure.py` owns exception classification.

## 18. Questionnaire Resolution

The active path is `src/resolution/hybrid_resolver.py:HybridQuestionResolver`.

Resolution order:

1. deterministic resolver;
2. answer constraints;
3. serialization;
4. LLM fallback only if unresolved;
5. LLM action/confidence safety gate;
6. semantic canonicalization;
7. answer-shape validation;
8. answer constraints;
9. questionnaire serialization;
10. resolved answer or manual review.

The LLM does not override deterministic answers.

`src/utils/questionnaire_resolver.py` contains the deterministic rule system and serialization helpers.

`src/resolution/evidence_retriever.py:retrieve_evidence()` deterministically retrieves relevant subsets from candidate evidence, including capabilities, projects, approved answers, positionable claims, unsupported claims, and LLM policy. It does not use embeddings or an LLM.

`src/llm/question_resolver.py:LLMQuestionResolver` returns `LLMQuestionDecision` with category, action, semantic answer, confidence, and reasoning.

`LLMQuestionDecision.is_safe_to_auto_answer()` requires action `answer`, non-empty semantic answer, and confidence of at least 0.85 by default.

Unresolved questions are appended by `src/utils/questionnaire_telemetry.py` to `data/questionnaire_telemetry.csv`.

## 19. Persistence and Data Flow

Current runtime persistence is fragmented across SQLite, CSV, JSON, raw response files, and run artifacts.

### SQLite

`data/application_ledger.db`

Owned by `ApplicationLedger`.

### CSV

`data/applied_jobs.csv` — append-only duplicate-prevention compatibility store.

`data/questionnaire_telemetry.csv` — unresolved-question telemetry.

### JSON

`data/job_search_cache.json` — versioned search cache.

`data/search_challenge_state.json` — challenge cooldown state.

`data/score_cache.json` — LLM score cache.

`data/manual_action_queue.json` — external/manual action queue.

### Raw responses

`data/responses/*.json`

Raw application and questionnaire submission responses.

### Run artifacts

`artifacts/runs/<run_id>/`

Expected stage artifacts include:

- `run.json`;
- `preflight.json`;
- `acquisition.json`;
- `classification.json`;
- `selection.json`;
- `application.json`;
- `reconciliation.json`;
- `strategy.json`;
- `report.json`;
- `result.json`.

### Legacy SQLite

`src/utils/dbhandler.py:NkparamDB` can create `nkparams.db`.

No active production caller was found during the audit.

## 20. SQLite Schema

`ApplicationLedger` creates four tables.

### applications

Primary key: `job_id`.

Columns:

- `job_id TEXT PRIMARY KEY`;
- `title TEXT NOT NULL DEFAULT ''`;
- `company TEXT NOT NULL DEFAULT ''`;
- `location TEXT NOT NULL DEFAULT ''`;
- `score INTEGER`;
- `priority TEXT NOT NULL DEFAULT ''`;
- `subtrack TEXT NOT NULL DEFAULT ''`;
- `source TEXT NOT NULL DEFAULT ''`;
- `status TEXT NOT NULL`;
- `first_seen_at TEXT NOT NULL`;
- `last_updated_at TEXT NOT NULL`;
- `applied_at TEXT`;
- `last_error TEXT`;
- `server_status TEXT`;
- `server_status_at TEXT`;
- `lifecycle_stage TEXT NOT NULL DEFAULT 'UNKNOWN'`;
- `lifecycle_updated_at TEXT`;
- `submitted_at TEXT`;
- `viewed_at TEXT`;
- `shortlisted_at TEXT`;
- `interview_at TEXT`;
- `rejected_at TEXT`;
- `offer_at TEXT`.

This table combines source job identity, job metadata, candidate evaluation, application execution state, source provenance, server status, normalized lifecycle, and lifecycle timestamps.

It does not satisfy the PRD separation between canonical job, source observation, evaluation, and application.

### status_events

- `id INTEGER PRIMARY KEY AUTOINCREMENT`;
- `job_id TEXT NOT NULL`;
- `status TEXT NOT NULL`;
- `detail TEXT`;
- `created_at TEXT NOT NULL`.

### strategy_decisions

- `id INTEGER PRIMARY KEY AUTOINCREMENT`;
- `run_id INTEGER`;
- `strategy_json TEXT NOT NULL`;
- `created_at TEXT NOT NULL`.

### runs

- `run_id INTEGER PRIMARY KEY AUTOINCREMENT`;
- `started_at TEXT NOT NULL`;
- `finished_at TEXT`;
- `dry_run INTEGER NOT NULL`;
- `fetched INTEGER NOT NULL DEFAULT 0`;
- `qualified INTEGER NOT NULL DEFAULT 0`;
- `applied INTEGER NOT NULL DEFAULT 0`;
- `already_applied INTEGER NOT NULL DEFAULT 0`;
- `failed INTEGER NOT NULL DEFAULT 0`;
- `summary_json TEXT`.

Indexes exist on status event job ID, application status, application company, application lifecycle stage, and strategy-decision run ID.

The only schema migration mechanism is `ApplicationLedger._migrate_application_columns()`, which conditionally adds lifecycle columns.

There is no general explicit migration framework.

## 21. Lifecycle Reconciliation

`ApplicationLedger.reconcile_server_history()`:

- reads parsed Naukri history;
- extracts earliest timestamps for normalized lifecycle stages;
- determines latest server status;
- inserts server-only historical applications;
- updates changed raw server status;
- appends server-status events;
- backfills missing lifecycle timestamps;
- advances normalized lifecycle only when permitted.

Normalized stages:

- `UNKNOWN`;
- `SUBMITTED`;
- `VIEWED`;
- `SHORTLISTED`;
- `INTERVIEW`;
- `REJECTED`;
- `OFFER`.

Lifecycle rules:

- unknown never overwrites meaningful state;
- first meaningful state is accepted;
- ordinary states advance monotonically;
- rejected and offer are terminal outcomes;
- offer is sticky;
- rejected can be replaced by offer as a correction.

The larger PRD lifecycle is not implemented.

## 22. Analytics

`src/application/analytics.py` implements:

- cumulative funnel;
- priority breakdown;
- subtrack breakdown;
- company breakdown;
- score-band breakdown;
- application age distribution;
- application velocity;
- response-time summary.

Analytics data comes from `ApplicationLedger.analytics_rows()`.

Included statuses:

- `applied`;
- `already_applied`;
- `server_history`.

Operational states such as dry-run suppression and external-apply skips are excluded.

Application timestamp logic deliberately avoids treating `first_seen_at` as submission time.

## 23. Adaptive Strategy

`src/application/adaptive_strategy.py` implements evidence-gated adaptation.

Activation requires configurable minimum application and response counts.

Pipeline selection also disables adaptation when classification metadata coverage is below the configured threshold.

Strategy groups performance by priority and subtrack.

Performance uses:

- smoothed response rate;
- prior strength;
- age decay;
- weighted lifecycle outcomes.

Lifecycle outcome weights range from zero for unknown/submitted to 12 for offer.

Strategy can affect:

- preferred priority groups;
- preferred subtracks;
- adaptive ranking;
- exploration/exploitation allocation;
- suggested run capacity;
- computed minimum score.

The current broad-coverage eligibility function does not enforce adaptive minimum score as a hard application gate.

## 24. Environment Configuration

Runtime code references these environment variables.

Credentials and local model:

- `NAUKRI_USERNAME`;
- `NAUKRI_PASSWORD`;
- `OMLX_BASE_URL`;
- `OMLX_API_KEY`;
- `OMLX_MODEL`;
- `QUESTIONNAIRE_LLM_MODEL`.

Live execution:

- `LIVE_APPLICATION_CONFIRMATION`;
- `APPLICATION_DRY_RUN`;
- `MAX_APPLICATIONS_PER_RUN`.

Search:

- `SEARCH_EXPERIENCE_LEVELS`;
- `SEARCH_MAX_PAGES`;
- `SEARCH_RESULTS_PER_PAGE`;
- `SEARCH_JOB_AGE_DAYS`;
- `JOB_SEARCH_CACHE_PATH`;
- `JOB_SEARCH_CACHE_TTL_DAYS`;
- `SEARCH_CHALLENGE_STATE_PATH`;
- `SEARCH_CHALLENGE_COOLDOWN_MINUTES`.

Classification and detail budget:

- `DETAIL_FETCH_BUDGET`;
- `DETAIL_BUDGET_MAX_PER_COMPANY`;
- `DETAIL_BUDGET_MAX_PER_FAMILY`;
- `AUTO_APPLY_MIN_SCORE`.

Selection and diversity:

- `MAX_APPLICATIONS_PER_COMPANY_PER_RUN`;
- `MAX_ROLE_FAMILY_PER_COMPANY`;
- `MAX_PER_VACANCY_FINGERPRINT`;
- `APPLICATION_SCAN_MULTIPLIER`.

Adaptive strategy:

- `ADAPTIVE_STRATEGY_ENABLED`;
- `ADAPTIVE_MIN_APPLICATIONS`;
- `ADAPTIVE_MIN_RESPONSES`;
- `ADAPTIVE_MIN_GROUP_SAMPLES`;
- `ADAPTIVE_EXPLORATION_FRACTION`;
- `ADAPTIVE_PRIOR_STRENGTH`;
- `ADAPTIVE_DECAY_HALF_LIFE_DAYS`;
- `ADAPTIVE_RESPONSE_WEIGHT`;
- `ADAPTIVE_OUTCOME_WEIGHT`;
- `ADAPTIVE_MIN_METADATA_COVERAGE`.

Persistence and monitoring:

- `APPLICATION_LEDGER_PATH`;
- `MANUAL_ACTION_QUEUE_PATH`;
- `STALE_APPLICATION_DAYS`.

Runtime defaults are not fully consistent between staged and legacy paths. Code contains differing defaults for `AUTO_APPLY_MIN_SCORE` and `MAX_APPLICATIONS_PER_RUN`.

`.env.example` is incomplete relative to all runtime variables referenced in code.

## 25. Security-Sensitive Runtime Data

The following must remain local and outside public Git history:

- `.env`;
- credentials;
- API keys;
- Naukri session cookies and tokens;
- candidate profile data;
- candidate evidence;
- application ledger databases;
- applied-jobs CSV;
- questionnaire telemetry;
- raw application responses;
- job-search cache;
- score cache;
- challenge cooldown state;
- manual action queue;
- orchestration run artifacts;
- local SQLite databases;
- nkparam token pools and equivalent anti-bot or session material.

The audited snapshot contains `config/candidate_profile.py` and `config/candidate_evidence.py`, which are security-sensitive candidate data.

`src/client/job_client.py:NaukriJobClient.__init__()` contains a pre-captured nkparam token literal and must be treated as security-sensitive source-specific material.

## 26. Test Organization and Validation

The audited baseline contained 38 `test_*.py` files.

The original static AST inventory found 206 test functions or methods before the deterministic oMLX test correction.

Original distribution:

- `tests/application/`: 19 files, 149 tests;
- `tests/client/`: 4 live/integration-style scripts rather than ordinary pytest test functions;
- `tests/llm/`: 2 files;
- `tests/orchestration/`: 1 file, 7 tests;
- `tests/resolution/`: 5 files;
- `tests/search/`: 7 files, 45 tests.

Phase 0 corrected:

- forward-annotation import failure in `apply_agent.py`;
- import-time oMLX network dependency in `tests/llm/test_omlx_client.py`.

Validated post-fix state:

- imports pass;
- pytest collection passes;
- focused subsystem tests pass;
- full regression suite passes;
- source compilation passes;
- staged pipeline dry-run passes.

`tests/client/` remains integration/live oriented and is not equivalent to the deterministic unit and regression suites.

AppleDouble `._*` metadata files must be excluded from generic compilation commands or removed because they are not Python source.

## 27. Known Architectural Coupling

### Pipeline to legacy module

`src/orchestration/pipeline.py` imports acquisition, detail enrichment, application metadata enrichment, applied-job CSV access, terminal reporting, and batch execution from `apply_agent.py`.

The staged pipeline is therefore not independent of the legacy monolith.

### Pipeline to Naukri

`CareerWorkflowPipeline.acquire()` directly constructs `NaukriLoginClient` and `NaukriJobClient`.

Reconciliation also depends on Naukri-specific history behavior.

No source adapter boundary exists.

### Representation coupling

The classifier normalizes source `Job` objects into dictionaries.

Selection later maps dictionaries back to original `Job` objects using `job_id`.

Application execution consumes both source `Job` objects and dictionary metadata.

### Ledger domain coupling

The `applications` row combines job, evaluation, source, execution, and lifecycle concerns.

### Candidate evidence coupling

Questionnaire resolution directly imports local candidate evidence and profile configuration.

This is compatible with local-first operation but must remain separate from source-job and canonical-job domains.

## 28. Duplicated and Legacy Responsibilities

Confirmed duplicated or legacy areas:

1. staged orchestration in `CareerWorkflowPipeline` versus legacy orchestration in `run_application_cycle()`;
2. CSV duplicate prevention versus SQLite applied-ID suppression;
3. active `response_interpreter.py` versus unused `response_classifier.py`;
4. active application metadata taxonomy versus separate `tools/score_jobs.py` taxonomy;
5. active questionnaire path versus unused client questionnaire helper path;
6. active application flow versus unused chatbot response path;
7. active generated nkparam path versus unused `NkparamDB`;
8. SQLite run state versus filesystem orchestration run artifacts.

These areas require incremental migration, not rewrite.

## 29. Technical Debt and Migration Risks

### High risk

- Current application storage collapses source job, evaluation, application, and lifecycle concerns.
- Naukri behavior leaks directly into orchestration.
- The staged pipeline imports substantial behavior from `apply_agent.py`.
- Two end-to-end orchestration paths remain.
- Application idempotency depends on both CSV and SQLite.
- Manual action queue is separate JSON persistence.
- Candidate evidence exists in repository source.
- A pre-captured platform token literal exists in Naukri client code.

### Medium risk

- Classification representation changes from `Job` object to dictionary and back.
- Acquisition provenance is stored as a mutable dynamic attribute.
- Search cache is versioned while relational persistence lacks a general migration framework.
- Unused response classification logic can diverge from active response interpretation.
- Unused client questionnaire and chatbot helpers can be mistaken for active behavior.
- `NkparamDB` exists without active production callers.
- Tooling contains a separate scoring taxonomy.
- Environment defaults differ between execution paths.
- Adaptive strategy computes a minimum score that eligibility does not enforce.
- Per-day application maximum is modeled but not enforced by the active batch executor.
- `PipelineContext.ledger_run_id` typing differs from ledger return type.
- Manual-review result accounting is incomplete.
- External manual queue URL mapping may be incomplete because the source `Job` field is `apply_link`.

### Low risk

- AppleDouble metadata files exist in the snapshot.
- `DECISIONS.md` contains documentation hygiene issues.

## 30. Career Workflow 2.0 Compatibility Constraints

Phase 1 must preserve:

1. `run_pipeline.py` CLI behavior.
2. Dry-run default.
3. Explicit live confirmation.
4. Live canary limit.
5. `apply_agent.py` compatibility until replacement is proven.
6. Existing `Job` consumers during canonical model introduction.
7. Naukri authentication, search, detail, apply, questionnaire, and history behavior.
8. Applied-job suppression from CSV and SQLite.
9. Search cache schema versions 1 and 2 readability.
10. Persistent challenge cooldown behavior.
11. Acquisition provenance values `live`, `cache`, and `live+cache`.
12. Cheap filtering before detail fetching and LLM scoring.
13. Broad AI-role eligibility.
14. Score as ranking rather than a general hard rejection gate.
15. Current Pune office/hybrid policy.
16. Current global remote acceptance behavior.
17. Full-description red-flag checks.
18. Score-cache compatibility or explicit versioned invalidation.
19. Historical analyzability of current priority and subtrack values.
20. Diversity overflow semantics.
21. Exact vacancy duplicate suppression.
22. External-application manual queue behavior.
23. Deterministic-first questionnaire resolution.
24. Candidate-grounded LLM fallback.
25. Confidence gating.
26. Canonicalization and shape validation.
27. Answer constraints and serialization validation.
28. Unresolved-question telemetry.
29. Raw response capture.
30. Unknown response shapes not being treated as success.
31. Bounded safe retry.
32. SQLite application history.
33. Lifecycle timestamps and status events.
34. Idempotent and monotonic reconciliation.
35. Sticky terminal lifecycle behavior.
36. `REJECTED` to `OFFER` correction.
37. Recruiting funnel population semantics.
38. Adaptive-strategy evidence gates.
39. Run artifact and stage-status compatibility until replacement observability is proven.

Phase 1 must not:

- introduce database v2 tables;
- implement API work;
- implement UI work;
- introduce unrelated infrastructure;
- place Naukri response structures or application mechanics inside source-independent domain objects.

## 31. Actual Gaps Against the PRD

### Implemented foundations

Implemented foundations include:

- staged orchestration;
- Naukri acquisition;
- broad AI search portfolio;
- exact source-job-ID deduplication;
- description and vacancy fingerprinting;
- AI relevance filtering;
- broad transition eligibility;
- Pune location policy;
- work-mode inference;
- fit scoring;
- score explanation;
- priority and subtrack metadata;
- direct Naukri auto-apply;
- external redirect queueing;
- questionnaire resolution;
- application tracking;
- lifecycle reconciliation;
- analytics;
- adaptive strategy.

### Partial

Partial capabilities:

- provenance exists as a string attribute, not a source-observation model;
- same-source and heuristic local dedup exist, but no cross-source canonical entity resolution;
- work mode exists, but remote-scope taxonomy does not;
- score and evaluation metadata exist, but are not versioned or separated from application storage;
- action queue is external JSON only;
- recruiting lifecycle stages exist, but not the full canonical product lifecycle;
- status events exist, but are keyed by job ID rather than application ID and lack explicit from/to state fields;
- application run table and filesystem run state exist, but no full relational source/stage run model;
- one ad hoc schema migration exists, but no explicit migration framework;
- challenge state and acquisition counters exist, but no general source-health model.

### Missing

Missing PRD capabilities:

- canonical source-independent job identity;
- source observation entity;
- source identity model;
- source capability model;
- source adapter protocol;
- Naukri adapter boundary;
- canonical URL matching;
- ATS requisition identity handling;
- cross-source deduplication;
- confidence-based canonical merge;
- preferred application route resolution;
- multi-source scheduled discovery;
- source-specific scheduling;
- source synchronization state;
- general source-health persistence;
- versioned candidate evaluations;
- fit/urgency separation;
- remote-scope classification;
- full application capability model;
- assisted apply workflow;
- first-class manual apply sessions;
- database-backed job action queue;
- shortlist/ignore/watch workflow;
- follow-up workflow;
- recruiter response workflow;
- interview entities;
- interview rounds;
- interview preparation workspace;
- notes and tasks domain;
- workflow API;
- operational UI;
- Today page;
- job inbox;
- job detail UI;
- applications UI;
- interview center;
- system/runs UI;
- target database v2 tables;
- explicit migration framework;
- database backup and rollback workflow;
- external source adapters beyond Naukri.

## 32. Phase 0 Exit State

Phase 0 baseline audit and stabilization are complete.

Completed deliverables:

- repository structure mapped;
- runtime entry points mapped;
- execution flow mapped;
- acquisition behavior validated;
- classification behavior validated;
- scoring behavior validated;
- selection behavior validated;
- application execution paths validated;
- questionnaire resolution validated;
- policy and diversity controls validated;
- search cache and challenge handling validated;
- persistence mechanisms mapped;
- SQLite schema documented;
- lifecycle reconciliation validated;
- analytics mapped;
- adaptive strategy mapped;
- orchestration stages mapped;
- environment configuration inventoried;
- runtime artifacts inventoried;
- test organization audited;
- architectural coupling documented;
- duplicated responsibilities documented;
- compatibility constraints documented;
- security-sensitive runtime data identified;
- implementation gaps against the PRD classified;
- baseline import blocker corrected;
- deterministic test collection restored;
- full regression suite validated green;
- source compilation validated green;
- staged pipeline dry-run validated green.

Phase 0 is ready for final baseline tagging after this document is committed and the final freeze audit passes on the resulting `main` commit.

No Phase 1 implementation is included in this state.
