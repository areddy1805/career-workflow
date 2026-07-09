Career Workflow Control Center

Business Requirements Document and Product Requirements Document

Document: CAREER_WORKFLOW_UI_PRD_BRD.md
Product: Career Workflow Control Center
Parent System: Career Workflow / Naukri Application Engine
Version: 1.0
Status: Implementation Specification
Delivery Constraint: One working day
Primary User: Repository owner
Deployment Model: Local-only
UI Framework: Streamlit
Product Principle: Thin operational interface over the existing system

⸻

1. Executive Summary

Career Workflow already contains a substantial backend system for AI-related job discovery, classification, ranking, selection, application execution, questionnaire resolution, lifecycle tracking, reconciliation, analytics, and adaptive strategy.

The current limitation is operational usability.

Most system capabilities are accessed through:

* CLI commands;
* environment variables;
* terminal output;
* JSON run summaries;
* CSV files;
* SQLite queries;
* Python reports;
* logs and runtime artifacts.

This creates unnecessary friction during daily job-search operation.

The purpose of the Career Workflow Control Center is to provide a lightweight local interface for operating and observing the existing system.

The UI must enable the user to:

* understand current job-search state;
* run the existing pipeline safely;
* inspect pipeline execution;
* browse discovered and classified jobs;
* inspect selected jobs;
* view application history;
* track recruiting lifecycle state;
* inspect manual-review cases;
* maintain a simple queue for external/manual applications;
* view existing analytics;
* inspect relevant operational settings.

The UI is explicitly not a new product architecture.

It must not introduce:

* a new backend service;
* REST APIs;
* FastAPI;
* React;
* Angular;
* authentication;
* cloud deployment;
* source adapters;
* canonical multi-source schemas;
* distributed workers;
* task queues;
* Redis;
* Celery;
* WebSockets;
* database redesign;
* multi-user support.

The implementation must remain a thin local operational layer over the existing Career Workflow system.

⸻

2. Business Context

2.1 Current Situation

Career Workflow currently provides a mature Naukri-centered application engine.

The system includes capabilities across:

DISCOVERY
    ↓
ACQUISITION
    ↓
NORMALIZATION
    ↓
DEDUPLICATION
    ↓
AI RELEVANCE CLASSIFICATION
    ↓
LOCATION AND WORK-MODE POLICY
    ↓
DETAIL ENRICHMENT
    ↓
FIT SCORING
    ↓
DETERMINISTIC CALIBRATION
    ↓
RANKING
    ↓
DIVERSITY CONTROL
    ↓
SELECTION
    ↓
APPLICATION EXECUTION
    ↓
QUESTIONNAIRE RESOLUTION
    ↓
OUTCOME INTERPRETATION
    ↓
PERSISTENT TRACKING
    ↓
SERVER RECONCILIATION
    ↓
LIFECYCLE ANALYTICS
    ↓
ADAPTIVE STRATEGY

The backend is operationally capable but CLI-oriented.

The immediate objective is not to expand the source architecture.

The immediate objective is to make the existing system practical for daily use.

⸻

2.2 Business Problem

The current workflow requires the user to remember and execute multiple commands, inspect multiple outputs, and mentally combine information from different storage locations.

Typical current interaction:

run pipeline command
        ↓
read terminal output
        ↓
find run summary
        ↓
inspect job CSV
        ↓
inspect application ledger
        ↓
run monitor
        ↓
run analytics report
        ↓
manually remember external jobs
        ↓
manually remember which applications need attention

This produces several problems:

Operational friction

Routine actions require terminal knowledge and command recall.

Fragmented visibility

Pipeline state, jobs, applications, lifecycle state, and analytics are not visible in one place.

Manual job fragmentation

Jobs discovered outside Naukri have no simple unified operational queue.

Review friction

Failures and manual-review cases are difficult to inspect systematically.

Poor daily usability

The backend can perform substantial work, but the user lacks a practical daily control surface.

⸻

3. Business Objective

Build a local control center that converts the existing Career Workflow backend into a usable daily job-search operating system.

The UI must reduce the daily workflow to:

OPEN UI
    ↓
CHECK DASHBOARD
    ↓
RUN PIPELINE
    ↓
INSPECT RESULTS
    ↓
REVIEW APPLICATIONS
    ↓
PROCESS MANUAL QUEUE
    ↓
PROCESS REVIEW QUEUE
    ↓
RECONCILE OUTCOMES
    ↓
CHECK ANALYTICS
    ↓
CLOSE SYSTEM

The UI must improve operation of the existing engine without materially changing the engine itself.

⸻

4. Success Definition

The one-day implementation is successful when the user can perform the following from one local interface:

1. View the latest operational state.
2. Start a dry pipeline run.
3. Start a constrained live pipeline run.
4. See whether the pipeline is idle, running, successful, or failed.
5. View the latest run summary.
6. Browse available job data.
7. Browse application ledger data.
8. Filter applications by lifecycle state.
9. inspect manual-review cases.
10. Add and update manually discovered jobs.
11. Open external job application pages.
12. Mark external jobs as applied or skipped.
13. Run or trigger application reconciliation.
14. View useful application analytics.
15. Inspect relevant runtime configuration safely.

The UI does not need to be visually perfect.

It must be:

* functional;
* understandable;
* safe;
* fast enough;
* operationally useful;
* maintainable;
* bounded.

⸻

5. Non-Goals

The following are explicitly outside scope.

5.1 No Backend Rewrite

Do not rewrite existing modules to make them more convenient for the UI.

Small adapters and query helpers are acceptable.

Large refactoring is prohibited.

⸻

5.2 No Multi-Source Architecture

Do not implement:

* LinkedIn ingestion;
* Google Jobs ingestion;
* Indeed ingestion;
* Instahyre ingestion;
* Wellfound ingestion;
* Cutshort ingestion;
* company career-page crawling;
* source adapter interfaces;
* source registries;
* canonical cross-source jobs.

External jobs enter the UI manually in V1.

⸻

5.3 No Web Application Architecture

Do not build:

frontend
    ↓ HTTP
backend API
    ↓
service layer
    ↓
database

Use:

Streamlit
    ↓
thin UI helpers
    ↓
existing modules / subprocess commands / SQLite

⸻

5.4 No Authentication

The application is local and single-user.

No:

* login page;
* passwords;
* OAuth;
* sessions;
* roles;
* permissions.

⸻

5.5 No Cloud Deployment

Do not deploy the UI.

It runs locally:

streamlit run ui/app.py

⸻

5.6 No Real-Time Infrastructure

No:

* WebSockets;
* event buses;
* background worker framework;
* distributed execution;
* task queues.

Simple process state and polling are sufficient.

⸻

5.7 No Database Migration Program

Do not redesign the existing application ledger.

The only permitted persistence extension is a small isolated manual-job queue if no suitable existing table already exists.

⸻

6. Product Scope

The application consists of seven primary operational areas:

1. Dashboard
2. Pipeline
3. Jobs
4. Applications
5. Manual Queue
6. Review Queue
7. Analytics

Settings may exist as an eighth read-only page if time permits.

Priority order:

P0
Dashboard
Pipeline
Applications
Manual Queue
P1
Jobs
Review Queue
P2
Analytics
Settings
Visual polish

If time becomes constrained, P2 work must be dropped before P0 functionality is compromised.

⸻

7. User Profile

The application has one user.

The user:

* owns the repository;
* runs the application locally;
* understands the job-search strategy;
* wants broad AI-related job coverage;
* wants office and hybrid opportunities only when Pune-compatible;
* wants remote opportunities globally;
* uses the Naukri engine for automated discovery and supported application flows;
* manually discovers and applies to external opportunities;
* needs a single place to track operational job-search state;
* values application throughput but does not want automation to interfere with interview preparation.

The UI should optimize for speed of operation, not general-market usability.

⸻

8. Product Principles

8.1 Existing System First

The UI must expose existing capabilities before creating new ones.

⸻

8.2 Read Before Write

Prefer read-only visibility first.

Mutation should only be added where operationally necessary.

⸻

8.3 Safe Execution

Live application execution must be visibly different from dry-run execution.

⸻

8.4 Explicit State

The UI must distinguish:

IDLE
RUNNING
SUCCESS
PARTIAL
FAILED

Do not imply success merely because a process started.

⸻

8.5 No Hidden Automation

Every live pipeline execution must require deliberate user action.

⸻

8.6 Operational Density Over Decoration

Prioritize:

* useful tables;
* filters;
* metrics;
* state;
* actions.

Avoid spending the implementation day on visual effects.

⸻

8.7 Graceful Missing Data

The UI must not crash because:

* a CSV does not exist;
* the ledger is empty;
* no run artifact exists;
* analytics have insufficient samples;
* a field is null;
* a cache is absent.

Show an empty state instead.

⸻

9. Information Architecture

Recommended navigation:

Career Workflow
├── Dashboard
├── Pipeline
├── Jobs
├── Applications
├── Manual Queue
├── Review Queue
├── Analytics
└── Settings

If implementation speed requires simplification:

Career Workflow
├── Dashboard
├── Pipeline
├── Jobs
├── Applications
├── Manual & Review
└── Analytics

The simpler six-page structure is acceptable.

⸻

10. Functional Requirements

FR-001: Dashboard

Purpose

Provide immediate understanding of the current job-search system state.

Required Metrics

Display, when available:

Jobs acquired
Jobs classified
Jobs selected
Applications submitted
Already applied
Failures
Manual-review cases
Submitted lifecycle count
Viewed count
Shortlisted count
Interview count
Rejected count
Offer count

Not all metrics need to come from the same data source.

The UI query layer may aggregate:

* latest run summary;
* application ledger;
* lifecycle state;
* manual queue.

Latest Run Section

Display:

Run ID
Overall status
Started at
Completed at
Duration
Acquired
Classified
Selected
Attempted
Submitted
Already applied
Failed
Manual review

Pipeline Health Section

Display:

Current process state
Last successful run
Last failed run, if available
Dry-run/live status of last run
Search challenge state, if accessible
Search cooldown state, if accessible

Dashboard Actions

Required:

Go to Pipeline
Refresh Data

Optional:

Run Reconciliation

Do not overload the dashboard with every execution action.

⸻

11. Pipeline Page Requirements

FR-002: Pipeline Control

Purpose

Provide a safe UI for executing the existing pipeline.

Inputs

Required controls:

Execution Mode:
    Dry Run
    Live
Maximum Applications:
    integer input

Suggested defaults:

Dry Run: 500
Live Canary: 3
Controlled Live Run: user-selected

The UI must not silently convert dry mode into live mode.

Required Actions

Run Pipeline
Refresh Status

Optional preset buttons:

Broad Dry Run
Live Canary
Controlled Batch

Execution Strategy

Preferred one-day implementation:

Streamlit UI
    ↓
subprocess.Popen()
    ↓
existing run_pipeline.py
    ↓
existing run artifacts

Do not duplicate pipeline orchestration logic inside Streamlit.

Example conceptual command construction:

Dry:
APPLICATION_DRY_RUN=true python run_pipeline.py --max-applications N
Live:
APPLICATION_DRY_RUN=false python run_pipeline.py --max-applications N

Use sys.executable rather than assuming the executable name python.

Safety Requirements

Before live execution:

* clearly display LIVE mode;
* show application ceiling;
* require a confirmation checkbox;
* disable the Run button until confirmation is checked.

Example:

Mode: LIVE
Maximum applications: 3
[ ] I understand this run may submit real applications.
[ RUN LIVE PIPELINE ]

This is sufficient. Do not build modal systems.

⸻

FR-003: Pipeline Process State

The UI must represent:

IDLE
RUNNING
SUCCESS
FAILED

If the existing run summary supports partial states, also expose:

PARTIAL

While running, display:

Process ID
Start time
Elapsed time
Latest known output

A simple text output area is acceptable.

Do not build sophisticated log streaming.

A basic implementation may:

1. start the subprocess;
2. store PID/state in session state or a small runtime state file;
3. capture stdout/stderr into a log file;
4. refresh the UI manually or periodically;
5. read the latest run summary artifact after completion.

⸻

FR-004: Stage Status

When run-summary information is available, display:

Stage	Status
Preflight	SUCCESS
Acquisition	SUCCESS
Classification	SUCCESS
Selection	SUCCESS
Application	SUCCESS
Reconciliation	SUCCESS
Strategy	SUCCESS
Report	SUCCESS

If stage progress is only available after completion, do not invent real-time stage tracking.

Display completed summary state only.

⸻

12. Jobs Page Requirements

FR-005: Job Browser

Purpose

Allow inspection of jobs known to the existing system.

Data Sources

Use existing available data, potentially including:

* raw job artifacts;
* scored job artifacts;
* latest pipeline outputs;
* ledger metadata;
* search cache where appropriate.

Do not create a new canonical jobs database merely for the UI.

Required Columns

Display available subset of:

Job ID
Title
Company
Location
Experience
Score
Priority
Subtrack
Source
Status
Applied state

Required Filters

Implement only filters supported by actual available data.

Priority filters:

Search text
Minimum score
Company
Location
Priority
Subtrack
Application state

Job Detail

Selecting a job should show, where available:

Title
Company
Location
Experience
Salary
Skills
Description
Score
Priority
Subtrack
Source
Application state

Optional:

score explanation
AI relevance evidence
red flags
location decision
selection reason

Do not block V1 waiting for all optional fields.

Actions

Where a usable job URL exists:

Open Job

Where appropriate:

Add to Manual Queue

Do not implement application execution directly from arbitrary table rows unless the existing backend already exposes a safe single-job execution path and integration is trivial.

⸻

13. Applications Page Requirements

FR-006: Application Ledger Browser

Purpose

Provide a usable view over the existing application ledger.

Data Source

Existing SQLite ledger.

No duplicate application database.

Required Columns

Display available fields:

Job ID
Title
Company
Location
Score
Priority
Subtrack
Source
Local status
Lifecycle stage
Applied date
Last update
Age

Lifecycle Filters

Support:

All
Submitted
Viewed
Shortlisted
Interview
Rejected
Offer
Unknown

Only expose stages actually represented by the current lifecycle model.

Additional Filters

Company
Subtrack
Priority
Minimum score
Application date range

Implement only those that are inexpensive.

Detail View

Show:

Job identity
Application metadata
Local execution status
Server status
Normalized lifecycle stage
Relevant timestamps
Failure information

If status events are accessible:

Status History
2026-07-01  Submitted
2026-07-03  Viewed
2026-07-05  Shortlisted

Status history is P1, not P0.

⸻

14. Manual Queue Requirements

FR-007: Manual Job Capture

Purpose

Provide one place to track jobs discovered outside automated Naukri acquisition.

Sources may include:

LinkedIn
Google Jobs
Instahyre
Wellfound
Cutshort
Indeed
Company Careers
Recruiter
Referral
Other

This is a tracking queue, not source integration.

Minimum Data Model

If no existing suitable persistence structure exists, create an isolated SQLite table:

CREATE TABLE IF NOT EXISTS manual_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    source TEXT NOT NULL,
    source_url TEXT,
    status TEXT NOT NULL DEFAULT 'DISCOVERED',
    priority TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    applied_at TEXT
);

Do not modify the existing application ledger schema merely to support this page.

Allowed States

DISCOVERED
SHORTLISTED
TO_APPLY
APPLIED
SKIPPED
EXPIRED

Required Actions

Add Job
Edit Job
Open Job URL
Change Status
Mark Applied
Mark Skipped

Delete is optional.

Prefer status transitions over deletion.

Add Job Form

Fields:

Title *
Company *
Location
Source *
Job URL
Priority
Notes

Keep the form fast.

No AI classification is required for manual jobs in V1.

⸻

15. Review Queue Requirements

FR-008: Operational Review Queue

Purpose

Surface cases that require human attention.

Potential sources include:

manual review application outcome
unresolved questionnaire
unknown response
failed application
terminal failure
retry exhausted
external apply requirement

The implementation must use actual existing states and artifacts.

Do not invent a new workflow engine.

Required Display

Where data exists:

Job
Company
Review reason
Failure type
Timestamp
Current state
Relevant details

Required Actions

At minimum:

Open Job
View Details

If straightforward:

Mark Reviewed
Mark Manually Applied
Mark Skipped

Do not implement complex retry controls unless the existing execution layer exposes a clearly safe reusable operation.

⸻

16. Analytics Requirements

FR-009: Analytics Dashboard

Purpose

Visualize existing application intelligence.

Reuse current analytics logic wherever practical.

Metrics

Display available:

Total applications
Response rate
Interview rate
Offer rate
Average time to first response
Application velocity
Application age distribution

Segment Views

Display where available:

Performance by priority
Performance by subtrack
Performance by score band
Lifecycle distribution

Charts

Use simple Streamlit-native charts or Plotly only if already available.

Do not spend significant time on chart customization.

The purpose is decision visibility.

⸻

17. Settings Requirements

FR-010: Operational Configuration View

This page is optional.

Display safe operational configuration such as:

APPLICATION_DRY_RUN
MAX_APPLICATIONS_PER_RUN
AUTO_APPLY_MIN_SCORE
DETAIL_FETCH_BUDGET
MAX_APPLICATIONS_PER_COMPANY_PER_RUN
MAX_ROLE_FAMILY_PER_COMPANY
MAX_PER_VACANCY_FINGERPRINT
ADAPTIVE_STRATEGY_ENABLED
ADAPTIVE_MIN_APPLICATIONS
ADAPTIVE_MIN_RESPONSES
SEARCH_CHALLENGE_COOLDOWN_MINUTES

Do not display:

NAUKRI_PASSWORD
OMLX_API_KEY
Bearer tokens
Cookies
Session data
nkparam values

V1 settings should preferably be read-only.

Do not build .env editing unless all higher-priority functionality is complete.

⸻

18. Technical Architecture

18.1 Target Architecture

┌───────────────────────────────────────────────┐
│              Streamlit Control Center         │
│                                               │
│ Dashboard                                     │
│ Pipeline                                      │
│ Jobs                                          │
│ Applications                                  │
│ Manual Queue                                  │
│ Review Queue                                  │
│ Analytics                                     │
└──────────────────────┬────────────────────────┘
                       │
          ┌────────────┼─────────────┐
          │            │             │
          ▼            ▼             ▼
    Query Helpers   Process Runner  Existing
          │            │           Analytics
          │            │
          ▼            ▼
      SQLite       run_pipeline.py
      CSV/JSON     monitor_applications.py
      Artifacts    application_report.py

⸻

18.2 Recommended Directory Structure

ui/
├── app.py
├── db.py
├── queries.py
├── pipeline_runner.py
├── artifact_reader.py
├── manual_queue.py
└── pages/
    ├── dashboard.py
    ├── pipeline.py
    ├── jobs.py
    ├── applications.py
    ├── manual_queue.py
    ├── review_queue.py
    ├── analytics.py
    └── settings.py

For a one-day build, an even smaller structure is acceptable:

ui/
├── app.py
├── data.py
├── runner.py
└── pages/
    ├── dashboard.py
    ├── pipeline.py
    ├── jobs.py
    ├── applications.py
    ├── manual_queue.py
    └── analytics.py

Prefer the smaller structure unless files become unwieldy.

⸻

19. Data Access Strategy

19.1 Existing Ledger

Read existing application state directly from SQLite using read queries.

Do not duplicate ledger records into UI-specific storage.

⸻

19.2 Run Summaries

Read existing generated run summaries from:

artifacts/runs/

The implementation must inspect the actual repository and determine:

* filename format;
* JSON schema;
* ordering;
* latest-run identification.

Do not assume undocumented structures.

⸻

19.3 Jobs

Inspect actual repository outputs before implementation.

Use the strongest available existing source.

Potential priority:

1. structured latest-run output, if present
2. scored_jobs.csv
3. raw_jobs.csv
4. ledger records
5. search cache

Do not merge multiple weak sources into a new canonical model during this project.

⸻

19.4 Manual Queue

Use a small separate SQLite database or table.

Preferred location:

data/manual_jobs.db

This isolates the one new UI-specific persistence requirement from the existing application ledger.

⸻

20. Process Execution Requirements

20.1 Pipeline Execution

The UI should invoke the existing pipeline entry point.

Conceptually:

env = os.environ.copy()
env["APPLICATION_DRY_RUN"] = "true"
command = [
    sys.executable,
    "run_pipeline.py",
    "--max-applications",
    str(limit),
]

For live mode:

env["APPLICATION_DRY_RUN"] = "false"

The actual implementation must verify current CLI arguments before coding.

⸻

20.2 Reconciliation

The UI may execute:

monitor_applications.py

through the same controlled subprocess mechanism.

This is P1 if pipeline execution consumes significant implementation time.

⸻

20.3 Analytics

Prefer direct use of existing analytics functions if they are cleanly callable.

Otherwise:

* read ledger data directly for basic metrics;
* preserve application_report.py as the detailed CLI report.

Do not refactor the analytics subsystem merely to integrate the UI.

⸻

21. Safety Requirements

SR-001: Live Mode Protection

Live runs require:

explicit Live selection
+
application limit
+
confirmation checkbox

⸻

SR-002: Single Pipeline Process

The UI must prevent accidental duplicate pipeline launches from the same UI session.

A simple process-state guard is sufficient.

Do not build distributed locking.

⸻

SR-003: Secret Protection

Never render secret environment variables.

Use an explicit allowlist for displayed settings.

Never use a denylist alone.

⸻

SR-004: No Shell Injection

Use subprocess argument arrays.

Do not concatenate user-controlled values into shell=True commands.

⸻

SR-005: Bounded Inputs

Application limit must be:

* integer;
* positive;
* bounded to a reasonable maximum.

The UI should not permit malformed values.

⸻

SR-006: Failure Visibility

If a subprocess exits non-zero:

Status: FAILED
Exit code: N
Error output: ...

Do not convert process completion into success automatically.

⸻

22. UX Requirements

22.1 Visual Style

Use a restrained operational dashboard.

Recommended characteristics:

* wide layout;
* sidebar navigation;
* metric cards;
* dataframes;
* clear status indicators;
* minimal decorative content.

Avoid:

* excessive gradients;
* animations;
* oversized hero sections;
* marketing copy;
* unnecessary custom CSS.

⸻

22.2 Page Header Pattern

Each page should have:

Page Title
One-line operational description
Primary controls
Primary data
Secondary detail

⸻

22.3 Empty States

Examples:

No pipeline runs found.
No applications found in the ledger.
No jobs currently require manual review.
No manual jobs have been added.
Insufficient outcome data for this metric.

No stack traces should appear for normal missing-data states.

⸻

23. One-Day Implementation Plan

Block 0 — Repository Inspection

Maximum: 45 minutes

Before writing UI code, inspect:

run_pipeline.py CLI
run summary artifact location and schema
application ledger schema
analytics interfaces
job CSV schemas
manual review representation
existing dependencies

Required commands may include:

python run_pipeline.py --help
find artifacts -maxdepth 3 -type f | sort | tail -30
find data -maxdepth 2 -type f | sort
sqlite3 data/application_ledger.db ".tables"
sqlite3 data/application_ledger.db ".schema"

Do not begin architecture redesign based on findings.

The purpose is interface discovery.

⸻

Block 1 — UI Shell and Data Access

Target: 1.5 hours

Implement:

Streamlit app shell
navigation
page structure
SQLite connection helper
latest run-summary reader
safe empty states

Deliverable:

streamlit run ui/app.py

opens successfully and navigation works.

⸻

Block 2 — Dashboard and Applications

Target: 2 hours

Implement:

dashboard metrics
latest run summary
lifecycle counts
application table
basic filters

At this point, the UI must already provide useful read-only value.

⸻

Block 3 — Pipeline Control

Target: 2 hours

Implement:

dry/live mode
application limit
live confirmation
subprocess execution
running state
completion state
stdout/stderr capture
latest summary refresh

Do not build real-time orchestration infrastructure.

⸻

Block 4 — Manual Queue

Target: 1.5 hours

Implement:

manual job persistence
add form
queue table
status update
open URL
mark applied
mark skipped

This completes the practical multi-source bridge without source integrations.

⸻

Block 5 — Jobs and Review

Target: 1.5 hours

Implement:

job browser
basic filters
review queue
failure/review detail

Use available existing data.

⸻

Block 6 — Analytics and Cleanup

Target: 1 hour

Implement:

basic funnel metrics
lifecycle distribution
subtrack or priority breakdown
error handling
README instructions
dependency update
basic tests

If behind schedule, reduce analytics rather than extending the day.

⸻

24. Hard Timebox Rules

The implementation must follow these rules:

If a feature requires backend redesign:
    skip it.
If a feature requires schema migration of the main ledger:
    skip it.
If a feature requires more than 60 minutes of debugging:
    simplify it.
If real-time progress is difficult:
    show process state and final summary.
If job data is fragmented:
    use the best existing source.
If analytics integration is difficult:
    calculate basic read-only metrics from ledger data.
If review actions are unsafe:
    make the page read-only.
If visual polish competes with functionality:
    choose functionality.

The one-day limit is part of the product requirement.

⸻

25. Acceptance Criteria

AC-001: Startup

Given the virtual environment is active, when the user runs:

streamlit run ui/app.py

the application opens without requiring another backend process.

⸻

AC-002: Dashboard

The dashboard displays:

* latest run status;
* latest run counts;
* application count;
* lifecycle distribution;
* pipeline process state.

Missing data does not crash the page.

⸻

AC-003: Dry Run

The user can configure and launch a dry run.

The resulting process uses:

APPLICATION_DRY_RUN=true

The UI displays process state and completion result.

⸻

AC-004: Live Run Safety

A live run cannot start unless:

* Live mode is selected;
* maximum applications is provided;
* live confirmation is checked.

⸻

AC-005: Applications

The user can view existing ledger applications and filter by lifecycle stage.

⸻

AC-006: Manual Job

The user can:

1. add an external job;
2. see it in the queue;
3. open its URL;
4. change its status;
5. mark it applied.

⸻

AC-007: Review

The UI exposes available manual-review or failure states without crashing on missing review data.

⸻

AC-008: Analytics

At least basic lifecycle and application metrics are visible.

⸻

AC-009: Secrets

No password, API key, bearer token, cookie, session token, or nkparam value is rendered by the UI.

⸻

AC-010: Regression Safety

Existing test suite remains green after UI addition.

The UI must not require modification of core application behavior merely to function.

⸻

26. Testing Strategy

The one-day implementation does not require extensive UI automation.

Minimum tests should target logic, not Streamlit rendering.

Recommended tests:

test latest run summary selection
test missing run directory behavior
test ledger query with empty database
test manual job creation
test manual job status transition
test pipeline command construction for dry mode
test pipeline command construction for live mode
test secret settings are excluded

Manual smoke test:

1. Start UI.
2. Open every page.
3. Verify empty/missing state behavior.
4. Run a small dry run.
5. Confirm run state.
6. Confirm final summary.
7. Inspect applications.
8. Add a manual job.
9. Update its state.
10. Open its URL.
11. Verify analytics.
12. Confirm no secrets appear.

⸻

27. Dependency Policy

Add only necessary dependencies.

Expected:

streamlit
pandas

Use existing charting dependencies if already installed.

Do not add a large UI dependency stack.

⸻

28. README Addition

Add a concise section to the main README.

Recommended structure:

## Local Control Center
Career Workflow includes a local Streamlit control center for:
- pipeline execution;
- run monitoring;
- job inspection;
- application tracking;
- lifecycle visibility;
- manual external-job tracking;
- review queues;
- analytics.
Run:
    streamlit run ui/app.py
The control center is a local operational interface over the existing
Career Workflow engine. It does not require a separate backend service.

Do not rewrite the entire README during this task.

⸻

29. Recommended Initial File Set

The implementation should begin with:

ui/
├── __init__.py
├── app.py
├── data.py
├── runner.py
└── pages/
    ├── __init__.py
    ├── dashboard.py
    ├── pipeline.py
    ├── jobs.py
    ├── applications.py
    ├── manual_queue.py
    ├── review_queue.py
    └── analytics.py

Responsibilities:

ui/app.py

Streamlit configuration
navigation
page routing
shared layout

ui/data.py

ledger reads
run summary reads
job artifact reads
review artifact reads
manual queue persistence
analytics queries

ui/runner.py

pipeline command construction
subprocess launch
process state
log capture
exit status
reconciliation execution

ui/pages/*

Rendering and page-specific interaction only.

Keep business logic out of page modules where practical.

⸻

30. Implementation Boundaries

The implementing chat must follow these boundaries.

Allowed

Add Streamlit
Add UI directory
Read existing SQLite
Read existing CSV/JSON artifacts
Launch existing scripts
Add isolated manual-job persistence
Add small query helpers
Add focused UI-support tests
Add concise README UI instructions

Not Allowed

Rewrite pipeline
Rewrite classifier
Rewrite application executor
Rewrite ledger
Introduce canonical jobs model
Introduce source adapters
Integrate new job boards
Add FastAPI
Add React
Add Angular
Add Docker deployment
Add cloud deployment
Add authentication
Add background task framework
Refactor apply_agent.py merely for UI cleanliness

⸻

31. Product Outcome

At the end of the implementation day, the operational model should be:

                    CAREER WORKFLOW CONTROL CENTER
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
    AUTOMATED NAUKRI      MANUAL EXTERNAL       TRACKING
       PIPELINE               QUEUE                 │
          │                    │                    │
          ▼                    ▼                    ▼
      DISCOVERED          LINKEDIN              SUBMITTED
      CLASSIFIED          GOOGLE JOBS           VIEWED
      SELECTED            INSTAHYRE             SHORTLISTED
      APPLIED             WELLFOUND             INTERVIEW
                          CUTSHORT               REJECTED
                          COMPANY SITES          OFFER
                          REFERRALS
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
                               ▼
                          ONE DASHBOARD

This does not make Career Workflow a complete multi-source autonomous platform.

It makes the existing system usable immediately.

That is the required outcome.

⸻

32. Deferred Future Work

The following remain part of the broader Career Workflow 2.0 roadmap and must not enter this implementation:

source-independent domain model
source adapters
Google Jobs provider
LinkedIn assisted workflow
Instahyre integration
Wellfound integration
Cutshort integration
company career-page discovery
cross-source deduplication
canonical job identity
unified opportunity state machine
interview workspace
follow-up automation
scheduled source synchronization
notification system
production API
production frontend
multi-user architecture
deployment

The manual queue is the temporary bridge between the current Naukri engine and those future capabilities.

⸻

33. Final Delivery Checklist

Before considering the UI task complete:

[ ] UI starts locally
[ ] navigation works
[ ] dashboard shows real data
[ ] latest run summary works
[ ] applications table works
[ ] lifecycle filtering works
[ ] dry pipeline execution works
[ ] live mode has explicit protection
[ ] process failure is visible
[ ] manual jobs can be added
[ ] manual jobs can be updated
[ ] job URLs can be opened
[ ] review cases are visible where data exists
[ ] basic analytics work
[ ] missing data does not crash pages
[ ] secrets are never rendered
[ ] existing tests remain green
[ ] new focused tests pass
[ ] README contains UI startup instructions
[ ] no backend redesign occurred
[ ] no new source integration occurred
[ ] implementation stopped at the one-day boundary