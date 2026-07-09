# Career Workflow — Product Requirements Document and Business Requirements Document

**Document status:** Living source of truth
**Product:** Career Workflow
**Product type:** Local-first personal Job Search Operating System
**Primary user:** Repository owner
**Primary market scope:** AI-related jobs in India and globally remote roles
**Current implementation base:** Existing Python Career Workflow repository, evolved from the NopeRi/Noperi Naukri API client foundation
**Document purpose:** Product map, architecture boundary, implementation sequence, acceptance criteria, and decision record for continued development

---

## 1. Executive Summary

Career Workflow is a local-first, candidate-specific Job Search Operating System for discovering, evaluating, prioritizing, applying to, tracking, and learning from AI-related job opportunities.

The system already contains a substantial Naukri-focused backend: resilient acquisition, candidate-aware classification, AI relevance filtering, fit scoring, policy controls, diversity controls, direct and questionnaire application flows, failure handling, a persistent SQLite application ledger, server-side lifecycle reconciliation, analytics, adaptive strategy, and staged orchestration.

The product objective is to evolve that backend into one definitive personal application for:

- discovering AI-related jobs across India;
- discovering globally remote AI-related jobs for which the candidate is eligible;
- aggregating multiple job sources into one canonical job store;
- deduplicating the same vacancy across platforms;
- filtering and ranking opportunities against the candidate's actual target strategy;
- automatically applying where reliable and appropriate;
- assisting manual application where automation is unavailable or undesirable;
- opening the correct application route and minimizing context switching;
- tracking every job and application through the complete recruiting lifecycle;
- managing follow-ups and stale applications;
- converting interview opportunities into structured preparation workflows;
- measuring source, role, score, application, resume, and funnel performance;
- adapting strategy only when sufficient evidence exists.

The core product principle is:

> The user should not need to repeatedly search individual job platforms, remember application state manually, or decide from scratch what to do next. The system should continuously build a unified opportunity set and present the highest-value next actions.

The product is not intended to maximize indiscriminate application volume. It is intended to maximize useful coverage, reduce missed opportunities, reduce repeated manual work, preserve application quality, and improve interview and offer probability through disciplined execution and feedback.

---

# 2. Business Requirements Document

## 2.1 Business Problem

The AI job market is fragmented across:

- Indian job portals;
- professional networks;
- startup hiring platforms;
- remote job boards;
- applicant tracking systems;
- employer career pages;
- recruiter outreach;
- manually discovered opportunities.

A candidate searching these sources independently faces several structural problems:

1. **Discovery fragmentation**
   Relevant opportunities are spread across many platforms and search interfaces.

2. **Duplicate exposure**
   The same vacancy may appear on several aggregators and the original employer ATS.

3. **High decision cost**
   Every job requires repeated evaluation of relevance, fit, geography, work mode, seniority, stack compatibility, and application value.

4. **Application friction**
   Some jobs can be applied to directly, some require questionnaires, and some require external/manual flows.

5. **State fragmentation**
   Application status, recruiter responses, interviews, rejections, follow-ups, and stale applications are difficult to track consistently.

6. **Poor feedback quality**
   Without structured data, the candidate cannot reliably determine which sources, role families, score bands, resume variants, or strategies produce interviews.

7. **Context switching**
   Repeatedly moving between job boards, spreadsheets, email, browser tabs, notes, and interview preparation wastes time.

8. **Timing pressure**
   The user must begin applying and interviewing now. Product development cannot become a substitute for actual job-search execution.

Career Workflow exists to solve these problems as one integrated operating system.

---

## 2.2 Business Objective

Create a single personal application that becomes the operational control plane for the user's AI job search.

The application must support the complete loop:

```text
DISCOVER
    ↓
NORMALIZE
    ↓
DEDUPLICATE
    ↓
QUALIFY
    ↓
SCORE
    ↓
PRIORITIZE
    ↓
ACT
    ↓
TRACK
    ↓
FOLLOW UP
    ↓
INTERVIEW
    ↓
MEASURE
    ↓
ADAPT
    └──────────────► DISCOVER
```

The system must answer these operational questions:

- What relevant new jobs appeared?
- Which jobs are genuinely AI-related?
- Which jobs am I geographically eligible for?
- Which jobs are highest priority?
- Which jobs can the system apply to automatically?
- Which jobs require manual action?
- Which manual application should I do next?
- Which applications require follow-up?
- Which applications have progressed?
- Which interviews are upcoming?
- What should I prepare for each interview?
- Which sources and strategies are producing useful outcomes?
- Where is the job-search funnel failing?

---

## 2.3 Success Definition

The product is successful when the user can conduct the majority of the operational job-search workflow from one interface.

A successful mature workflow is:

```text
Open Career Workflow
        ↓
Review Today page
        ↓
Process high-priority jobs
        ↓
Run or approve automatic applications
        ↓
Complete manual application session
        ↓
Review follow-ups
        ↓
Review upcoming interviews
        ↓
Close application
```

Success is not defined by the number of adapters, scraped jobs, or automated submissions.

Success is defined by:

- high coverage of relevant opportunities;
- low duplicate noise;
- low irrelevant-job noise;
- low time spent searching individual platforms;
- short time from discovery to application;
- complete application-state tracking;
- disciplined follow-up;
- improved interview conversion;
- reliable data for strategy decisions.

---

## 2.4 Business Scope

### In scope

- India-based AI-related jobs;
- global remote AI-related jobs where the candidate can realistically work;
- multi-source job discovery;
- canonical job normalization;
- cross-source vacancy deduplication;
- AI relevance classification;
- candidate-specific fit scoring;
- location and remote eligibility;
- role-family and subtrack classification;
- job ranking and priority;
- automatic application where technically reliable;
- assisted and manual application workflows;
- application state tracking;
- recruiter lifecycle tracking;
- follow-up tasks;
- stale application detection;
- interview tracking and preparation;
- run observability;
- funnel analytics;
- source performance analytics;
- evidence-gated strategy adaptation.

### Out of scope for the current personal-product phase

- SaaS productization;
- multi-user accounts;
- public user registration;
- billing;
- subscriptions;
- organization tenancy;
- cloud-native microservices;
- Kubernetes;
- Kafka;
- generic candidate onboarding;
- mobile native applications;
- social networking;
- job-board marketplace functionality;
- indiscriminate auto-apply on every source;
- fabricated questionnaire answers or candidate qualifications;
- complex agent frameworks without a demonstrated product need.

---

## 2.5 Business Constraints

### BC-01: Job search must continue during development

The system must be built incrementally. Existing working application capability must remain usable while the product expands.

### BC-02: Current working backend must be preserved

The existing Naukri pipeline is an asset, not a prototype to discard. Refactoring must preserve behavior behind regression tests.

### BC-03: Local-first operation

The primary deployment target is the user's own machine. SQLite and local services are acceptable and preferred until scale proves otherwise.

### BC-04: Conservative automation

Unknown or ambiguous execution outcomes must not be counted as successful applications.

### BC-05: Candidate-grounded answers

Questionnaire answers must derive from candidate profile data and evidence. The system must not fabricate experience, qualifications, salary facts, notice period, authorization, or other material claims.

### BC-06: Broad AI eligibility strategy

Genuinely AI-related roles should normally remain eligible despite imperfect stack match. Stack mismatch should affect ranking and priority, not automatically cause rejection.

### BC-07: Geography strategy

The default target policy is:

- office roles: Pune-compatible only;
- hybrid roles: Pune-compatible only;
- unknown work mode: Pune-compatible only unless manually overridden;
- remote roles: globally discoverable, but remote eligibility must be evaluated;
- a job saying “remote” is not sufficient evidence of India eligibility.

### BC-08: Development time must remain bounded

Engineering effort must prioritize features that directly improve real application throughput, opportunity coverage, state management, or interview conversion.

---

# 3. Product Requirements Document

## 3.1 Product Vision

Career Workflow will be the definitive personal operating system for the user's AI job search.

It will combine:

```text
JOB AGGREGATOR
+
CANDIDATE-SPECIFIC DECISION ENGINE
+
APPLICATION EXECUTION ENGINE
+
PERSONAL APPLICATION CRM
+
FOLLOW-UP MANAGER
+
INTERVIEW WORKSPACE
+
JOB-SEARCH ANALYTICS SYSTEM
```

The product should optimize the user's attention, not merely automate clicks.

---

## 3.2 Primary User

The initial product has exactly one primary user: the repository owner.

The product may encode user-specific strategy and preferences. Premature generalization for arbitrary users is explicitly discouraged.

Current target profile context:

- experienced software engineer;
- strong Angular/MEAN background;
- transitioning toward Applied AI / AI Engineer / GenAI Engineer roles;
- practical experience and portfolio focus around RAG, LLM applications, agentic systems, Azure AI, AI evaluation, backend integration, and production AI engineering;
- target compensation focus on strong senior opportunities;
- broad AI-role application strategy;
- Pune-only for office/hybrid work;
- remote roles can be globally sourced when work eligibility is plausible.

Candidate facts must remain in dedicated profile/evidence configuration, not hard-coded across classifiers.

---

## 3.3 Product Principles

### P-01: One queue, not many websites

The user should consume opportunities through a unified inbox and action queue.

### P-02: Broad acquisition, progressive narrowing

Discovery should favor recall. Expensive enrichment and scoring should be applied only after cheap gates.

### P-03: Separate observation from decision

Source data, canonical job data, candidate evaluation, and application state are separate concepts.

### P-04: Job is not application

A job can be discovered, reviewed, shortlisted, rejected, or watched without becoming an application.

### P-05: One vacancy can have many source observations

Cross-source duplicates must map to one canonical opportunity.

### P-06: Prefer original application routes

When a vacancy is found on an aggregator and an original employer or ATS application URL is available, preserve provenance and prefer the authoritative route where appropriate.

### P-07: Automation capability is source-specific

Every source does not need auto-apply. Discovery, details, application, and status sync are independent capabilities.

### P-08: Unknown is not success

Ambiguous API or browser outcomes must become retry, failure, or manual-review states.

### P-09: Evidence before adaptation

Strategy must not react aggressively to small samples.

### P-10: Product development must serve the job search

New engineering work must be evaluated against actual job-search value.

---

# 4. Current System Baseline

The existing repository already implements substantial functionality.

## 4.1 Current staged orchestration

The pipeline contains:

1. preflight;
2. acquisition;
3. classification;
4. selection;
5. application;
6. reconciliation;
7. strategy;
8. report.

Current orchestration capabilities include:

- run IDs;
- per-run artifacts;
- atomic artifact persistence;
- stage-level status;
- fatal and non-fatal stage handling;
- structured errors;
- run summaries;
- partial-run semantics.

This orchestration engine must be retained and evolved into the backend execution layer.

---

## 4.2 Current acquisition capabilities

The current Naukri acquisition engine supports:

- authenticated sessions;
- multiple search keywords;
- multiple experience buckets;
- pagination;
- configurable page depth;
- configurable page size;
- configurable job age;
- empty-page termination;
- partial-page termination;
- repeated-page fingerprint detection;
- deduplication;
- CAPTCHA/challenge detection;
- partial-result preservation;
- persistent search cache;
- challenge cooldown state;
- cached fallback;
- acquisition telemetry.

Current architecture is recall-oriented at acquisition and progressively more selective downstream.

---

## 4.3 Current intelligence capabilities

The existing classifier supports or contains foundations for:

- AI relevance classification;
- title-quality filtering;
- non-software vetoes;
- research-primary role vetoes;
- executive-scope vetoes;
- candidate-specific stack overlap;
- transition-role compatibility;
- work-mode inference;
- location eligibility;
- full-description red-flag analysis;
- role-family classification;
- subtrack classification;
- LLM-assisted fit scoring;
- deterministic post-score guards;
- score explanations;
- score caching.

Current intended strategy:

> Genuine AI-related jobs remain broadly eligible. Exact stack mismatch affects ranking and priority rather than acting as a default hard rejection.

---

## 4.4 Current application controls

Existing controls include:

- minimum score thresholds;
- dry-run mode;
- maximum applications per run;
- duplicate prevention;
- company concentration controls;
- role-family concentration controls;
- vacancy fingerprinting;
- priority-aware selection;
- subtrack-aware selection;
- exploration/exploitation allocation;
- retry-aware execution.

---

## 4.5 Current application execution

The current application layer supports:

- direct application flows;
- questionnaire flows;
- response interpretation;
- already-applied detection;
- failure classification;
- bounded retry;
- terminal failure handling;
- manual-review paths;
- local outcome persistence.

The Naukri executor should remain the first mature automatic application adapter.

---

## 4.6 Current questionnaire resolution

The repository contains a hybrid resolution architecture using:

1. candidate profile;
2. candidate evidence;
3. question normalization;
4. evidence retrieval;
5. deterministic resolution;
6. allowed-answer constraints;
7. answer-shape validation;
8. local LLM fallback;
9. schema validation;
10. response interpretation;
11. telemetry and unresolved-response capture.

This subsystem is sufficiently advanced for the current phase and should only be expanded based on live failure evidence.

---

## 4.7 Current persistent state

The current SQLite application ledger tracks:

- job metadata;
- fit score;
- priority;
- subtrack;
- source;
- execution status;
- timestamps;
- failures;
- server status;
- normalized lifecycle;
- per-stage timestamps;
- run summaries;
- append-only status events.

Current lifecycle capabilities include:

- server-history reconciliation;
- status normalization;
- monotonic lifecycle progression;
- terminal outcomes;
- stale application detection;
- lifecycle funnels;
- idempotent monitoring.

The ledger is a strong foundation but must evolve from application-centric storage to a broader job-search domain model.

---

## 4.8 Current analytics and adaptation

Existing capabilities include:

- application totals;
- lifecycle distribution;
- response rate;
- interview rate;
- offer rate;
- velocity;
- application age;
- time to first response;
- priority performance;
- subtrack performance;
- score-band performance;
- evidence-gated adaptive strategy.

Adaptive strategy must remain conservative until real outcome volume is statistically meaningful.

---

# 5. Target Product Architecture

## 5.1 Logical architecture

```text
                         SOURCE ECOSYSTEM
      ┌─────────────────────────────────────────────────┐
      │ Naukri | LinkedIn | Instahyre | Cutshort       │
      │ Wellfound | Himalayas | Remote Boards          │
      │ Greenhouse | Lever | Ashby | Career Pages      │
      └─────────────────────────────────────────────────┘
                              │
                              ▼
                    SOURCE ADAPTER LAYER
                              │
                              ▼
                     RAW SOURCE OBSERVATIONS
                              │
                              ▼
                    CANONICALIZATION ENGINE
                              │
                              ▼
                   CROSS-SOURCE DEDUPLICATION
                              │
                              ▼
                       CANONICAL JOB STORE
                              │
                              ▼
                     JOB INTELLIGENCE ENGINE
               ┌──────────────┼───────────────┐
               │              │               │
          Eligibility      Evaluation       Priority
               │              │               │
               └──────────────┼───────────────┘
                              ▼
                         ACTION ENGINE
               ┌──────────────┼───────────────┐
               ▼              ▼               ▼
          AUTO APPLY     ASSISTED APPLY    MANUAL APPLY
               │              │               │
               └──────────────┼───────────────┘
                              ▼
                       APPLICATION CRM
                              │
                              ▼
                 LIFECYCLE / FOLLOW-UP ENGINE
                              │
                              ▼
                      INTERVIEW WORKSPACE
                              │
                              ▼
                  ANALYTICS / STRATEGY ENGINE
                              │
                              └──────────────► PRIORITY
```

---

## 5.2 Proposed repository architecture

Target structure:

```text
career-workflow/
├── run_pipeline.py
├── apply_agent.py
├── monitor_applications.py
├── application_report.py
│
├── api/
│   ├── main.py
│   ├── dependencies.py
│   └── routes/
│       ├── dashboard.py
│       ├── jobs.py
│       ├── actions.py
│       ├── applications.py
│       ├── interviews.py
│       ├── runs.py
│       └── analytics.py
│
├── config/
│   ├── candidate_profile.py
│   ├── candidate_evidence.py
│   ├── search_strategy.py
│   └── source_config.py
│
├── src/
│   ├── domain/
│   │   ├── job.py
│   │   ├── evaluation.py
│   │   ├── application.py
│   │   ├── action.py
│   │   ├── interview.py
│   │   ├── source.py
│   │   └── enums.py
│   │
│   ├── sources/
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── naukri/
│   │   ├── greenhouse/
│   │   ├── lever/
│   │   ├── ashby/
│   │   ├── wellfound/
│   │   └── ...
│   │
│   ├── canonicalization/
│   │   ├── normalizer.py
│   │   ├── company_normalizer.py
│   │   ├── title_normalizer.py
│   │   └── location_normalizer.py
│   │
│   ├── deduplication/
│   │   ├── vacancy_fingerprint.py
│   │   ├── similarity.py
│   │   └── resolver.py
│   │
│   ├── intelligence/
│   │   ├── classifier.py
│   │   ├── evaluator.py
│   │   ├── eligibility.py
│   │   ├── remote_scope.py
│   │   └── prioritizer.py
│   │
│   ├── application/
│   ├── resolution/
│   ├── lifecycle/
│   ├── analytics/
│   ├── orchestration/
│   ├── persistence/
│   └── llm/
│
├── frontend/
│   └── ...
│
├── tests/
├── data/
├── artifacts/
└── docs/
    └── PRODUCT_REQUIREMENTS.md
```

This is a target direction, not a requirement to move every current module immediately.

---

# 6. Domain Model Requirements

## 6.1 Canonical Job

The source-independent canonical job model must support at least:

```text
CanonicalJob
├── id
├── title
├── normalized_title
├── company_name
├── normalized_company
├── description
├── locations[]
├── country_codes[]
├── work_mode
├── remote_scope
├── employment_type
├── experience_min
├── experience_max
├── salary_min
├── salary_max
├── salary_currency
├── salary_period
├── skills[]
├── posted_at
├── first_seen_at
├── last_seen_at
├── expires_at
├── likely_closed
├── preferred_apply_url
├── application_method
├── created_at
└── updated_at
```

Requirements:

- source-independent internal ID;
- support multiple locations;
- preserve unknown values rather than inventing defaults;
- support explicit remote-scope semantics;
- distinguish canonical application URL from source observation URL;
- track freshness independently of posting date.

---

## 6.2 Source Job Observation

```text
SourceJob
├── id
├── source
├── source_job_id
├── canonical_job_id
├── source_url
├── apply_url
├── raw_title
├── raw_company
├── raw_location
├── raw_description
├── raw_payload_reference
├── first_seen_at
├── last_seen_at
├── source_posted_at
├── active
└── metadata
```

Requirements:

- one canonical job may have many source jobs;
- source payloads must not contaminate canonical fields directly;
- source provenance must remain queryable;
- original ATS/employer routes must be distinguishable from aggregator observations.

---

## 6.3 Job Evaluation

```text
JobEvaluation
├── id
├── job_id
├── evaluator_version
├── ai_relevance
├── fit_score
├── confidence
├── eligibility
├── priority
├── urgency
├── role_family
├── subtrack
├── work_mode_assessment
├── remote_eligibility
├── strengths[]
├── gaps[]
├── red_flags[]
├── explanation
└── evaluated_at
```

Requirements:

- evaluations must be versioned;
- re-evaluation must not destroy historical evaluation records unless explicitly designed as replaceable cache;
- candidate-specific evaluation must remain separate from canonical job data;
- score explanations must be available to the UI.

---

## 6.4 Job Action

```text
JobAction
├── id
├── job_id
├── action_type
├── status
├── priority
├── due_at
├── snoozed_until
├── reason
├── source
├── run_id
├── created_at
└── updated_at
```

Action types:

```text
REVIEW
SHORTLIST_DECISION
AUTO_APPLY
ASSISTED_APPLY
MANUAL_APPLY
FOLLOW_UP
INTERVIEW_PREP
RECRUITER_RESPONSE
MANUAL_REVIEW
```

Statuses:

```text
PENDING
IN_PROGRESS
COMPLETED
SKIPPED
SNOOZED
FAILED
CANCELLED
```

The current JSON manual-action queue must eventually migrate to this database-backed model.

---

## 6.5 Application

```text
Application
├── id
├── job_id
├── application_method
├── status
├── source
├── resume_version
├── cover_letter_version
├── applied_at
├── external_reference
├── last_error
├── server_status
├── lifecycle_stage
├── lifecycle_updated_at
├── submitted_at
├── viewed_at
├── recruiter_contact_at
├── shortlisted_at
├── interview_at
├── rejected_at
├── offer_at
├── withdrawn_at
└── updated_at
```

Requirements:

- application must reference canonical job;
- support auto, assisted, and manual origin;
- lifecycle transitions must be event-backed;
- repeated reconciliation must be idempotent.

---

## 6.6 Application Event

```text
ApplicationEvent
├── id
├── application_id
├── event_type
├── from_state
├── to_state
├── detail
├── source
└── created_at
```

Event history is append-only.

---

## 6.7 Interview

```text
Interview
├── id
├── application_id
├── company
├── role
├── current_round
├── status
├── scheduled_at
├── timezone
├── meeting_url
├── preparation_status
├── notes
└── updated_at
```

Interview rounds:

```text
InterviewRound
├── id
├── interview_id
├── sequence
├── round_type
├── scheduled_at
├── status
├── preparation_notes
├── feedback_notes
└── outcome
```

---

# 7. Source Adapter Requirements

## 7.1 Adapter contract

Every source adapter must expose a common conceptual contract:

```text
SourceAdapter

search(search_spec) -> list[SourceJobCandidate]

get_job_details(source_job_id) -> SourceJobDetails

get_application_capability(job) -> ApplicationCapability

apply(job, application_context) -> ApplicationResult

sync_status(application) -> StatusSyncResult
```

Not all capabilities are mandatory.

Adapters declare capability flags:

```text
CAN_SEARCH
CAN_FETCH_DETAILS
CAN_AUTO_APPLY
CAN_ASSIST_APPLY
CAN_SYNC_STATUS
CAN_FETCH_RECOMMENDATIONS
```

The orchestrator must not assume all adapters support all operations.

---

## 7.2 Initial source roadmap

The source strategy uses four complementary acquisition families:

1. direct job platforms;
2. ATS-backed employer boards;
3. remote-specialist boards;
4. meta-aggregation and search discovery.

No single source is expected to provide complete coverage. The product combines direct integrations with aggregation-based coverage-gap discovery and canonical source resolution.

### Tier 0 — Existing

- Naukri.

Naukri remains the first production source and currently provides the deepest integration:

- search;
- recommended jobs;
- job details;
- automated application;
- questionnaire handling;
- application-history synchronization;
- lifecycle reconciliation.

### Tier 1A — Direct ATS Sources

Highest-priority external source integrations:

- Greenhouse-backed employer boards;
- Lever-backed employer boards;
- Ashby-backed employer boards;
- Workable-backed employer boards;
- SmartRecruiters-backed employer boards.

These sources are preferred because they provide direct employer-originated vacancies and generally resolve to authoritative application routes.

### Tier 1B — India-Focused Discovery

- LinkedIn discovery;
- Instahyre;
- Cutshort;
- Hirist;
- Foundit;
- Indeed India discovery.

These sources expand India-specific coverage beyond Naukri.

The primary geographic policy remains:

- office roles: Pune only;
- hybrid roles: Pune only;
- remote roles: eligible regardless of employer geography when India-based employment is permitted;
- unknown work mode: conservative location handling until resolved.

### Tier 1C — Global Remote Discovery

- Wellfound;
- Himalayas;
- Remote OK;
- We Work Remotely;
- Remotive;
- YC Jobs;
- selected AI-specific job boards.

These sources are used for genuinely remote global opportunities.

Remote eligibility must consider:

- India eligibility;
- worldwide eligibility;
- timezone constraints;
- country restrictions;
- work authorization requirements;
- contractor versus employee arrangement;
- compensation currency where available.

### Tier 1D — Meta-Aggregation and Search Discovery

- Google Jobs / Google for Jobs result discovery;
- search-engine job discovery;
- structured `JobPosting` metadata discovery;
- employer career-page discovery;
- ATS fingerprinting and original-source resolution.

This source family exists primarily for coverage-gap detection.

Google/search-derived observations are not automatically treated as authoritative canonical jobs.

The required processing flow is:

```text
Google/Search Discovery
        ↓
Search Result Extraction
        ↓
Original Source Resolution
        ↓
Employer / ATS Identification
        ↓
Canonical URL Resolution
        ↓
Cross-Source Entity Resolution
        ↓
Canonical Job Merge
        ↓
Eligibility Evaluation
        ↓
Preferred Application Route Selection
```

A Google/search observation may resolve to:

- an employer career page;
- Greenhouse;
- Lever;
- Ashby;
- Workable;
- SmartRecruiters;
- Workday;
- another ATS;
- a job platform;
- an unresolved external application page.

The system must prefer the authoritative employer or ATS application route over an aggregator route when both represent the same vacancy.

Google/search discovery must therefore be implemented as a discovery and source-resolution adapter, not as an independent authoritative application system.

### Tier 2 — Expanded ATS and Career-Site Coverage

- Workday career pages;
- target-company career pages;
- additional ATS families;
- selected recruitment agency sources;
- niche AI engineering boards;
- startup-specific sources.

### Tier 3 — Evidence-Driven Gap Filling

Additional sources are added only when coverage analysis demonstrates meaningful unique eligible-job yield.

Source implementation order is not permanently fixed. It must be adjusted using:

- unique canonical jobs contributed;
- unique eligible jobs contributed;
- Tier A and Tier B opportunity yield;
- duplicate rate;
- source freshness;
- integration reliability;
- implementation cost;
- maintenance burden;
- application conversion;
- interview conversion.

## 7.3 Source value metrics

Each source must eventually be measurable by:

- jobs discovered;
- unique canonical jobs contributed;
- eligible jobs;
- high-priority jobs;
- applications;
- responses;
- interviews;
- offers;
- duplicate ratio;
- stale-job ratio;
- source failure rate;
- acquisition latency.

A source with high raw volume but negligible unique eligible yield is low value.

---


## 7.4 Meta-Discovery Source Requirements

Meta-discovery adapters differ from ordinary job-source adapters.

A conventional source adapter may directly provide:

```text
source job
    ↓
job details
    ↓
application capability
    ↓
application route
```

A meta-discovery adapter provides:

```text
discovery observation
    ↓
candidate vacancy URL
    ↓
source resolution
    ↓
canonical job matching
    ↓
authoritative application route
```

Meta-discovery adapters must support the following conceptual contract:

```text
MetaDiscoveryAdapter

discover(search_spec) -> list[DiscoveryObservation]

resolve_source(observation) -> SourceResolution

resolve_canonical_url(source_resolution) -> CanonicalRoute

match_existing_job(canonical_route) -> CanonicalJobMatch
```

Required metadata includes:

```text
DiscoveryObservation
├── discovery_source
├── discovered_title
├── discovered_company
├── discovered_location
├── discovered_url
├── snippet
├── discovered_at
├── possible_original_source
└── resolution_status
```

Resolution statuses:

```text
UNRESOLVED
RESOLVED_EMPLOYER
RESOLVED_ATS
RESOLVED_JOB_BOARD
DUPLICATE_EXISTING
STALE
INVALID
```

Meta-discovery requirements:

- preserve discovery provenance;
- resolve redirect chains where legally and technically appropriate;
- identify known ATS URL patterns;
- normalize employer domains;
- extract canonical job identifiers where available;
- avoid creating duplicate canonical jobs;
- prefer authoritative source URLs;
- preserve all source observations after canonical merge;
- measure incremental coverage contributed by meta-discovery;
- detect stale or expired vacancies before presenting them for application.

The product must distinguish:

```text
discovered_by = GOOGLE_JOBS
canonical_source = GREENHOUSE
preferred_apply_route = EMPLOYER_ATS
```

This distinction is mandatory for correct provenance, deduplication, and application routing.

# 8. Discovery Requirements

## FR-DISC-001: Scheduled multi-source discovery

The system shall run discovery across enabled sources according to source-specific schedules and constraints.

## FR-DISC-002: Incremental discovery

The system shall avoid reprocessing unchanged source jobs unnecessarily.

## FR-DISC-003: Partial failure isolation

Failure of one source shall not invalidate successful acquisition from other sources.

## FR-DISC-004: Source health

The system shall record:

- last attempted run;
- last successful run;
- fetched count;
- error state;
- challenge/cooldown state where relevant;
- duration.

## FR-DISC-005: Broad AI search portfolio

Search strategy shall cover genuine AI-related families including, but not limited to:

- AI Engineer;
- Applied AI Engineer;
- GenAI Engineer;
- LLM Engineer;
- RAG Engineer;
- AI Application Engineer;
- Agentic AI Engineer;
- AI Platform Engineer;
- ML Engineer where transition-compatible;
- NLP Engineer;
- MLOps / LLMOps where relevant;
- AI-enabled backend/full-stack roles;
- Azure AI roles;
- AI solutions engineering roles.

Search vocabulary is discovery-oriented. Final eligibility is determined downstream.

---

# 9. Canonicalization and Deduplication Requirements

## FR-DEDUP-001: Exact source deduplication

Repeated observations of the same source job ID must update the existing source observation.

## FR-DEDUP-002: Canonical URL matching

Known canonical URLs and ATS requisition identifiers must be used as strong duplicate evidence.

## FR-DEDUP-003: Cross-source entity resolution

Potential duplicate vacancies must be evaluated using:

- normalized company;
- normalized title;
- location overlap;
- description similarity;
- posting-date proximity;
- requisition identifiers;
- canonical URLs;
- employment type;
- source relationships.

## FR-DEDUP-004: Confidence-based merge

Cross-source merge decisions shall have confidence levels.

Ambiguous matches must remain separate or enter review rather than being destructively merged.

## FR-DEDUP-005: Provenance preservation

Merging source observations into one canonical job must not erase source provenance.

## FR-DEDUP-006: Preferred route selection

Where multiple application routes exist, the system shall choose or recommend a preferred route based on source authority, application friction, and reliability.

---

# 10. Eligibility and Intelligence Requirements

## FR-INT-001: AI relevance

The system shall distinguish genuine AI-related work from incidental use of AI terminology.

## FR-INT-002: Broad transition eligibility

Exact stack mismatch shall normally reduce fit score or priority rather than automatically reject genuine AI roles.

## FR-INT-003: Hard vetoes

The system may reject clearly unsuitable categories such as:

- non-software roles;
- unrelated support or operations roles;
- unrealistic executive roles;
- research-primary roles requiring credentials clearly outside target strategy;
- clearly ineligible geography;
- fraudulent or low-quality listings;
- closed jobs.

## FR-INT-004: Work-mode inference

The system shall classify:

```text
REMOTE
HYBRID
OFFICE
UNKNOWN
```

## FR-INT-005: Remote scope classification

Remote jobs shall be classified as:

```text
WORLDWIDE
INDIA_ELIGIBLE
APAC_ELIGIBLE
TIMEZONE_RESTRICTED_COMPATIBLE
COUNTRY_RESTRICTED_INELIGIBLE
UNKNOWN
```

## FR-INT-006: Pune location policy

Office, hybrid, and unknown work-mode roles must be Pune-compatible by default.

## FR-INT-007: Role families and subtracks

The system shall classify jobs into useful strategy segments, including:

```text
GENAI_LLM
AGENTIC_AI
APPLIED_AI
AI_PLATFORM
AI_FULLSTACK
AI_BACKEND
TRADITIONAL_ML
MLOPS_LLMOPS
NLP
OTHER_AI
```

The exact taxonomy may evolve, but historical mappings must remain analyzable.

## FR-INT-008: Evaluation explanation

Every scored job shown as actionable must expose:

- why it matches;
- major strengths;
- major gaps;
- red flags;
- location/remote assessment;
- score explanation;
- recommended action.

---

# 11. Prioritization Requirements

The system shall distinguish fit from urgency.

## Fit score factors may include

- AI relevance;
- candidate skill overlap;
- role transition plausibility;
- experience alignment;
- production AI relevance;
- Azure relevance;
- RAG/LLM/agentic relevance;
- engineering depth;
- seniority compatibility.

## Urgency factors may include

- fit score;
- priority tier;
- job freshness;
- closing date;
- application friction;
- source confidence;
- company desirability;
- scarcity;
- recruiter activity;
- manual due date.

The Today page should rank actions using action priority, not raw fit score alone.

---

# 12. Application Capability Model

Every actionable job shall resolve to one application capability:

```text
AUTO_APPLY
ASSISTED_APPLY
MANUAL_APPLY
EXTERNAL_REDIRECT
UNAVAILABLE
UNKNOWN
```

## AUTO_APPLY

The system can execute the application reliably with bounded failure semantics.

## ASSISTED_APPLY

The system can prepare data, answers, or navigation but requires user completion.

## MANUAL_APPLY

The system opens the application route and tracks completion manually.

## EXTERNAL_REDIRECT

The source only points to another authoritative route.

## UNAVAILABLE

The application is closed or cannot currently be completed.

## UNKNOWN

Capability requires inspection.

---

# 13. Manual Application Workflow

Manual application support is a first-class feature, not a fallback afterthought.

## 13.1 Manual session mode

The UI shall support a focused application session:

```text
START SESSION

Job 1 of N
Title
Company
Score
Priority
Freshness
Why it matches
Application route

[OPEN APPLICATION]

Return state:
[MARK APPLIED]
[SKIP]
[FAILED]
[SNOOZE]
[ADD NOTE]
```

## 13.2 Manual completion

Marking a job as applied shall:

- create or update an application record;
- create an application event;
- complete the manual action;
- record timestamp;
- preserve source and application route;
- remove it from pending application actions.

## 13.3 Session ordering

Manual session ordering should prioritize:

1. high urgency;
2. high priority;
3. fresh jobs;
4. lower application friction when otherwise similar.

---

# 14. Application Lifecycle Requirements

Canonical product lifecycle:

```text
DISCOVERED
REVIEWED
SHORTLISTED
READY_TO_APPLY
APPLYING
APPLIED
VIEWED
RECRUITER_CONTACT
EMPLOYER_SHORTLISTED
INTERVIEW_SCHEDULED
INTERVIEWING
OFFER
REJECTED
WITHDRAWN
STALE
```

Requirements:

- lifecycle transitions are event-backed;
- server reconciliation must be idempotent;
- terminal states must be protected;
- later-stage progression must not accidentally regress;
- manual corrections must be possible and auditable;
- stale is an operational classification and must not destroy actual last known recruiting state.

---

# 15. Follow-Up Requirements

The system shall create and manage follow-up actions.

Follow-up triggers may include:

- application age threshold;
- recruiter requested information;
- recruiter message awaiting reply;
- interview follow-up;
- referral follow-up;
- manually scheduled reminder.

The Today page shall show due follow-ups separately from new applications.

A follow-up action shall support:

```text
COMPLETE
SNOOZE
SKIP
ADD NOTE
OPEN RELATED APPLICATION
```

---

# 16. Interview Workspace Requirements

Interview functionality is a post-MVP product phase but part of the final product boundary.

When an application reaches recruiter contact, shortlist, or interview stage, the system should be able to create an interview preparation workspace.

## Interview workspace content

- company;
- role;
- JD snapshot;
- current job evaluation;
- candidate strengths;
- candidate gaps;
- likely technical areas;
- likely interview round types;
- company research notes;
- relevant project stories;
- relevant experience stories;
- coding preparation needs;
- system design preparation needs;
- AI/LLM/RAG/evaluation preparation needs;
- scheduled rounds;
- round notes;
- feedback;
- next action.

The interview module must use truthful candidate evidence and approved resume narrative.

---

# 17. User Interface Requirements

The first UI must be functional, information-dense, and simple.

No design-heavy work is required.

## 17.1 Today Page

Purpose: answer “What should I do now?”

Widgets:

- high-priority new jobs;
- pending auto applications;
- manual applications due;
- reviews required;
- follow-ups due;
- upcoming interviews;
- pipeline/source errors.

Primary table: Top Actions.

Columns:

```text
Action
Priority
Job / Application
Company
Score
Reason
Due / Age
Source
```

---

## 17.2 Job Inbox

Columns:

```text
Score
Priority
Urgency
Title
Company
Location
Work Mode
Remote Scope
Source Count
Freshness
Role Family
Application Method
Status
Actions
```

Filters:

- new only;
- score range;
- priority;
- source;
- India;
- global remote;
- role family;
- subtrack;
- work mode;
- remote eligibility;
- company;
- posted date;
- application method;
- reviewed/unreviewed.

Actions:

- view;
- shortlist;
- reject;
- watch;
- apply;
- open;
- add note.

---

## 17.3 Job Detail Page

Sections:

1. canonical job information;
2. source observations;
3. preferred application route;
4. why it matches;
5. why it may not match;
6. strengths;
7. gaps;
8. red flags;
9. score explanation;
10. geography eligibility;
11. application capability;
12. duplicate/related listings;
13. notes;
14. action history;
15. application timeline if applied.

---

## 17.4 Action Queue

Tabs:

```text
AUTO READY
MANUAL APPLY
NEEDS REVIEW
FOLLOW-UP
FAILED
SNOOZED
```

The queue must support batch selection where safe.

---

## 17.5 Applications Page

Required views:

- table;
- lifecycle board.

Table filters:

- lifecycle stage;
- source;
- role family;
- score band;
- age;
- company;
- application method;
- resume version.

---

## 17.6 Interview Center

Views:

- upcoming;
- preparation required;
- completed rounds;
- awaiting outcome;
- historical.

---

## 17.7 Analytics

Initial analytics:

- applications per day/week;
- response rate;
- interview rate;
- offer rate;
- source yield;
- source conversion;
- role-family performance;
- subtrack performance;
- score-band performance;
- application age;
- time to response;
- manual vs automatic performance;
- resume-version performance when data exists.

---

## 17.8 System / Runs

Controls:

```text
RUN DISCOVERY
RUN CLASSIFICATION
RUN DRY RUN
RUN APPLICATION BATCH
SYNC APPLICATION STATUS
GENERATE REPORT
```

Display:

- recent runs;
- stage status;
- errors;
- source health;
- last successful poll;
- jobs fetched;
- unique jobs;
- eligible jobs;
- selected jobs;
- application counters;
- challenge/cooldown state.

---

# 18. API Requirements

Initial workflow-oriented API:

```text
GET    /api/dashboard

GET    /api/jobs
GET    /api/jobs/{id}
POST   /api/jobs/{id}/shortlist
POST   /api/jobs/{id}/reject
POST   /api/jobs/{id}/watch
POST   /api/jobs/{id}/note

GET    /api/actions
POST   /api/actions/{id}/start
POST   /api/actions/{id}/complete
POST   /api/actions/{id}/skip
POST   /api/actions/{id}/snooze

GET    /api/applications
GET    /api/applications/{id}
PATCH  /api/applications/{id}
POST   /api/applications/{id}/events

GET    /api/interviews
GET    /api/interviews/{id}
POST   /api/interviews
PATCH  /api/interviews/{id}

POST   /api/runs/discovery
POST   /api/runs/classification
POST   /api/runs/dry-run
POST   /api/runs/apply
POST   /api/runs/reconcile
POST   /api/runs/report

GET    /api/runs
GET    /api/runs/{id}

GET    /api/analytics/funnel
GET    /api/analytics/sources
GET    /api/analytics/roles
GET    /api/analytics/scores
```

The API must expose workflows, not every internal function.

---

# 19. Persistence Requirements

## Minimum target tables

```text
sources
source_jobs
jobs
job_source_links
job_evaluations
job_actions
applications
application_events
interviews
interview_rounds
notes
tasks
pipeline_runs
pipeline_stage_runs
strategy_decisions
```

## Persistence rules

- SQLite remains the default database;
- migrations must be explicit;
- existing application history must be preserved;
- runtime state must remain excluded from public Git history;
- raw source payloads may be stored by reference rather than bloating relational rows;
- sensitive candidate data must remain local and ignored by Git;
- database backups must be possible before migrations.

---

# 20. Non-Functional Requirements

## NFR-001: Reliability

A source failure must not crash the entire discovery cycle.

## NFR-002: Idempotency

Repeated discovery and reconciliation must not create duplicate jobs, applications, or lifecycle events.

## NFR-003: Auditability

Important decisions and transitions must be explainable through stored evaluation, action, run, and event data.

## NFR-004: Performance

Cheap filters must run before expensive detail fetching and LLM inference.

## NFR-005: Local resource control

LLM use must be concentrated on cases where deterministic processing is insufficient.

## NFR-006: Security

The system must not commit:

- credentials;
- API keys;
- session tokens;
- cookies;
- candidate evidence;
- application history;
- questionnaire telemetry containing private data;
- raw application responses;
- local databases.

## NFR-007: Recoverability

Database migration and destructive operations require backups or reversible migration paths.

## NFR-008: Testability

Source adapters, normalization, deduplication, eligibility, scoring, action generation, lifecycle transitions, and API workflows must be independently testable.

## NFR-009: Observability

Every pipeline run must record:

- run ID;
- timestamps;
- source/stage status;
- counts;
- errors;
- completion status.

## NFR-010: Maintainability

New source integrations must not require source-specific conditions scattered through the domain and UI layers.

---

# 21. Delivery Plan

## Phase 0 — Freeze and Baseline

**Estimated focused effort:** 0.5–1 day

Tasks:

- tag current stable system;
- back up current SQLite state;
- run complete regression suite;
- run compile validation;
- run static hygiene checks;
- perform a very small live Naukri canary;
- verify application result interpretation;
- verify ledger writes;
- run server reconciliation;
- document known current failures.

Deliverable:

```text
v1-naukri-engine
```

Exit criteria:

- regression baseline recorded;
- current pipeline behavior known;
- rollback point exists.

---

## Phase 1 — Canonical Domain Model and Source Boundary

**Estimated focused effort:** 2–3 days

Tasks:

- introduce canonical job model;
- introduce source observation model;
- introduce evaluation model;
- define source adapter protocol;
- create source capability model;
- wrap current Naukri search/details/apply behavior in adapter boundaries;
- add Naukri-to-canonical mapper;
- adapt downstream classifier incrementally;
- preserve old interfaces temporarily where required.

Exit criteria:

- Naukri pipeline still works;
- canonical jobs can be created;
- source provenance is preserved;
- downstream evaluation can process canonical jobs;
- current regression suite passes.

---

## Phase 2 — Database v2

**Estimated focused effort:** 2 days

Tasks:

- create migrations;
- add jobs;
- add source jobs;
- add job-source mapping;
- add evaluations;
- add actions;
- migrate application relationships;
- migrate manual queue from JSON;
- preserve historical application records.

Exit criteria:

- discovery state persists independently from applications;
- one canonical job can map to multiple sources;
- manual actions persist in SQLite;
- existing history remains intact.

---

## Phase 3 — API Layer

**Estimated focused effort:** 2 days

Tasks:

- add FastAPI application;
- dashboard endpoints;
- jobs endpoints;
- actions endpoints;
- applications endpoints;
- run-control endpoints;
- analytics summary endpoints;
- background run state handling appropriate for local use.

Exit criteria:

- core workflows are operable through API;
- API tests exist;
- pipeline execution remains usable from CLI.

---

## Phase 4 — Basic Operational UI

**Estimated focused effort:** 3–4 days

Build only:

- Today;
- Job Inbox;
- Job Detail;
- Action Queue;
- Applications;
- System / Runs.

Explicitly defer:

- elaborate design system;
- animations;
- complex mobile work;
- public authentication;
- advanced charts.

Exit criteria:

- normal Naukri-based daily operation can be performed from UI;
- user can review, shortlist, reject, open, mark applied, inspect applications, and run core workflows.

This is the first major usable-product milestone.

---

## Phase 5 — First External Source Wave

**Estimated focused effort:** 4–7 days

Initial targets:

1. Greenhouse;
2. Lever;
3. Ashby;
4. Wellfound;
5. Himalayas;
6. Google Jobs / search-based meta-discovery;
7. original-source and ATS resolution.

Implementation sequence:

```text
Wave 1
    Greenhouse
    Lever
    Ashby

Wave 2
    Wellfound
    Himalayas

Wave 3
    Google Jobs / Search Discovery
            ↓
    Original Source Resolver
            ↓
    ATS Fingerprinting
            ↓
    Canonical Job Matching
```

For direct sources:

```text
discover
normalize
persist
deduplicate
evaluate
display
manual apply
track
```

For Google/search meta-discovery:

```text
discover observation
resolve original source
identify employer or ATS
canonicalize URL
match existing canonical job
merge provenance
evaluate only if genuinely new
open preferred original application route
track
```

No Google/search-specific auto-apply requirement exists.

The purpose of this integration is discovery coverage, not automation against the aggregation layer.

Exit criteria:

- external jobs enter the same inbox;
- source provenance remains visible;
- duplicates can merge;
- evaluation is source-independent;
- preferred apply route opens correctly;
- Mark Applied creates application state;
- meta-discovery observations resolve to canonical sources where possible;
- Google/search-derived duplicates do not create duplicate actionable jobs.

---

## Phase 6 — India Coverage Expansion

**Estimated focused effort:** 3–6 days

Targets:

- LinkedIn discovery;
- Instahyre;
- Cutshort;
- Hirist.

Acquisition mechanisms may differ:

- public endpoints;
- structured pages;
- browser-assisted discovery;
- email ingestion;
- manual import;
- search discovery.

Do not force all sources into one transport mechanism.

---

## Phase 7 — Remote Coverage Expansion

**Estimated focused effort:** 2–4 days

Targets:

- Remote OK;
- We Work Remotely;
- Remotive;
- YC Jobs;
- selected AI-specific boards.

Required parallel feature:

- remote-scope classifier;
- India eligibility;
- APAC eligibility;
- timezone compatibility;
- country restriction detection.

---

## Phase 8 — Follow-Up and Interview Workflow

**Estimated focused effort:** 3–5 days

Tasks:

- follow-up task generation;
- stale application policies;
- recruiter-response tasks;
- interview objects;
- interview rounds;
- preparation workspace;
- JD snapshot;
- gap extraction;
- preparation checklist.

---

## Phase 9 — Analytics and Strategy Calibration

**Estimated focused effort:** 2–4 days

Tasks:

- source unique-yield analytics;
- source conversion;
- role-family conversion;
- score calibration;
- application method comparison;
- resume version tracking;
- adaptive strategy review.

Do not expand adaptation until outcome data volume is sufficient.

---

# 22. Delivery Timeline Interpretation

Approximate total for the broader product:

```text
19–29 focused development days
```

This is not a waiting period before job applications begin.

Operational rollout:

```text
DAY 1
Validate and use current Naukri pipeline.

DAYS 2–7
Canonical domain, persistence evolution, API.
Continue real applications.

DAYS 8–11
Basic UI.
Begin daily operation through unified interface.

DAYS 12–18
ATS and first external source wave.
Begin unified multi-source inbox.

DAY 19+
Expand India and remote coverage based on measured gaps.
Add follow-up and interview workflow.
```

The first genuinely useful unified product should be achievable in approximately 8–12 focused development days because the core intelligence and Naukri execution engine already exist.

---

# 23. Prioritization Framework for Future Work

Every proposed feature should be scored against:

1. Does it discover materially more unique eligible jobs?
2. Does it reduce time spent on repetitive job-search work?
3. Does it improve application quality?
4. Does it reduce missed or duplicate applications?
5. Does it improve follow-up discipline?
6. Does it improve interview preparation?
7. Does it produce data that changes a real decision?
8. Can it be delivered without destabilizing the working application engine?

Low-value engineering should be deferred even if technically interesting.

---

# 24. Key Product Metrics

## Discovery metrics

- jobs discovered;
- unique jobs;
- eligible jobs;
- high-priority jobs;
- duplicate ratio;
- stale ratio;
- source unique contribution.

## Action metrics

- pending actions;
- action completion time;
- discovery-to-review time;
- discovery-to-application time;
- manual queue age;
- application completion rate.

## Application metrics

- applications per week;
- auto vs manual applications;
- response rate;
- recruiter-contact rate;
- shortlist rate;
- interview rate;
- offer rate;
- rejection rate;
- stale rate;
- time to first response.

## Strategy metrics

- conversion by source;
- conversion by role family;
- conversion by subtrack;
- conversion by score band;
- conversion by resume version;
- conversion by application method.

Metrics must not become vanity dashboards. They exist to support decisions.

---

# 25. Testing Strategy

## Unit tests

Required for:

- source mapping;
- canonicalization;
- company normalization;
- title normalization;
- location normalization;
- remote-scope classification;
- eligibility;
- vacancy fingerprinting;
- duplicate similarity;
- evaluation guards;
- action generation;
- lifecycle transitions;
- retry classification.

## Contract tests

Each source adapter should have a common contract suite validating declared capabilities.

## Fixture tests

Sanitized source responses should be stored as regression fixtures where legally and operationally appropriate.

## Integration tests

Required workflows:

```text
source observation
→ canonical job
→ evaluation
→ action
→ application
→ event
→ analytics
```

## Regression tests

Existing Naukri behavior must remain protected during refactor.

## Live canaries

Live tests must be:

- explicitly invoked;
- bounded;
- excluded from normal unit suite;
- safe by default;
- capable of dry-run execution.

---

# 26. Security and Public Repository Requirements

The repository is public. Therefore:

- `.env` and `.env.*` remain ignored except `.env.example`;
- database files remain ignored;
- search caches remain ignored;
- raw jobs and scored jobs remain ignored;
- application logs remain ignored;
- questionnaire telemetry remains ignored;
- raw responses remain ignored;
- token pools remain ignored;
- session artifacts remain ignored;
- candidate evidence containing private information must not be committed.

Before major public releases:

```text
gitleaks detect --source . --verbose
```

or equivalent secret scanning should remain part of release hygiene.

No documentation example may contain real credentials, tokens, private application data, or candidate-sensitive evidence.

---

# 27. Licensing Constraint

The repository originated from an upstream project history and currently requires deliberate license review before adding a license.

Rules:

- do not add MIT, Apache-2.0, GPL, or another license merely because the repository is public;
- inspect upstream repository licensing and authorship history;
- preserve required attribution;
- distinguish rights over original upstream code from newly authored extensions;
- if licensing remains unclear, public visibility does not automatically grant reuse rights.

Licensing work is separate from product functionality but must be resolved before presenting the repository as freely reusable open source.

---

# 28. Product Risks

## Risk 1: Building instead of applying

Mitigation:

- maintain real application cadence throughout development;
- use current Naukri engine immediately;
- time-box product phases;
- stop feature work that does not improve near-term job-search outcomes.

## Risk 2: Source integration fragility

Mitigation:

- source adapter isolation;
- per-source health;
- partial failure handling;
- independent schedules;
- source-specific tests;
- no assumption that every source supports automation.

## Risk 3: Duplicate explosion

Mitigation:

- canonical model;
- source observations;
- confidence-based entity resolution;
- provenance preservation.

## Risk 4: Remote-job false positives

Mitigation:

- explicit remote scope;
- country eligibility;
- timezone compatibility;
- unknown state rather than optimistic assumptions.

## Risk 5: Over-automation

Mitigation:

- capability model;
- conservative response semantics;
- manual review;
- bounded retries;
- dry-run and canary modes.

## Risk 6: Strategy overfitting

Mitigation:

- minimum sample thresholds;
- priors;
- time decay;
- exploration fraction;
- human-visible strategy decisions.

## Risk 7: Architecture rewrite spiral

Mitigation:

- strangler-style refactor;
- wrap current Naukri behavior;
- migrate boundaries incrementally;
- preserve CLI during API/UI build;
- require regression green before phase completion.

---

# 29. Explicit Non-Goals Until Proven Necessary

Do not build these during the initial product program:

- microservices;
- Kubernetes;
- Kafka;
- distributed queues;
- multi-tenant authentication;
- payment system;
- generic onboarding wizard;
- public SaaS deployment;
- native mobile application;
- browser extension;
- universal web auto-apply engine;
- autonomous recruiter messaging;
- arbitrary resume generation;
- cover letters for every application;
- vector database solely because the product contains AI;
- agent orchestration framework without a specific unmet workflow requirement.

---

# 30. Definition of MVP

The MVP is not “multiple sources.”

The MVP is achieved when the user can:

1. run discovery;
2. see discovered Naukri jobs in a UI;
3. filter and sort jobs;
4. inspect evaluation explanations;
5. shortlist or reject jobs;
6. see an action queue;
7. execute or approve bounded auto applications;
8. open manual application routes;
9. mark manual applications complete;
10. view all applications;
11. sync Naukri application state;
12. inspect run health and failures.

This MVP should be built before broad source expansion.

---

# 31. Definition of Multi-Source V1

Multi-Source V1 is achieved when:

- Naukri plus at least three materially useful external source families feed the canonical store;
- one canonical job can have multiple source observations;
- cross-source duplicates are controlled;
- all sources use the same evaluation engine;
- manual application works from one action queue;
- applications are tracked independently of source;
- source contribution is measurable.

---

# 32. Definition of Final Personal Product

The product vision is substantially complete when the user can operate this loop:

```text
CAREER WORKFLOW
│
├── DISCOVER
│   ├── India portals
│   ├── global remote boards
│   ├── ATS sources
│   └── target companies
│
├── DECIDE
│   ├── normalize
│   ├── deduplicate
│   ├── evaluate eligibility
│   ├── score fit
│   ├── assign priority
│   └── calculate urgency
│
├── ACT
│   ├── auto apply
│   ├── assisted apply
│   ├── manual session
│   └── follow up
│
├── TRACK
│   ├── applications
│   ├── recruiter contacts
│   ├── shortlists
│   ├── interviews
│   ├── rejections
│   └── offers
│
├── PREPARE
│   ├── JD analysis
│   ├── skill gaps
│   ├── company research
│   ├── project stories
│   ├── experience stories
│   └── interview rounds
│
└── LEARN
    ├── source performance
    ├── role performance
    ├── score calibration
    ├── application-method performance
    ├── resume performance
    └── funnel analytics
```

---

# 33. Required Implementation Sequence

The implementation sequence is a product constraint:

```text
1. Protect current working system
2. Validate Naukri live canary
3. Introduce canonical domain model
4. Introduce source adapter boundary
5. Evolve database
6. Add API
7. Build minimal operational UI
8. Start daily UI-based use
9. Add ATS source family
10. Add startup/remote source
11. Add India source coverage
12. Harden cross-source deduplication
13. Add follow-up workflow
14. Add interview workspace
15. Expand sources based on measured coverage gaps
16. Calibrate analytics and adaptive strategy using real outcomes
```

Do not begin by adding many sources directly into the existing Naukri-oriented model.

---

# 34. Development Rules for AI Coding Assistants

Any AI assistant working on this repository must follow these rules:

1. Inspect the actual repository before proposing code.
2. Treat this document as product direction, not proof that every described module already exists.
3. Do not invent existing files, functions, schemas, or tests.
4. Preserve working behavior before refactoring.
5. Make incremental, testable changes.
6. Do not perform large rewrites unless explicitly approved.
7. Keep source-specific behavior behind adapters.
8. Keep canonical domain models source-independent.
9. Keep candidate evaluation separate from source job data.
10. Keep job state separate from application state.
11. Preserve source provenance.
12. Preserve historical application data.
13. Add migrations for schema changes.
14. Add tests with every behavioral change.
15. Do not weaken safety controls to make tests pass.
16. Do not fabricate candidate qualifications.
17. Do not commit secrets or runtime data.
18. Keep CLI workflows functional until UI/API replacements are proven.
19. Prefer simple local architecture over unnecessary infrastructure.
20. Stop after each coherent implementation phase and validate before continuing.

---

# 35. Living Decision Log

This section should be updated as implementation decisions are finalized.

| Decision | Current position | Status |
|---|---|---|
| Deployment model | Local-first | Decided |
| Primary DB | SQLite | Decided |
| Backend | Existing Python system + FastAPI layer | Planned |
| Frontend | Angular or React; choose for implementation speed and maintainability | Open |
| Naukri engine | Preserve and wrap, do not rewrite | Decided |
| Source model | Adapter-based | Decided |
| Job model | Canonical job + source observations | Decided |
| Manual queue | Move from JSON to SQLite action model | Planned |
| Auto-apply scope | Source-specific, conservative | Decided |
| Remote eligibility | Explicit scope classification required | Decided |
| Adaptive strategy | Evidence-gated and conservative | Decided |
| SaaS scope | Out of scope | Decided |
| License | Requires upstream license review | Open |

---

# 36. Immediate Next Milestone

The next milestone is not “add more job boards.”

The next milestone is:

## Milestone: Unified Product Foundation

Deliver:

- stable baseline tag;
- canonical job domain model;
- source observation model;
- source adapter protocol;
- Naukri adapter wrapper;
- database v2 schema and migrations;
- database-backed action queue;
- minimal FastAPI workflow layer;
- basic operational UI.

Completion condition:

> The user can run the existing Naukri workflow, review and act on jobs, track applications, and inspect run health through the new unified product architecture without losing current functionality.

Only after this milestone should external source expansion become the primary development stream.

---

# 37. Product North Star

The product must optimize one thing:

> Put the highest-value job-search action in front of the user at the correct time, with enough context to execute it quickly and with complete state tracking afterward.

Everything else is supporting infrastructure.
