# Career Workflow v2.7 — Enterprise Operations Console

An AI-Assisted Job Discovery, Evaluation, and Application Orchestration platform.

## Overview
Career Workflow is a closed-loop job application orchestration system that combines resilient job discovery, candidate-aware qualification, policy-controlled selection, application execution, questionnaire resolution, lifecycle tracking, funnel analytics, and evidence-gated strategy adaptation.

With version 2.7, this project introduces a fully polished React operations console for managing all aspects of the daily job search, acquisition, and application lifecycle.

## 🚀 Daily Operations Guide

The pipeline is completely automated, but designed for operator oversight. Your daily routine should be:

1. **Start the System**: Run the backend API and frontend console.
2. **Launch the Pipeline**: Navigate to the `Pipeline` tab and click "Launch Pipeline". You can watch the live terminal logs.
3. **Review Queues**:
   - Go to the `Queues` tab.
   - The **Review Queue** shows the jobs the system shortlisted in the latest run.
   - The **Auto Detected** queue shows external jobs that require you to apply manually (with quick action buttons to Open, Mark Reviewed, or Dismiss).
   - The **Manually Sourced** queue lets you add jobs you found elsewhere (LinkedIn, Wellfound).
4. **Inspect Outcomes**: View the `Dashboard` for System Health, Pipeline Funnel, and Top Companies.
5. **Analyze Search Intelligence**: Visit the `Search` tab to verify exactly which profiles and queries the system generated and what technologies matched.

## 🔧 Installation & Setup

1. **Backend**:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8090
```

2. **Frontend**:
```bash
cd frontend
npm install
npm run dev -- --port 5173
```

3. **Access the Console**: Open `http://localhost:5173`.

## ⚙️ Configuration & Profiles

The heart of the acquisition engine is the **Search Profile Engine** (located in `config/`). It uses configuration over code to dynamically assemble search queries.

- `user_profile.yaml`: Your master configuration. Defines active career profiles and locations.
- `search_profiles/`: YAML files defining roles (e.g., `agentic_ai_engineer.yaml`). Each profile cross-references technology groups.
- `technology_profiles/`: Reusable taxonomies of skills (e.g., `cloud.yaml`, `rag.yaml`).
- `negative_profiles/`: Exclusion terms that are automatically appended to queries (`-SAP`, `-BPO`).

*See `config/README.md` for a comprehensive guide on adding new profiles and technologies.*

## 🔍 Artifacts & Explainability

Every execution creates an immutable snapshot in `artifacts/runs/<timestamp>/`.

Career Workflow exposes the "Why" behind every action. Every job evaluated by the system records:
- **Search Profile**: Which profile triggered the acquisition (`rag_engineer`).
- **Generated Query**: The exact search string (`"AI Engineer" ChromaDB -SAP`).
- **Matched Technology**: The specific technology group that matched.
- **Rejection Reason**: If rejected, a clear explanation (e.g., `No salary specified`, `Score below threshold`).

You can view these directly in the `Artifacts` tab in the UI.

## 🛠️ Recovery & Troubleshooting

The system is designed to be resilient.
- **Corrupt Cache / State Files**: The system uses safe loading. If a JSON file is corrupt, it is gracefully ignored, allowing the system to continue running.
- **Interrupted Pipeline**: The daemon scheduler tracks process health. If the pipeline dies unexpectedly, the Lock is cleared, and the run is marked as `RECOVERED`. You can safely launch it again.
- **Stale Dashboard Status**: Check the `Runtime` tab to verify if the UI API, Scheduler, or Pipeline workers are actually alive.
