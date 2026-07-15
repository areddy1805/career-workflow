# Changelog

All notable changes to Career Workflow are documented in this file.

The format follows a project-oriented changelog rather than individual commit history.

---

# [3.0 Phase 1.1]

## Overview
Phase 1.1 refactors the classification funnel to align with the spray-and-pray application strategy. We transitioned from aggressive hard-gates to a progressive ranking architecture. Legacy NiceGUI dependencies have been fully removed.

---

## Changed
- **Summary Ranking Pipeline**: Introduced an adaptive, heuristic-based summary ranker that scores jobs *before* executing the detail fetch budget.
- **AI Relevance Gate**: Removed `LOW_AI_RELEVANCE` as a hard rejection. Engineering roles lacking explicit AI signals are now penalized in ranking, rather than eliminated.
- **Location Policy**: Replaced the strict Pune-only office policy with a robust Location Preference engine (Preferred, Acceptable, Rejected) acting as a ranking penalty.
- **Application Budgets**: `DAILY_APPLY_LIMIT` no longer abruptly truncates the classification pipeline; jobs are now fully ranked and handed over to the Selection stage.
- **Decoupled Strategy Config**: Introduced `config/search_strategy.yaml` to decouple budget and gating thresholds from the core logic.

## Removed
- **Wrong Track Hard Gate**: Eliminated hard rejections for tracks like DevOps, SRE, and Mobile.
- **Legacy NiceGUI**: Safely removed all unused legacy NiceGUI code, pages, and runner scripts.

---

# [2.7.0]
---

## Added

### Enterprise React Operations Console
- Modern, responsive React + Vite frontend replacing NiceGUI.
- **Search Intelligence Dashboard**: Real-time visibility into generated search queries, locations, matching technologies, and active profiles.
- **Actionable Workflows**: Triage manual review and external application queues natively (Mark Reviewed, Dismiss, Open Posting).
- **Dashboard Telemetry**: Live system health (disk, scheduler, pipeline locks), top target companies, pipeline funnel, and upcoming executions.

### Search Profile Engine
- Configuration-driven architecture (`config/user_profile.yaml`) replacing hardcoded strings.
- YAML taxonomies for roles (`search_profiles/`) and technologies (`technology_profiles/`).
- Extensible logic to scale from a single query matrix to hundreds of targeted combinations.

### Artifact Traceability & Explainability
- Complete provenance injected into job objects (`search_profile`, `matched_technology`).
- Explicit `rejection_reason` tracking for all jobs evaluated by the system.
- Artifacts directly explain the "Why" behind selection and rejection decisions.

### Backend Infrastructure
- Extensible REST API in FastAPI bridging the control center to the React frontend.
- Persistent `review_state.json` ledger for queue actions and dismissals.
- Hardened `json.loads` recovery logic across the scheduler, `recovery.py`, and `job_search_cache.py`.

---

# [2.0.0]

## Overview

Career Workflow evolved from an API automation client into a complete policy-driven job application orchestration platform.

Version 2.0 introduces a production-style pipeline architecture, persistent application intelligence, operational observability, and a dedicated operations control plane.

---

## Added

### NiceGUI Operations Control Plane

- Command Center dashboard
- Pipeline execution console
- Jobs explorer
- Applications explorer
- Workflow queue
- Manual queue
- Review queue
- Analytics dashboard
- Run Inspector
- System Health dashboard
- Runtime configuration pages

---

### Pipeline Orchestration

Introduced staged pipeline execution:

- Preflight
- Acquisition
- Classification
- Selection
- Application
- Reconciliation
- Strategy
- Reporting

Each stage executes independently with structured artifacts and isolated failure handling.

---

### Run Artifacts

Every execution now produces immutable run artifacts.

Added:

- run.json
- result.json
- report.json
- preflight.json
- acquisition.json
- classification.json
- selection.json
- application.json
- reconciliation.json
- strategy.json
- timeline.json
- diagnostics.json
- environment.json
- manifest.json

Artifacts now include:

- schema version
- stage timings
- runtime metadata
- diagnostics
- environment
- execution summaries
- rejection analytics

---

### Runtime Observability

Added:

- scheduler runtime state
- pipeline runtime state
- UI runtime state
- heartbeat monitoring
- process ownership detection
- orphan detection
- stale detection
- runtime diagnostics

---

### Job Acquisition

Expanded acquisition into a resilient multi-query engine.

Added:

- search caching
- cache fallback
- challenge detection
- cooldown handling
- pagination limits
- duplicate suppression
- acquisition telemetry
- bounded search execution

---

### Classification

Expanded job intelligence.

Added:

- AI relevance analysis
- candidate-aware scoring
- deterministic filters
- work-mode policy
- location policy
- company vetoes
- stack compatibility
- LLM-assisted fit scoring
- score caching
- structured rejection decisions

---

### Selection Policy

Added:

- application ceilings
- company diversity
- role-family diversity
- vacancy fingerprint limits
- selection budgets
- deterministic allocation

---

### Application Engine

Added:

- direct application execution
- questionnaire handling
- semantic response interpretation
- retry policy
- failure classification
- dry-run execution
- canary mode

---

### Questionnaire Resolution

Implemented hybrid resolution pipeline.

Added:

- deterministic resolver
- evidence retrieval
- constraint validation
- answer validation
- local LLM fallback
- telemetry capture

---

### Persistent Ledger

Added SQLite-backed application tracking.

Stores:

- applications
- lifecycle state
- server status
- timestamps
- event history
- run summaries

---

### Lifecycle Intelligence

Added:

- recruiter status reconciliation
- server history import
- lifecycle normalization
- monotonic stage progression
- stale application detection

---

### Analytics

Added:

- funnel metrics
- lifecycle analytics
- response rates
- velocity
- age distribution
- priority analysis
- subtrack analysis
- adaptive strategy metrics

---

### Adaptive Strategy

Implemented evidence-gated optimization.

Supports:

- score threshold tuning
- application allocation
- priority balancing
- subtrack balancing
- exploration vs exploitation

---

### Rejection Explainability

Added structured rejection recording.

Captures:

- rejection stage
- rejection code
- rejection reason
- AI explanation
- score
- threshold
- summary statistics

Run Inspector now exposes complete rejection diagnostics.

---

### Operational Utilities

Added:

- factory reset procedure
- runtime cleanup
- diagnostics helpers
- runtime status services
- centralized formatting utilities
- IST timestamp formatting

---

### Testing

Expanded automated coverage across:

- application engine
- acquisition
- classifier
- selection policy
- adaptive strategy
- reconciliation
- NiceGUI UI
- operational services

---

### Documentation

Completely rewrote project documentation.

Added:

- architecture
- operating model
- pipeline documentation
- UI documentation
- observability
- runtime model
- lifecycle intelligence
- adaptive strategy
- deployment
- repository structure
- factory reset
- quick start
- control plane documentation

---

## Changed

### Architecture

Migrated from a direct application script into a layered architecture:

```
UI
↓

Control Center

↓

Pipeline

↓

Application Services

↓

Search / Classification / Resolution

↓

Persistence
```

---

### Runtime Model

Separated runtime truth into independent sources:

- UI Runtime
- Scheduler Runtime
- Pipeline Runtime
- Artifact State
- Persistent Portfolio

---

### Observability

Migrated from console logging to structured operational artifacts and runtime diagnostics.

---

### Repository

Reorganized into clear domains:

- career_ui
- control_center
- src
- tests
- config
- artifacts
- data

---

## Fixed

- Scheduler state inconsistencies
- Runtime orphan detection
- Pipeline state persistence
- Artifact schema consistency
- IST timezone rendering
- Dashboard runtime accuracy
- Rejection tracking
- Classification diagnostics
- Application policy reporting
- Pipeline diagnostics
- Historical artifact inspection
- Test regressions
- Runtime cleanup
- UI consistency issues

---

## Removed

- Temporary migration scripts
- Development helper utilities
- Experimental patch files
- Stale virtual environments
- Obsolete runtime state
- Legacy UI behaviors

---

# [1.x]

Initial API automation foundation based on the NopeRi project.

Included:

- authentication
- session handling
- profile APIs
- search APIs
- application APIs

This version served as the foundation upon which Career Workflow was developed.