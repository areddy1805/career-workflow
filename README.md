<p align="center">
  <img src="assets/logo.png" alt="Career Workflow" width="720"/>
</p>

<h1 align="center">Career Workflow</h1>

<p align="center">
  <strong>Policy-Driven AI Job Discovery, Qualification, and Application Orchestration Engine</strong>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
  <img alt="Tests" src="https://img.shields.io/badge/tests-passing-brightgreen">
  <img alt="Release" src="https://img.shields.io/badge/release-v1.0.0--RC1-blue">
  <img alt="Architecture" src="https://img.shields.io/badge/architecture-staged%20pipeline-blueviolet">
  <img alt="Providers" src="https://img.shields.io/badge/providers-Naukri%20%7C%20JobSpy-2E8B57">
  <img alt="Storage" src="https://img.shields.io/badge/storage-SQLite-003B57?logo=sqlite&logoColor=white">
  <img alt="LLM" src="https://img.shields.io/badge/LLM-local--first%20%28oMLX%29-orange">
  <img alt="Console" src="https://img.shields.io/badge/console-React%20%2B%20FastAPI-61DAFB">
</p>

---

## Overview

**Career Workflow** is an enterprise-grade, policy-driven application orchestration engine. It combines multi-provider job acquisition, candidate-aware AI qualification, selection budget enforcement, direct and questionnaire-based application execution, lifecycle tracking, funnel analytics, and intelligent dual-tier performance caching.

Above the core engine sits a modern **React Operations Console** and **FastAPI Control Plane**, providing real-time visibility into pipeline execution, application queues, metrics projections, and system health.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        CAREER WORKFLOW PIPELINE                         │
└─────────────────────────────────────────────────────────────────────────┘
   │
   ▼
[ 1. ACQUISITION ]    Naukri API + JobSpy (Indeed, LinkedIn, Glassdoor, Google)
   │
   ▼
[ 2. CLASSIFICATION ] Local LLM Fit Scoring + Stack & Location Alignment
   │
   ▼
[ 3. SELECTION ]      Selection Budget + Company & Role Diversity Controls
   │
   ▼
[ 4. APPLICATION ]    Application Router + Questionnaire Resolver (Deterministic/LLM)
   │
   ▼
[ 5. ACCOUNTING ]     SQLite Ledger + Universal Job Link Preservation + Terminal Status
   │
   ▼
[ 6. OBSERVABILITY ]  Metrics Projection + Trace Log + Event Bus Projections
```

---

## Key Capabilities (Verified against Code)

- **Dual-Engine Job Acquisition**: Hybrid provider fetching via authenticated Naukri API client (`src/client/naukri_client.py`) and unauthenticated JobSpy scraping (`src/acquisition/jobspy_provider.py`) supporting Google Jobs, Indeed, and LinkedIn with Pandas DataFrame isolation.
- **Candidate-Aware AI Scoring**: Local-first LLM evaluation (`src/llm/client.py`) scoring match quality against candidate stack, experience, and target roles.
- **Selection Budget & Diversity Engine**: Hard capacity budget constraints (`src/application/policy.py`, `src/application/diversity.py`) preventing application over-clustering per company, role family, or vacancy.
- **Hybrid Questionnaire Resolution**: Deterministic rule matching combined with local LLM resolution (`src/resolution/hybrid_resolver.py`) for complex multi-choice, text, and numeric application screening questions.
- **Universal Job Link Preservation**: Guarantees raw job posting URLs and apply direct links are preserved end-to-end across acquisition, classification, selection, and terminal accounting.
- **SQLite Application Ledger**: Transactional state store (`src/application/ledger.py`) tracking job application lifecycles from acquisition through terminal states (`APPLIED`, `REJECTED`, `EXPIRED`, `SKIPPED`).
- **Intelligent Dual-Tier Caching**: High-performance caching layer with LLM Fingerprint Caching (`src/cache/fingerprint.py`) and Job Search Acquisition Caching (`src/search/job_search_cache.py`).
- **React Operations Console**: Modern web dashboard built with React, Vite, and TailwindCSS (`frontend/`) communicating with FastAPI Control Plane (`api/routes.py`).

---

## Verified Project Structure

```text
career-workflow/
├── api/                   # FastAPI Control Plane endpoints
│   ├── main.py            # API entry point & CORS configuration
│   ├── routes.py          # REST routes for dashboard, jobs, queues, runs
│   └── schemas.py         # Request payload validation models
├── assets/                # Repository logo & assets
├── config/                # Candidate profiles & search configuration
│   ├── candidate_evidence.py
│   ├── candidate_profile.py
│   ├── search_strategy.yaml
│   └── user_profile.yaml
├── control_center/        # Backend helpers for Operations Console
├── data/                  # Local SQLite ledger & caches (gitignored)
├── deploy/                # Deployment configurations (macOS launchd plist)
├── docs/                  # Architecture & system specifications
│   ├── API.md             # Control Plane REST API documentation
│   ├── ARCHITECTURE.md    # Complete system architecture specification
│   ├── CONFIGURATION.md   # Configuration & environment variable guide
│   ├── PRODUCTION_CHECKLIST.md # Production release gate checklist
│   └── releases/
│       └── v1.0.0-RC1.md  # Official Release Candidate notes
├── frontend/              # React + Vite enterprise operations console
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── src/                   # Core Python application package
│   ├── acquisition/       # Multi-board scrapers & JobSpy provider
│   ├── application/       # Router, lifecycle, & manual action queue
│   ├── cache/             # LLM fingerprint & job search cache manager
│   ├── client/            # Naukri API client & AI job classifier
│   ├── llm/               # oMLX / Local LLM HTTP client
│   ├── orchestration/     # Staged pipeline, event bus, & metrics
│   ├── resolution/        # Hybrid questionnaire resolver
│   └── search/            # Search planner & challenge cooldown manager
├── tests/                 # Automated unit and integration test suite
├── .env.example           # Example configuration file
├── .gitignore             # Comprehensive repository exclusion rules
├── LICENSE                # MIT License
├── pyproject.toml         # Package metadata, ruff & pytest configuration
├── README.md              # Open-source manual
├── requirements.txt       # Python package requirements
├── run_pipeline.py        # Pipeline CLI entry point
└── run_scheduler.py       # Automated background scheduler
```

---

## Quick Start & Verified Operations

### 1. Installation

```bash
git clone https://github.com/areddy1805/career-workflow.git
cd career-workflow

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Verified CLI Commands

Run a **Dry Run** (simulates discovery, scoring, selection without live submission):
```bash
python run_pipeline.py --mode dry_run --budget 10
```

Run a **Live Application Run**:
```bash
python run_pipeline.py --mode live_run --budget 5
```

Run the **Automated Background Scheduler**:
```bash
python run_scheduler.py
```

### 3. Operations Console (Web UI)

Start FastAPI Control Plane:
```bash
uvicorn api.main:app --reload --port 8000
```

Start React Operations Console:
```bash
cd frontend
npm install
npm run dev
```

Navigate to `http://localhost:5173` to open the Operations Console.

---

## License

Distributed under the MIT License. See `LICENSE` for details.
