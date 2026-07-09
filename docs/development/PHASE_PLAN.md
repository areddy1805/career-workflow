
# Career Workflow 2.0 Development Plan

## Objective

Transform the existing Career Workflow 1.0 automation pipeline into a local-first Job Search Operating System without interrupting real job-search activity.

The migration is incremental.

Existing working CLI behavior remains operational while new domain, persistence, API, UI, and source layers are introduced.

---

# Phase 0 — Baseline and Freeze

## Goal

Establish a trustworthy 1.0 baseline before structural migration.

## Deliverables

- repository audit;

- runtime flow map;

- database schema inventory;

- environment variable inventory;

- test inventory;

- baseline regression result;

- representative dry-run summary;

- representative live canary result if operationally appropriate;

- current system state document;

- protected baseline tag.

## Exit Criteria

- full test suite passes;

- current runtime entry points are documented;

- current persistence mechanisms are documented;

- current private runtime artifacts are identified;

- 1.0 baseline can be restored from Git;

- no 2.0 structural refactor has begun.

---

# Phase 1 — Canonical Domain and Source Boundary

## Goal

Introduce source-independent job representation without breaking the existing Naukri workflow.

## Deliverables

- canonical job model;

- source job observation model;

- source identity model;

- source capability model;

- source adapter protocol;

- Naukri adapter boundary;

- compatibility mapping from current Job model;

- canonicalization tests;

- provenance tests.

## Exit Criteria

- existing Naukri acquisition still works;

- source-specific payloads do not leak into canonical domain logic;

- one canonical job can represent multiple source observations;

- tests prove source provenance is preserved;

- existing CLI flow remains operational.

---

# Phase 2 — Database V2 and Migration Layer

## Goal

Create persistence capable of supporting multi-source jobs, candidate evaluation, application state, action queues, and source observations.

## Deliverables

- explicit schema migration mechanism;

- canonical jobs table;

- source observations table;

- candidate evaluations table;

- applications table;

- application events table;

- action queue table;

- source synchronization state;

- migration tests;

- compatibility import from existing ledger where required.

## Exit Criteria

- migration is repeatable;

- existing application history is preserved;

- rollback or backup procedure is documented;

- canonical jobs and source observations persist independently;

- application lifecycle behavior remains correct.

---

# Phase 3 — Workflow API

## Goal

Expose existing and new domain capabilities through a stable local API.

## Initial API Scope

- inbox;

- job details;

- evaluations;

- shortlist;

- ignore;

- queue action;

- mark applied;

- application list;

- lifecycle state;

- run history;

- analytics summary.

## Exit Criteria

- API starts locally;

- API tests pass;

- existing CLI remains operational;

- API uses domain services rather than duplicating business logic;

- UI-required workflows are supported.

---

# Phase 4 — Basic Operational UI

## Goal

Make the system usable as the daily control plane for job search.

## Required Screens

### Inbox

Show:

- title;

- company;

- location;

- work mode;

- source;

- score;

- priority;

- AI relevance;

- recommendation;

- age;

- application capability.

Actions:

- inspect;

- shortlist;

- ignore;

- apply automatically where supported;

- open preferred application route;

- mark manually applied.

### Job Detail

Show:

- canonical job information;

- source observations;

- evaluation explanation;

- score;

- red flags;

- recommendation;

- application routes;

- application history.

### Applications

Show:

- application date;

- source;

- application method;

- lifecycle stage;

- last update;

- stale state;

- notes.

### Dashboard

Show:

- discovered jobs;

- qualified jobs;

- shortlisted jobs;

- applications;

- response rate;

- interview rate;

- source contribution;

- application velocity.

## Exit Criteria

- real daily job workflow can be performed from the UI;

- manual application workflow is fully trackable;

- auto-apply workflow remains controlled;

- UI does not duplicate core business logic;

- CLI remains available for diagnostics and fallback.

---

# Operational Stop Point

After Phase 4:

1. stop major foundation development;

2. use Career Workflow daily;

3. apply to real jobs;

4. prepare for interviews;

5. record workflow friction;

6. prioritize only high-impact improvements.

The project must not become a substitute for the job search itself.

---

# Phase 5 — External Source Wave 1

## Goal

Prove the multi-source architecture with high-value direct sources and discovery coverage.

## Wave 1

- Greenhouse;

- Lever;

- Ashby.

## Wave 2

- Wellfound;

- Himalayas.

## Wave 3

- Google Jobs / search-based discovery;

- original-source resolution;

- ATS fingerprinting;

- canonical URL resolution.

## Exit Criteria

- external jobs enter the same inbox;

- provenance remains visible;

- duplicate jobs merge correctly;

- evaluation remains source-independent;

- preferred application route opens correctly;

- manual application state is trackable.

---

# Phase 6 — India Coverage Expansion

Source priority will be based on measured coverage gaps.

Candidate sources include:

- LinkedIn discovery;

- Instahyre;

- Cutshort;

- Hirist;

- Foundit;

- Indeed India discovery.

No source is added solely because it is popular.

Each source must be evaluated using:

- unique eligible job yield;

- duplicate rate;

- source freshness;

- implementation cost;

- maintenance burden;

- application conversion;

- interview conversion.

---

# Phase 7 — Remote Coverage Expansion

Candidate sources include:

- Remote OK;

- We Work Remotely;

- Remotive;

- YC Jobs;

- selected AI-specific boards;

- employer career sites.

Remote eligibility must account for:

- India eligibility;

- worldwide eligibility;

- country restrictions;

- timezone constraints;

- work authorization;

- employee versus contractor arrangement.

---

# Phase 8 — Operational Hardening

Potential work:

- run locking;

- scheduler;

- structured logging;

- notifications;

- daily digest;

- source health monitoring;

- stale-job cleanup;

- retention policies;

- backup and restore;

- action queue recovery.

This phase is driven by real usage evidence rather than speculative infrastructure design.

