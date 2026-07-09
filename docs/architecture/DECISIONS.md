his document records architectural decisions that materially affect the structure, data model, interfaces, or long-term evolution of Career Workflow.

It is not a changelog.

Implementation history belongs in Git.

Current implementation status belongs in `CURRENT_SYSTEM_STATE.md`.

Product requirements belong in `CAREER_WORKFLOW_PRD_BRD.md`.

---

## Decision Format

Each accepted decision uses this structure:

```text

## ADR-XXX — Decision Title

Status: Accepted | Superseded | Deprecated

Date: YYYY-MM-DD

### Context

Why the decision was required.

### Decision

What was decided.

### Consequences

What this enables, constrains, or makes more difficult.

⸻

ADR-001 — Local-First Architecture

Status: Accepted

Date: 2026-07-09

Context

Career Workflow is a personal job-search operating system intended primarily for one user. The system handles private candidate data, application history, credentials, questionnaire evidence, and recruiting lifecycle information.

The current workload does not justify distributed infrastructure.

Decision

Career Workflow will remain local-first.

The primary deployment model will use:

* local application processes;
* a local relational database;
* local or explicitly configured LLM inference;
* browser-based local UI;
* external job sources accessed through isolated source adapters.

Cloud infrastructure will not be introduced without a concrete operational requirement.

Consequences

The architecture remains simpler to operate and protects private data.

Horizontal scaling and multi-user concerns are explicitly out of scope for the current product.

⸻

ADR-002 — Modular Monolith

Status: Accepted

Date: 2026-07-09

Context

The product is expanding from a single-source automation workflow into a multi-source job-search operating system.

The system requires clear domain boundaries but does not require independently deployed services.

Decision

Career Workflow 2.0 will use a modular monolith architecture.

Major logical boundaries include:

* source acquisition;
* canonical job domain;
* candidate evaluation;
* application policy;
* application execution;
* manual action queue;
* lifecycle tracking;
* analytics;
* strategy adaptation;
* API;
* UI.

These boundaries may exist as Python packages and interfaces inside one deployable application.

Consequences

The system gains architectural separation without distributed-system overhead.

Internal boundaries must remain explicit enough to prevent source-specific behavior from leaking across the product.

⸻

ADR-003 — Canonical Job Separate from Source Observation

Status: Accepted

Date: 2026-07-09

Context

The same vacancy may appear through multiple sources:

* Naukri;
* an employer career site;
* Greenhouse;
* Lever;
* Google Jobs discovery;
* another job board.

Treating every source record as a unique job creates duplicate evaluation, duplicate presentation, and duplicate application risk.

Decision

Career Workflow 2.0 will distinguish:

1. canonical job identity;
2. source-specific job observations.

A canonical job may have multiple source observations.

Each source observation preserves:

* source;
* source job identifier;
* source URL;
* discovered timestamp;
* source-specific metadata;
* raw or normalized source fields as required.

Consequences

Cross-source deduplication becomes a first-class capability.

Source provenance remains preserved after merging.

The data model becomes more complex than a single jobs table but supports the intended multi-source architecture.

⸻

ADR-004 — Job Separate from Candidate Evaluation

Status: Accepted

Date: 2026-07-09

Context

Job attributes and candidate-specific evaluation are different domains.

A job description is source data.

Fit score, AI relevance, priority tier, red flags, and recommendation are candidate-relative assessments.

Decision

Canonical job data will remain separate from candidate evaluation data.

Evaluation results may evolve independently as:

* candidate profile changes;
* scoring logic changes;
* model configuration changes;
* evaluation versions change.

Consequences

Jobs do not need to be duplicated when evaluation logic changes.

Evaluation history and rescoring become possible.

⸻

ADR-005 — Job Separate from Application

Status: Accepted

Date: 2026-07-09

Context

A discovered job may never be applied to.

An application has its own lifecycle, events, timestamps, status history, and execution metadata.

Decision

Job entities and application entities will remain separate.

Application lifecycle state will not be stored as intrinsic canonical job state.

Consequences

The system can track:

* discovered but ignored jobs;
* shortlisted jobs;
* queued jobs;
* manually applied jobs;
* automatically applied jobs;
* server-imported historical applications.

⸻

ADR-006 — Source Adapter Boundary

Status: Accepted

Date: 2026-07-09

Context

Career Workflow must support direct platforms, ATS systems, remote job boards, employer career pages, and meta-discovery sources.

Each source has different authentication, pagination, rate limits, fields, and application capabilities.

Decision

Source-specific behavior will be isolated behind adapter boundaries.

Core evaluation, policy, canonicalization, application tracking, and UI logic must not depend directly on source-specific response structures.

Consequences

New sources can be added incrementally.

Source capabilities may differ without contaminating core domain logic.

⸻

ADR-007 — Meta-Discovery Is Not an Authoritative Application Source

Status: Accepted

Date: 2026-07-09

Context

Google Jobs and search-based discovery can reveal opportunities that direct integrations miss.

However, search aggregation results often point to another job board, ATS, or employer career page.

Decision

Meta-discovery sources will produce discovery observations.

The system will attempt to resolve:discovery observation
    → original source
    → employer or ATS
    → canonical URL
    → canonical job
    → preferred application route

The authoritative employer or ATS route is preferred when available.

Consequences

Meta-discovery expands coverage without becoming a duplicate application channel.

Source resolution and provenance become explicit parts of the architecture.

⸻

ADR-008 — Preserve Existing 1.0 Behavior During Migration

Status: Accepted

Date: 2026-07-09

Context

Career Workflow 1.0 already performs useful real-world work:

* acquisition;
* classification;
* selection;
* application execution;
* questionnaire resolution;
* tracking;
* reconciliation;
* analytics;
* adaptive strategy.

A rewrite would delay real job applications and introduce unnecessary regression risk.

Decision

Career Workflow 2.0 will be developed through incremental migration.

Existing CLI workflows remain available until replacement paths are validated.

Consequences

Temporary compatibility layers may exist.

Some duplication during migration is acceptable when it reduces risk.

Removal of old paths requires explicit evidence that replacement behavior is complete and tested.
EOF
The authoritative employer or ATS route is preferred when available.

Consequences

Meta-discovery expands coverage without becoming a duplicate application channel.

Source resolution and provenance become explicit parts of the architecture.

⸻

ADR-008 — Preserve Existing 1.0 Behavior During Migration

Status: Accepted

Date: 2026-07-09

Context

Career Workflow 1.0 already performs useful real-world work:

* acquisition;
* classification;
* selection;
* application execution;
* questionnaire resolution;
* tracking;
* reconciliation;
* analytics;
* adaptive strategy.

A rewrite would delay real job applications and introduce unnecessary regression risk.

Decision

Career Workflow 2.0 will be developed through incremental migration.

Existing CLI workflows remain available until replacement paths are validated.

Consequences

Temporary compatibility layers may exist.

Some duplication during migration is acceptable when it reduces risk.

Removal of old paths requires explicit evidence that replacement behavior is complete and tested.
