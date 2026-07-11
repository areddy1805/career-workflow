import json
import os
import re
import requests


class JobFilterPipeline2:

    # ── your stack — AI scores against this ──────────────────────────────────
    MY_STACK = [
        # ── Core backend ──────────────────────────────────────────────
        "node",
        "node.js",
        "nodejs",
        "python",
        "javascript",
        "typescript",
        "angular",
        "rxjs",
        "html",
        "css",
        # ── Frameworks ───────────────────────────────────────────────
        "express",
        "express.js",
        "fastapi",
        "flask",
        "nestjs",
        "nest.js",
        "django",
        "hapi",
        "koa",
        # ── Databases ────────────────────────────────────────────────
        "mongodb",
        "mongoose",
        "postgresql",
        "mysql",
        "redis",
        "sqlite",
        "dynamodb",
        "firestore",
        "cassandra",
        "elasticsearch",
        "sql",
        "nosql",
        # ── Cloud & DevOps ───────────────────────────────────────────
        "aws",
        "gcp",
        "azure",
        "docker",
        "kubernetes",
        "ci/cd",
        "github actions",
        "jenkins",
        "terraform",
        "linux",
        "nginx",
        "ec2",
        "s3",
        "lambda",
        "cloudwatch",
        # ── APIs & Messaging ─────────────────────────────────────────
        "rest",
        "rest api",
        "restful",
        "graphql",
        "websocket",
        "grpc",
        "kafka",
        "rabbitmq",
        "celery",
        "bull",
        "socket.io",
        # ── Automation & Scraping ────────────────────────────────────
        "selenium",
        "playwright",
        "puppeteer",
        "beautifulsoup",
        "scrapy",
        "web scraping",
        "automation",
        "n8n",
        "trigger.dev",
        "zapier",
        # ── AI / LLM ─────────────────────────────────────────────────
        "langchain",
        "openai",
        "llm",
        "rag",
        "vector db",
        "pinecone",
        "weaviate",
        "chromadb",
        "huggingface",
        "embeddings",
        "genai",
        "langsmith",
        "llamaindex",
        "langgraph",
        "semantic kernel",
        "azure openai",
        "azure ai search",
        "agentic ai",
        "tool calling",
        "llm evaluation",
        # ── Tools & Practices ────────────────────────────────────────
        "git",
        "github",
        "postman",
        "swagger",
        "jwt",
        "oauth",
        "microservices",
        "system design",
        "api design",
    ]

    PRIMARY_STACK_CONFLICTS = {
        "java developer": {
            "java",
            "spring",
            "spring boot",
            "hibernate",
        },
        ".net developer": {
            ".net",
            "c#",
            "asp.net",
            "dotnet",
        },
        "vba automation": {
            "vba",
            "advanced excel",
            "power query",
            "excel macros",
        },
        "ml research": {
            "tensorflow",
            "pytorch",
            "deep learning",
            "computer vision",
            "linear algebra",
            "model training",
        },
    }

    # ── hard veto BEFORE ai — title only, zero ambiguity ────────────────────
    # Hard veto only unmistakably non-target employment formats / non-engineering roles.
    # AI/ML/Data Science/CV/model-training titles are deliberately NOT vetoed.
    VETO_TITLES = [
        "walk-in",
        "walkin",
        "walk in",
        "tutor",
        "trainer",
        "sales executive",
        "business development executive",
        "recruiter",
        "talent acquisition",
    ]

    # Broad-coverage policy: company name never decides AI eligibility.
    VETO_COMPANIES = set()

    # ── red flag sniff on description (cheap, pre-ai) ───────────────────────
    # Only the things AI genuinely can't infer from tags alone
    DESC_RED_FLAGS = {
        "walk-in": r"walk.?in|walkin",
        "venue listed": r"venue\s*:|interview venue|bring your resume|carry your resume",
    }

    SOFTWARE_KEYWORDS = {
        "software",
        "developer",
        "engineer",
        "engineering",
        "backend",
        "full stack",
        "fullstack",
        "python",
        "node",
        "nodejs",
        "javascript",
        "typescript",
        "django",
        "fastapi",
        "flask",
        "golang",
        "devops",
        "cloud",
        "sre",
        "platform",
        "api",
        "microservices",
        "infrastructure",
        "tech lead",
        "sde",
        "swe",
        "mts",
        "programmer",
        "react",
    }

    # if ANY of these appear in title → drop it
    # Only obvious non-software/non-AI tracks. Stack and AI sub-discipline are ranking signals.
    WRONG_TRACK_TITLE_KEYWORDS = {
        "android developer",
        "ios developer",
        "flutter developer",
        "site reliability engineer",
        "sre engineer",
        "devops engineer",
    }

    # Backward-compatible alias for callers/tests that inspect the old name.
    FRONTEND_VETO_KEYWORDS = WRONG_TRACK_TITLE_KEYWORDS

    # =========================================================
    # AI RELEVANCE GATE
    # =========================================================

    STRONG_AI_SIGNALS = {
        "generative ai",
        "genai",
        "gen ai",
        "large language model",
        "large language models",
        "llm",
        "llms",
        "rag",
        "retrieval augmented generation",
        "langchain",
        "langgraph",
        "llamaindex",
        "semantic kernel",
        "azure openai",
        "openai api",
        "vector database",
        "vector db",
        "vector search",
        "embeddings",
        "prompt engineering",
        "agentic ai",
        "ai agent",
        "ai agents",
        "multi-agent",
        "autogen",
        "crewai",
    }

    MEDIUM_AI_SIGNALS = {
        "artificial intelligence",
        "natural language processing",
        "nlp",
        "machine learning",
        "hugging face",
        "huggingface",
        "transformers",
        "transformer models",
        "foundation models",
        "language models",
        "chatbot",
        "conversational ai",
        "ai application",
        "ai applications",
        "ai integration",
        "ai platform",
    }

    AI_TITLE_SIGNALS = {
        "ai engineer",
        "artificial intelligence engineer",
        "generative ai engineer",
        "genai engineer",
        "gen ai engineer",
        "llm engineer",
        "llm operations engineer",
        "llm model developer",
        "rag engineer",
        "ai developer",
        "genai developer",
        "ai application developer",
        "applied ai engineer",
        "ai software engineer",
        "ai backend developer",
        "python ai developer",
        "ai/ml engineer",
        "ai ml engineer",
        "machine learning engineer",
        "ml engineer",
        "data scientist",
        "computer vision engineer",
        "deep learning engineer",
        "nlp engineer",
        "prompt engineer",
        "ml scientist",
        "applied scientist",
        "mlops engineer",
        "llmops engineer",
        "ai lead",
        "ai architect",
        "ai full stack engineer",
        "full stack ai engineer",
        "fullstack ai engineer",
    }

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        cache_file: str = "data/score_cache.json",
        daily_apply_limit: int = 50,
        min_apply_score: int = 50,
        ai_score_limit: int = 300,
        batch_size: int = 5,
    ):
        self.api_key = api_key or os.getenv("OMLX_API_KEY")

        if not self.api_key:
            raise ValueError("OMLX_API_KEY is not configured")

        self.base_url = (
            base_url or os.getenv("OMLX_BASE_URL") or "http://127.0.0.1:8000/v1"
        ).rstrip("/")

        self.model = model or os.getenv("OMLX_MODEL") or "qwen3.5-4b"

        self.url = f"{self.base_url}/chat/completions"

        self.cache_file = cache_file
        self.daily_apply_limit = daily_apply_limit
        self.min_apply_score = min_apply_score
        self.ai_score_limit = ai_score_limit
        self.batch_size = batch_size
        self.cache = self._load_cache()

    # =========================================================
    # MAIN
    # =========================================================

    def pre_filter(self, jobs):
        """
        Cheap deterministic filtering before full job-detail enrichment.
        """

        print("\nRAW JOBS:", len(jobs))

        jobs = self.normalize_jobs(jobs)
        print("AFTER NORMALIZE:", len(jobs))

        jobs = self.dedup(jobs)
        print("AFTER DEDUP:", len(jobs))

        jobs = self.hard_veto(jobs)
        print("AFTER HARD VETO:", len(jobs))

        # Experience is ranking-only; never reject locally.
        # jobs = self.experience_filter(jobs)
        print("AFTER EXP FILTER:", len(jobs))

        jobs = self.desc_red_flag_check(jobs)
        print("AFTER RED FLAG CHECK:", len(jobs))

        jobs = self.title_filter(jobs)
        print("AFTER TITLE FILTER:", len(jobs))

        # Company is not an application eligibility gate.
        # jobs = self.company_veto(jobs)
        print("AFTER COMPANY VETO:", len(jobs))

        jobs = self.ai_relevance_gate(jobs)
        print("AFTER AI RELEVANCE GATE:", len(jobs))

        # Stack mismatch is a ranking signal, never an eligibility veto.
        jobs = self.tag_presort(jobs)

        jobs = jobs[: self.ai_score_limit]
        print("AFTER LIMIT:", len(jobs))

        return jobs

    def score_and_select(self, jobs):
        """
        Final classification after full-JD enrichment.

        Order:
        1. Full-JD red flags
        2. Full-JD primary stack conflicts
        3. AI scoring
        4. Deterministic post-score enforcement
        5. Rank and select
        """

        jobs = self.full_description_red_flag_check(jobs)
        print("AFTER FULL JD RED FLAG CHECK:", len(jobs))

        jobs = self.location_work_mode_gate(jobs)
        print("AFTER LOCATION / WORK-MODE GATE:", len(jobs))

        jobs = self.ai_score_batch(jobs)

        jobs = self.post_score_guard(jobs)
        print("AFTER POST-SCORE GUARD:", len(jobs))

        jobs = self.rank(jobs)
        print("AFTER RANK:", len(jobs))

        jobs = self.select(jobs)
        print("FINAL SELECTED:", len(jobs))

        for j in jobs:
            print(
                f"  {j.get('ai_score'):>3}  "
                f"{j.get('title')} @ {j.get('company')}"
                f"  |  {j.get('ai_reason', '')}"
            )

        return jobs

    def run(self, jobs):
        """
        Compatibility wrapper for tests and existing callers.

        Production orchestration should use:
            pre_filter()
            enrichment
            score_and_select()
        """

        candidates = self.pre_filter(jobs)

        return self.score_and_select(candidates)

    # =========================================================
    # NORMALIZE  — tags are the star, keep them clean
    # =========================================================
    def normalize_jobs(self, jobs):
        normalized = []

        for j in jobs:
            job = j if isinstance(j, dict) else j.__dict__

            # days old
            posted = (job.get("posted_date") or "").lower()
            days_old = 7
            if "today" in posted or "hour" in posted or "just now" in posted:
                days_old = 0
            elif "yesterday" in posted:
                days_old = 1
            else:
                m = re.search(r"(\d+)\s*day", posted)
                if m:
                    days_old = int(m.group(1))
                else:
                    m = re.search(r"(\d+)\s*week", posted)
                    if m:
                        days_old = int(m.group(1)) * 7

            # experience range
            exp = job.get("experience") or ""
            exp_min, exp_max = 0, 10
            nums = re.findall(r"\d+", exp)
            if len(nums) >= 2:
                exp_min, exp_max = int(nums[0]), int(nums[1])
            elif len(nums) == 1:
                exp_min = exp_max = int(nums[0])

            # tags — normalize once, use everywhere
            raw_tags = job.get("tags") or job.get("skills") or []
            if isinstance(raw_tags, str):
                raw_tags = re.split(r"[,;|]", raw_tags)
            tags = [t.strip().lower() for t in raw_tags if t.strip()]

            normalized.append(
                {
                    "job_id": job.get("job_id"),
                    "title": (job.get("title") or "").strip(),
                    "company": (job.get("company") or "").strip(),
                    "location": (job.get("location") or "").strip(),
                    "description": (job.get("description") or "").strip(),
                    "tags": tags,
                    "mandatory_tags": tags[:2],
                    "optional_tags": tags[2:],
                    "days_old": days_old,
                    "experience_min": exp_min,
                    "experience_max": exp_max,
                    "search_track": (job.get("search_track") or "UNKNOWN"),
                    "search_query": (job.get("search_query") or ""),
                }
            )

        return normalized

    # =========================================================
    # DEDUP
    # =========================================================
    def dedup(self, jobs):
        seen, result = set(), []
        for j in jobs:
            job_id = j.get("job_id")
            if job_id is None:
                result.append(j)  # can't dedup without an id, just keep it
                continue
            if job_id in seen:
                continue
            seen.add(job_id)
            result.append(j)
        return result

    # =========================================================
    # HARD VETO  — title only, no ambiguity allowed
    # =========================================================
    def hard_veto(self, jobs):
        clean = []
        for j in jobs:
            title = (j.get("title") or "").lower()
            if any(kw in title for kw in self.VETO_TITLES):
                print(f"  [VETO] {j.get('title')}")
                continue
            clean.append(j)
        return clean

    # =========================================================
    # EXPERIENCE FILTER
    # =========================================================
    def experience_filter(self, jobs):
        """
        Keep roles that are plausible for the candidate's overall engineering
        seniority. Do not equate years of Applied-AI work with total software
        experience: the candidate has a senior full-stack foundation and a
        newer Applied-AI specialization.

        Reject only clearly junior-only roles and roles whose minimum
        experience is beyond a credible transition range.
        """
        clean = []

        for job in jobs:
            title = (job.get("title") or "").lower()
            exp_min = int(job.get("experience_min", 0) or 0)
            exp_max = int(job.get("experience_max", 10) or 10)

            junior_only = (
                any(
                    token in title
                    for token in ("intern", "internship", "graduate trainee", "fresher")
                )
                or exp_max == 0
            )

            too_senior = exp_min >= 10 or any(
                token in title
                for token in (
                    "vice president",
                    "vp of",
                    "head of engineering",
                    "head of technology",
                    "chief technology officer",
                    "cto",
                )
            )

            if junior_only or too_senior:
                continue

            clean.append(job)

        return clean

    # =========================================================
    # DESC RED FLAG CHECK  — one cheap regex pass, nothing more
    # =========================================================
    def desc_red_flag_check(self, jobs):
        clean = []
        for j in jobs:
            desc = (j.get("description") or "").lower()
            flagged = [
                label
                for label, pat in self.DESC_RED_FLAGS.items()
                if re.search(pat, desc)
            ]
            if flagged:
                print(f"  [RED FLAG {flagged}] {j.get('title')}")
                continue
            clean.append(j)
        return clean

    def full_description_red_flag_check(self, jobs):
        """
        Re-run description safety checks against the enriched full JD.

        Search-result descriptions may be empty or abbreviated, so the same
        checks are applied again after detail enrichment.
        """

        clean = []

        for job in jobs:
            desc = (job.get("description") or "").lower()

            flagged = [
                label
                for label, pattern in self.DESC_RED_FLAGS.items()
                if re.search(pattern, desc)
            ]

            if flagged:
                print(
                    f"  [FULL JD RED FLAG {flagged}] "
                    f"{job.get('title')} @ "
                    f"{job.get('company')}"
                )
                continue

            clean.append(job)

        return clean

    # =========================================================
    # TAG PRESORT  — rough stack overlap count, no AI cost
    # Keeps best candidates at the front before we hit the limit
    # =========================================================

    def title_filter(self, jobs):
        result = []

        for job in jobs:
            title = (job.get("title") or "").lower()

            explicit_ai_title = any(signal in title for signal in self.AI_TITLE_SIGNALS)

            if not explicit_ai_title and not any(
                keyword in title for keyword in self.SOFTWARE_KEYWORDS
            ):
                print(f"  [TITLE FILTER - not software/AI] {job.get('title')}")
                continue

            if not explicit_ai_title and any(
                keyword in title for keyword in self.WRONG_TRACK_TITLE_KEYWORDS
            ):
                print(f"  [TITLE FILTER - wrong track] {job.get('title')}")
                continue

            result.append(job)

        return result

    def company_veto(self, jobs):
        clean = []
        for j in jobs:
            company = (j.get("company") or "").lower()
            if any(vc in company for vc in self.VETO_COMPANIES):
                print(f"  [COMPANY VETO] {j.get('title')} @ {j.get('company')}")
                continue
            clean.append(j)
        return clean

    def ai_relevance_gate(self, jobs):
        """
        Keep Applied-AI roles and AI-enabled software roles.

        Generic backend/full-stack/frontend overlap is not enough. Conversely,
        Angular or full-stack work is not a negative when the JD contains
        concrete LLM/RAG/agent/application-AI responsibilities.
        """
        relevant = []

        for job in jobs:
            title = (job.get("title") or "").lower()
            tags_text = " ".join(job.get("tags") or []).lower()
            description = (job.get("description") or "").lower()
            searchable_text = " ".join((title, tags_text, description))

            title_hits = sorted(
                signal for signal in self.AI_TITLE_SIGNALS if signal in title
            )
            strong_hits = sorted(
                signal for signal in self.STRONG_AI_SIGNALS if signal in searchable_text
            )
            medium_hits = sorted(
                signal for signal in self.MEDIUM_AI_SIGNALS if signal in searchable_text
            )

            explicit_ai_title = bool(title_hits)
            concrete_ai_work = len(strong_hits) >= 1
            broad_ai_evidence = len(medium_hits) >= 2

            if explicit_ai_title:
                relevance_reason = f"AI title signal: {title_hits[0]}"
            elif concrete_ai_work:
                relevance_reason = f"Strong AI signal: {strong_hits[0]}"
            elif broad_ai_evidence:
                relevance_reason = "Multiple AI signals: " + ", ".join(medium_hits[:3])
            else:
                print(
                    f"  [AI RELEVANCE REJECT] "
                    f"{job.get('title')} @ {job.get('company')}"
                )
                continue

            job["ai_relevance"] = True
            job["ai_relevance_reason"] = relevance_reason
            job["ai_signal_count"] = (
                len(title_hits) + len(strong_hits) + len(medium_hits)
            )
            relevant.append(job)

        return relevant

    def primary_stack_conflict_filter(
        self,
        jobs,
        use_full_description=False,
    ):
        """
        Compatibility hook. Broad AI coverage policy never rejects a genuine
        AI job because of Java/C++/.NET/CV/ML/Data-Science stack differences.
        Those differences are handled by scoring and ranking only.
        """
        return list(jobs)

    @staticmethod
    def _classify_work_mode(job):
        structured = " ".join(
            str(job.get(key) or "")
            for key in ("work_mode", "workMode")
        ).lower().strip()

        if structured:
            if re.search(r"\b(remote|wfh|work from home)\b", structured):
                return "remote"
            if re.search(r"\bhybrid\b", structured):
                return "hybrid"
            if re.search(r"\b(office|onsite|on-site|wfo)\b", structured):
                return "office"

        location = str(job.get("location") or "").lower().strip()
        description = str(job.get("description") or "").lower()
        text = f"{location} {description}"

        negative_remote = (
            r"\bnot remote\b",
            r"\bno remote (?:work|working|option)\b",
            r"\bremote (?:work|working) (?:is )?not available\b",
            r"\bno work[- ]from[- ]home\b",
            r"\bwfh (?:is )?not available\b",
            r"\bmust relocate\b",
        )
        hybrid_signals = (
            r"\bhybrid (?:role|position|work|working|model|mode)\b",
            r"\bhybrid\b",
        )
        office_signals = (
            r"\bwork[- ]from[- ]office\b",
            r"\bwfo\b",
            r"\bon[- ]site\b",
            r"\bin[- ]office\b",
            r"\boffice[- ]based\b",
        )
        remote_signals = (
            r"\bfully remote\b",
            r"\b100% remote\b",
            r"\bremote (?:role|position|job|work|working)\b",
            r"\bwork remotely\b",
            r"\bwork[- ]from[- ]home\b",
            r"\bwfh\b",
            r"\blocation independent\b",
            r"\bwork from anywhere\b",
        )

        if any(re.search(pattern, text) for pattern in negative_remote):
            if any(re.search(pattern, text) for pattern in hybrid_signals):
                return "hybrid"
            if any(re.search(pattern, text) for pattern in office_signals):
                return "office"
            return "office"

        if any(re.search(pattern, text) for pattern in hybrid_signals):
            return "hybrid"

        if any(re.search(pattern, text) for pattern in office_signals):
            return "office"

        # Location metadata may legitimately be exactly "Remote",
        # "Remote - India", or "India - Remote". Keep this inference
        # isolated from description text so phrases such as
        # "remote sensing" are not treated as work-mode evidence.
        if re.search(r"\bremote\b", location):
            return "remote"

        if any(re.search(pattern, text) for pattern in remote_signals):
            return "remote"

        return "unknown"

    @staticmethod
    def _is_pune_location(job):
        pune_pattern = r"\bpune\b|\bpimpri\b|\bchinchwad\b|\bhinja?wadi\b"

        location = str(job.get("location") or "").lower()
        if re.search(pune_pattern, location):
            return True

        description = str(job.get("description") or "").lower()
        explicit_location_patterns = (
            rf"\b(?:job|work|base|office) location\s*[:\-]\s*[^.\n]{{0,100}}(?:{pune_pattern})",
            rf"\bbased in\s+(?:{pune_pattern})",
            rf"\bposition is based in\s+(?:{pune_pattern})",
        )
        return any(
            re.search(pattern, description) for pattern in explicit_location_patterns
        )

    def location_work_mode_gate(self, jobs):
        """
        Hard location/work-mode policy:

        - remote/WFH: eligible worldwide;
        - office/hybrid: eligible only when Pune is explicitly present;
        - unknown mode: eligible only when Pune is explicitly present.

        This is the only hard job-selection gate.
        """
        eligible = []

        for job in jobs:
            mode = self._classify_work_mode(job)
            location = (job.get("location") or "").strip()
            is_pune = self._is_pune_location(job)

            job["work_mode_classification"] = mode
            job["is_pune_location"] = is_pune

            if mode == "remote":
                eligible.append(job)
                continue

            if mode in {"office", "hybrid"}:
                if is_pune:
                    eligible.append(job)
                else:
                    print(
                        f"  [LOCATION REJECT - {mode}] "
                        f"{job.get('title')} @ {job.get('company')} | {location}"
                    )
                continue

            if is_pune:
                eligible.append(job)
            else:
                print(
                    "  [LOCATION REJECT - unknown-mode-non-pune] "
                    f"{job.get('title')} @ {job.get('company')} | {location}"
                )

        return eligible

    def tag_presort(self, jobs):
        my_stack = set(self.MY_STACK)

        def overlap(j):
            tags = set(j.get("tags", []))
            mandatory_hit = sum(1 for t in j.get("mandatory_tags", []) if t in my_stack)
            total_hit = len(tags & my_stack)
            recency_bonus = max(0, 7 - j.get("days_old", 7))
            # mandatory tags weighted 3x — they represent the job's core ask
            return mandatory_hit * 3 + total_hit + recency_bonus

        return sorted(jobs, key=overlap, reverse=True)

    def _job_text(self, job):
        return " ".join(
            [
                (job.get("title") or "").lower(),
                " ".join(job.get("mandatory_tags") or []).lower(),
                " ".join(job.get("optional_tags") or []).lower(),
                " ".join(job.get("tags") or []).lower(),
                (job.get("description") or "").lower(),
            ]
        )

    def _fit_features(self, job):
        text = self._job_text(job)
        title = (job.get("title") or "").lower()

        applied_ai_terms = (
            "generative ai",
            "genai",
            "large language model",
            "llm",
            "rag",
            "retrieval augmented generation",
            "langchain",
            "langgraph",
            "llamaindex",
            "semantic kernel",
            "azure openai",
            "openai api",
            "vector database",
            "vector db",
            "vector search",
            "embedding",
            "agentic ai",
            "ai agent",
            "tool calling",
            "function calling",
            "prompt engineering",
            "llm evaluation",
        )
        backend_terms = (
            "python",
            "fastapi",
            "flask",
            "node.js",
            "nodejs",
            "express",
            "rest api",
            "microservices",
            "mongodb",
            "postgresql",
            "docker",
            "azure",
            "aws",
        )
        frontend_terms = (
            "angular",
            "typescript",
            "rxjs",
            "frontend",
            "front-end",
            "full stack",
            "fullstack",
        )
        research_terms = (
            "research scientist",
            "applied research",
            "publish papers",
            "publication record",
            "phd required",
            "train foundation models",
            "train deep learning models",
            "training neural networks",
            "novel architectures",
            "computer vision research",
        )
        ml_core_terms = (
            "tensorflow",
            "pytorch",
            "scikit-learn",
            "feature engineering",
            "model training",
            "hyperparameter tuning",
            "deep learning",
            "computer vision",
        )

        return {
            "ai_hits": sum(term in text for term in applied_ai_terms),
            "backend_hits": sum(term in text for term in backend_terms),
            "frontend_hits": sum(term in text for term in frontend_terms),
            "research_hits": sum(term in text for term in research_terms),
            "ml_core_hits": sum(term in text for term in ml_core_terms),
            "ai_title": any(signal in title for signal in self.AI_TITLE_SIGNALS),
            "fullstack_title": any(
                term in title
                for term in ("full stack", "fullstack", "software engineer")
            ),
        }

    def _calibrate_score(self, job, raw_score):
        """
        Bound model variance with deterministic evidence bands.

        The LLM judges semantic fit inside a band; deterministic evidence
        prevents generic AI mentions from outranking direct Applied-AI roles.
        """
        score = max(0, min(100, int(raw_score)))
        f = self._fit_features(job)

        if f["research_hits"] >= 2 and f["ai_hits"] == 0:
            return min(score, 25)

        if f["ml_core_hits"] >= 3 and f["ai_hits"] <= 1:
            return min(score, 39)

        if f["ai_hits"] >= 4 and (f["backend_hits"] >= 2 or f["ai_title"]):
            return max(score, 78)

        if f["ai_hits"] >= 2 and f["backend_hits"] >= 2:
            return max(score, 72)

        if f["ai_hits"] >= 2 and (f["backend_hits"] >= 1 or f["frontend_hits"] >= 1):
            return max(score, 65)

        if f["ai_hits"] == 1 and not f["ai_title"]:
            return min(score, 59)

        return score

    # =========================================================
    # AI SCORING  — tags go in, score + reason come out
    # =========================================================
    def ai_score_batch(self, jobs):
        result = []

        for i in range(
            0,
            len(jobs),
            self.batch_size,
        ):
            batch = jobs[i : i + self.batch_size]

            uncached_jobs = []

            for job in batch:
                jid = str(job.get("job_id") or "").strip()

                if jid and jid in self.cache:
                    cached = self.cache[jid]

                    job["ai_score"] = cached.get("score", 0)
                    job["ai_reason"] = cached.get(
                        "reason",
                        "cached",
                    )

                    result.append(job)

                else:
                    uncached_jobs.append(job)

            if not uncached_jobs:
                continue

            scores = self._call_ai(uncached_jobs)

            submitted_ids = {
                str(job.get("job_id") or "").strip()
                for job in uncached_jobs
                if str(job.get("job_id") or "").strip()
            }

            valid_scores = {}

            if isinstance(scores, list):
                for item in scores:
                    if not isinstance(item, dict):
                        continue

                    jid = str(item.get("job_id") or "").strip()

                    score = item.get("score")

                    if (
                        jid in submitted_ids
                        and jid not in valid_scores
                        and isinstance(score, int)
                    ):
                        valid_scores[jid] = item

            missing_jobs = []

            for job in uncached_jobs:
                jid = str(job.get("job_id") or "").strip()

                data = valid_scores.get(jid)

                if data is None:
                    missing_jobs.append(job)
                    continue

                normalized_data = {
                    "score": self._calibrate_score(
                        job,
                        data["score"],
                    ),
                    "reason": str(data.get("reason") or "").strip(),
                }

                job["ai_score"] = normalized_data["score"]
                job["ai_reason"] = normalized_data["reason"]

                if jid:
                    self.cache[jid] = normalized_data

                result.append(job)

            # Retry malformed or missing jobs individually.
            for job in missing_jobs:
                jid = str(job.get("job_id") or "").strip()

                print(
                    f"  [AI RETRY SINGLE] "
                    f"{job.get('title')} @ "
                    f"{job.get('company')}"
                )

                retry_data = self._call_ai([job])

                matched = None

                if isinstance(retry_data, list):
                    for item in retry_data:
                        if not isinstance(item, dict):
                            continue

                        if str(item.get("job_id") or "").strip() == jid and isinstance(
                            item.get("score"), int
                        ):
                            matched = item
                            break

                if matched is None:
                    print(
                        f"AI score unavailable after retry "
                        f"for job_id={jid or '<unknown>'}"
                    )

                    job["ai_score"] = 0
                    job["ai_reason"] = "AI scoring unavailable after retry"

                    result.append(job)
                    continue

                normalized_data = {
                    "score": self._calibrate_score(
                        job,
                        matched["score"],
                    ),
                    "reason": str(matched.get("reason") or "").strip(),
                }

                job["ai_score"] = normalized_data["score"]
                job["ai_reason"] = normalized_data["reason"]

                if jid:
                    self.cache[jid] = normalized_data

                result.append(job)

            self._save_cache()

        return result

    def _call_ai(self, jobs):
        job_block = ""
        for j in jobs:
            mandatory = ", ".join(j.get("mandatory_tags", [])) or "none"
            optional = ", ".join(j.get("optional_tags", [])) or "none"
            exp = f"{j.get('experience_min', 0)}-{j.get('experience_max', 10)} yrs"
            description = (j.get("description") or "").strip()

            description = description[:6000]

            job_block += (
                f"Job ID:      {j.get('job_id')}\n"
                f"  Title:       {j.get('title')}\n"
                f"  Company:     {j.get('company')}\n"
                f"  Mandatory:   {mandatory}\n"
                f"  Optional:    {optional}\n"
                f"  Exp:         {exp}\n"
                f"  Days old:    {j.get('days_old', 7)}\n"
                f"  Search track:{j.get('search_track', 'UNKNOWN')}\n"
                f"  AI evidence: {j.get('ai_relevance_reason', '')}\n"
                f"  Full JD:\n{description}\n"
                f"---\n"
            )

        prompt2 = f"""
You rank genuine AI jobs for this candidate. Eligibility is broad; ranking is preference.

Candidate ground-truth profile for matching:
- Senior software engineer with production full-stack/backend experience.
- Angular/TypeScript, Node.js/Express, REST APIs, MongoDB, service integration.
- Production AI engineering experience represented by Python/FastAPI AI services,
  RAG, hybrid retrieval, reranking, embeddings, vector search, LangChain/LangGraph,
  agents, tool calling, LLM evaluation, local model serving, Azure OpenAI,
  Azure AI Foundry, and Azure AI Search.

POLICY:
- Any genuinely AI-related engineering role is eligible.
- Do NOT reject or heavily punish a role merely because its primary stack is
  Java, C++, .NET, TensorFlow, PyTorch, computer vision, NLP, traditional ML,
  data science, model training, MLOps, or another AI sub-discipline.
- Stack and sub-discipline mismatch affect ranking only.
- Generic software jobs with only incidental AI wording should score below 50.
- Explicit AI roles should normally score at least 50.
- Prefer GenAI/LLM/RAG/Agentic roles, then Applied AI/NLP/Prompt/AI Full Stack,
  then ML/CV/DL/Data Science + AI, then ambiguous AI-adjacent roles.
- Evaluate against the stated candidate profile; do not describe the candidate
  as transitioning into AI or lacking production AI experience.

SCORING:
90-100: direct GenAI/LLM/RAG/agentic fit with strong stack overlap.
80-89: strong applied-AI fit.
70-79: genuine AI role with good transferable overlap.
60-69: genuine AI role with meaningful stack/sub-discipline gaps.
50-59: genuine AI role with substantial gaps but still worth applying.
0-49: not genuinely AI work, or AI is merely incidental.

OUTPUT CONTRACT:
Return exactly one result for every supplied Job ID. Copy IDs exactly.
No markdown or extra text. Integer score 0-100.

Return ONLY:
{{
  "results": [
    {{
      "job_id": "exact supplied id",
      "score": 82,
      "reason": "Specific evidence-based fit explanation."
    }}
  ]
}}

Jobs:
{job_block}
"""

        try:
            res = requests.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt2,
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000,
                    "response_format": {
                        "type": "json_object",
                    },
                    "chat_template_kwargs": {
                        "enable_thinking": False,
                    },
                },
                timeout=300,
            )

            if res.status_code != 200:
                print("AI HTTP ERROR:", res.status_code, res.text[:200])
                return []

            response_json = res.json()

            message = response_json["choices"][0]["message"]

            content = message.get("content") or ""

            content = re.sub(
                r"```json|```",
                "",
                content,
            ).strip()

            match = re.search(
                r"\{.*\}",
                content,
                re.S,
            )

            if not match:
                print(
                    "AI PARSE ERROR — no JSON object found\n"
                    f"finish_reason={response_json['choices'][0].get('finish_reason')}\n"
                    f"content={content[:1000]}"
                )

                return []

            json_text = match.group(0)

            try:
                data = json.loads(json_text)

            except json.JSONDecodeError as exc:
                print(
                    "AI JSON ERROR\n"
                    f"error={exc}\n"
                    f"finish_reason={response_json['choices'][0].get('finish_reason')}\n"
                    f"content={content[:1500]}"
                )

                return []

            if not isinstance(data, dict):
                return []

            results = data.get("results")

            if not isinstance(results, list):
                print("AI CONTRACT ERROR — " "'results' must be a list")
                return []

            return results

        except Exception as e:
            print("AI call error:", e)
            return []

    def post_score_guard(self, jobs):
        """
        Enforce deterministic consistency between job evidence and score.

        The model may refine ordering inside evidence bands, but it cannot:
        - promote incidental-AI generic software above direct AI work;
        - keep obvious VBA/content roles because the title contains AI;
        - leave concrete LLM/RAG/agentic backend roles below their evidence floor.
        """
        clean = []

        for job in jobs:
            features = self._fit_features(job)
            text = self._job_text(job)
            title = (job.get("title") or "").lower()
            score = int(job.get("ai_score", 0) or 0)

            vba_automation_hits = sum(
                term in text
                for term in (
                    "vba",
                    "excel macros",
                    "advanced excel",
                    "power query",
                    "macro automation",
                )
            )
            content_role_hits = sum(
                term in text
                for term in (
                    "copywriter",
                    "copywriting",
                    "brand copy",
                    "marketing copy",
                    "content writer",
                    "social media content",
                )
            )
            engineering_hits = features["backend_hits"] + features["ai_hits"]

            # Misleading AI titles: the actual work is office automation or content.
            if vba_automation_hits >= 2 and features["ai_hits"] <= 1:
                print(
                    f"  [POST-SCORE REJECT - INCIDENTAL AUTOMATION] "
                    f"{job.get('title')} @ {job.get('company')}"
                )
                continue

            if content_role_hits >= 2 and engineering_hits <= 2:
                print(
                    f"  [POST-SCORE REJECT - NON-ENGINEERING AI] "
                    f"{job.get('title')} @ {job.get('company')}"
                )
                continue

            # Generic software with one weak AI mention stays below application floor.
            if features["ai_hits"] <= 1 and not features["ai_title"]:
                score = min(score, 49)

            # Concrete applied-AI backend work gets deterministic floors even when
            # the title is generic (for example an agentic manufacturing platform).
            if features["ai_hits"] >= 4 and (
                features["backend_hits"] >= 2 or features["ai_title"]
            ):
                score = max(score, 78)
            elif features["ai_hits"] >= 2 and features["backend_hits"] >= 2:
                score = max(score, 72)
            elif features["ai_hits"] >= 2 and (
                features["backend_hits"] >= 1 or features["frontend_hits"] >= 1
            ):
                score = max(score, 65)

            # Explicit AI engineering titles remain eligible, but only after the
            # misleading-title rejection rules above have run.
            if features["ai_title"]:
                score = max(score, self.min_apply_score)

            job["ai_score"] = max(0, min(100, score))
            clean.append(job)

        return clean

    # =========================================================
    # RANK  — ai score + small recency bump
    # =========================================================
    def rank(self, jobs):
        return sorted(
            jobs,
            key=lambda job: (
                job.get("ai_score", 0),
                job.get("ai_signal_count", 0),
                -job.get("days_old", 7),
            ),
            reverse=True,
        )

    # =========================================================
    # SELECT
    # =========================================================
    def select(self, jobs):
        """
        Every job reaching this stage has already passed the hard-veto,
        genuine-AI relevance, and location/work-mode eligibility gates.

        AI score controls ordering only; it is not an eligibility threshold.
        """
        return jobs[: self.daily_apply_limit]

    # =========================================================
    # CACHE
    # =========================================================
    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file) as f:
                    data = json.load(f)

                return data if isinstance(data, dict) else {}

            except Exception:
                return {}

        return {}

    def _save_cache(self):
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f, indent=2)
