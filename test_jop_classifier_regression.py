from src.client import jop_classifier as module

Pipeline = module.JobFilterPipeline2


def pipeline(tmp_path, min_apply_score=50):
    return Pipeline(
        api_key="test",
        cache_file=str(tmp_path / "cache.json"),
        min_apply_score=min_apply_score,
    )


def job(job_id, title, tags=None, description="", location="Pune",
        experience="4-8 Yrs", work_mode=None):
    data = {
        "job_id": job_id,
        "title": title,
        "company": "Test Co",
        "location": location,
        "tags": tags or [],
        "description": description,
        "experience": experience,
        "posted_date": "1 day ago",
    }
    if work_mode:
        data["work_mode"] = work_mode
    return data


def norm(p, raw):
    return p.normalize_jobs([raw])[0]


def test_ai_ml_title_not_hard_vetoed(tmp_path):
    p = pipeline(tmp_path)
    raw = job("1", "AI/ML Engineer", ["python", "pytorch"], "Build ML systems")
    assert p.hard_veto(p.normalize_jobs([raw]))


def test_data_scientist_ai_role_not_hard_vetoed(tmp_path):
    p = pipeline(tmp_path)
    raw = job("2", "Data Scientist - Generative AI", ["llm"], "Build AI systems")
    assert p.hard_veto(p.normalize_jobs([raw]))


def test_stack_conflict_is_never_eligibility_veto(tmp_path):
    p = pipeline(tmp_path)
    raws = [
        job("j", "Java AI Engineer", ["java", "spring", "machine learning"]),
        job("c", "C++ Computer Vision Engineer", ["c++", "opencv", "deep learning"]),
        job("n", ".NET AI Developer", [".net", "azure ai", "artificial intelligence"]),
    ]
    normalized = p.normalize_jobs(raws)
    assert len(p.primary_stack_conflict_filter(normalized, True)) == 3


def test_explicit_ml_and_cv_titles_pass_ai_relevance(tmp_path):
    p = pipeline(tmp_path)
    raws = [
        job("m", "Machine Learning Engineer", ["python"], "Train ML models"),
        job("v", "Computer Vision Engineer", ["opencv"], "Build vision AI"),
    ]
    normalized = p.normalize_jobs(raws)
    assert len(p.ai_relevance_gate(normalized)) == 2


def test_generic_backend_without_ai_fails_relevance(tmp_path):
    p = pipeline(tmp_path)
    raw = job("3", "Backend Developer", ["node.js"], "Build REST APIs")
    normalized = p.normalize_jobs([raw])
    assert p.ai_relevance_gate(normalized) == []


def test_remote_anywhere_passes_location_gate(tmp_path):
    p = pipeline(tmp_path)
    raw = norm(p, job("4", "AI Engineer", ["ai"], "Remote role", "Bengaluru", work_mode="Remote"))
    assert p.location_work_mode_gate([raw]) == [raw]


def test_pune_hybrid_passes_location_gate(tmp_path):
    p = pipeline(tmp_path)
    raw = norm(p, job("5", "AI Engineer", ["ai"], "Hybrid role", "Pune", work_mode="Hybrid"))
    assert p.location_work_mode_gate([raw]) == [raw]


def test_non_pune_hybrid_rejected(tmp_path):
    p = pipeline(tmp_path)
    raw = norm(p, job("6", "AI Engineer", ["ai"], "Hybrid role", "Chennai", work_mode="Hybrid"))
    assert p.location_work_mode_gate([raw]) == []


def test_non_pune_office_rejected(tmp_path):
    p = pipeline(tmp_path)
    raw = norm(p, job("7", "AI Engineer", ["ai"], "Work from office", "Hyderabad"))
    assert p.location_work_mode_gate([raw]) == []


def test_explicit_ai_title_gets_apply_floor(tmp_path):
    p = pipeline(tmp_path, min_apply_score=50)
    raw = norm(p, job("8", "Machine Learning Engineer", ["pytorch"], "Train models"))
    raw["ai_score"] = 31
    guarded = p.post_score_guard([raw])
    assert guarded[0]["ai_score"] == 50


def test_incidental_ai_generic_job_is_capped(tmp_path):
    p = pipeline(tmp_path)
    raw = norm(p, job("9", "Backend Developer", ["node.js"], "Integrate one AI API"))
    raw["ai_score"] = 80
    guarded = p.post_score_guard([raw])
    assert guarded[0]["ai_score"] <= 49


def test_rank_prefers_fit_score(tmp_path):
    p = pipeline(tmp_path)
    a = {"ai_score": 90, "ai_signal_count": 2, "days_old": 7}
    b = {"ai_score": 70, "ai_signal_count": 8, "days_old": 0}
    assert p.rank([b, a])[0] is a
