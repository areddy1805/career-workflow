import importlib.util
from pathlib import Path

from src.client import jop_classifier as module
Pipeline = module.JobFilterPipeline2


def pipeline(tmp_path):
    return Pipeline(
        api_key="test",
        cache_file=str(tmp_path / "cache.json"),
        min_apply_score=60,
    )


def job(
    job_id,
    title,
    tags,
    description,
    experience="4-8 Yrs",
    days_old=1,
):
    return {
        "job_id": job_id,
        "title": title,
        "company": "Test Co",
        "location": "Pune",
        "tags": tags,
        "description": description,
        "experience": experience,
        "posted_date": f"{days_old} days ago",
    }


def normalize_one(p, raw):
    return p.normalize_jobs([raw])[0]


def test_ai_enabled_angular_fullstack_survives_prefilter(tmp_path):
    p = pipeline(tmp_path)
    raw = job(
        "1",
        "Full Stack Engineer - Angular + GenAI",
        ["angular", "typescript", "python", "rag", "langchain"],
        "Build Angular AI products, Python APIs, RAG pipelines, vector search and LLM agents.",
    )
    result = p.pre_filter([raw])
    assert [x["job_id"] for x in result] == ["1"]


def test_pure_angular_role_fails_ai_relevance_gate(tmp_path):
    p = pipeline(tmp_path)
    raw = job(
        "2",
        "Angular Developer",
        ["angular", "typescript", "rxjs"],
        "Build enterprise dashboards and reusable UI components.",
    )
    normalized = p.normalize_jobs([raw])
    assert p.ai_relevance_gate(normalized) == []


def test_generic_backend_role_fails_ai_relevance_gate(tmp_path):
    p = pipeline(tmp_path)
    raw = job(
        "3",
        "Backend Engineer",
        ["python", "fastapi", "postgresql", "docker"],
        "Build REST APIs and microservices.",
    )
    normalized = p.normalize_jobs([raw])
    assert p.ai_relevance_gate(normalized) == []


def test_strong_applied_ai_score_gets_floor(tmp_path):
    p = pipeline(tmp_path)
    j = normalize_one(
        p,
        job(
            "4",
            "Applied AI Engineer",
            ["python", "fastapi", "rag", "langchain", "vector search"],
            "Build RAG, embeddings, vector search, LangGraph agents, tool calling and LLM evaluation APIs.",
        ),
    )
    assert p._calibrate_score(j, 55) >= 78


def test_incidental_ai_mention_is_capped(tmp_path):
    p = pipeline(tmp_path)
    j = normalize_one(
        p,
        job(
            "5",
            "Software Engineer",
            ["python", "fastapi", "postgresql"],
            "Build backend services and occasionally integrate an OpenAI API.",
        ),
    )
    j["ai_score"] = 88
    guarded = p.post_score_guard([j])
    assert guarded[0]["ai_score"] <= 59


def test_research_primary_role_is_vetoed(tmp_path):
    p = pipeline(tmp_path)
    j = normalize_one(
        p,
        job(
            "6",
            "Research Engineer",
            ["python", "pytorch", "deep learning"],
            "Research scientist work: applied research, publish papers, novel architectures, train foundation models.",
        ),
    )
    j["ai_score"] = 90
    assert p.post_score_guard([j]) == []


def test_ml_libraries_do_not_equal_applied_ai(tmp_path):
    p = pipeline(tmp_path)
    j = normalize_one(
        p,
        job(
            "7",
            "Machine Learning Engineer",
            ["python", "pytorch", "tensorflow", "scikit-learn"],
            "Model training, feature engineering, hyperparameter tuning and deep learning.",
        ),
    )
    assert p._calibrate_score(j, 85) <= 39


def test_senior_transition_role_not_rejected_by_four_year_cutoff(tmp_path):
    p = pipeline(tmp_path)
    j = normalize_one(
        p,
        job(
            "8",
            "Senior Generative AI Engineer",
            ["python", "rag", "langgraph"],
            "Build production LLM applications and agents.",
            experience="6-9 Yrs",
        ),
    )
    assert p.experience_filter([j]) == [j]


def test_unrealistic_executive_scope_rejected(tmp_path):
    p = pipeline(tmp_path)
    j = normalize_one(
        p,
        job(
            "9",
            "VP of AI Engineering",
            ["genai", "llm"],
            "Own the global AI engineering organization.",
            experience="12-18 Yrs",
        ),
    )
    assert p.experience_filter([j]) == []


def test_rank_fit_dominates_recency(tmp_path):
    p = pipeline(tmp_path)
    older_better = {"job_id": "a", "ai_score": 85, "ai_signal_count": 5, "days_old": 6}
    newer_weaker = {"job_id": "b", "ai_score": 84, "ai_signal_count": 8, "days_old": 0}
    ranked = p.rank([newer_weaker, older_better])
    assert ranked[0]["job_id"] == "a"
