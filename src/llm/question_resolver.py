import json
from typing import Any

from src.llm.client import OMLXClient
from src.llm.schemas import LLMQuestionDecision

SYSTEM_PROMPT = """
You are a decision component inside an automated job application system.

Your task is to analyze ONE recruiter questionnaire question and return a strict JSON decision.

The deterministic rule engine has already failed to resolve this question.

You must classify the question and decide whether it is safe to answer automatically.

Allowed categories:
- capability
- experience
- relocation
- interview_availability
- work_arrangement
- employment_type
- notice_period
- compensation
- location
- descriptive
- sensitive
- unknown

Allowed actions:
- answer
- manual_review

Rules:

1. Capability questions asking whether the candidate has used, built, deployed,
   implemented, designed, or worked with a technology may be answered "Yes".

2. Experience questions asking for years of experience should be answered "2"
   when no more specific deterministic profile value is available.

3. Relocation questions may be answered "Yes".

4. Interview availability questions may be answered "Yes".

5. Questions about willingness to attend interviews, assessments, coding tests,
   HackerRank tests, face-to-face rounds, weekend drives, or hiring events may
   be answered "Yes".

6. Questions about remote work, hybrid work, office visits, work from office,
   alternate Saturdays, shifts, or contract employment may be answered "Yes".

7. Questions requiring PAN number, Aadhaar number, passport number, exact home
   address, date of birth, bank details, tax identifiers, or other sensitive
   personal information must use action "manual_review".

8. Never invent app links, production metrics, user counts, ROI figures,
   employer names, dates, addresses, certifications, or project facts.

9. Descriptive technical questions may only be answered when sufficient
   candidate context is explicitly supplied.

10. If uncertain, use action "manual_review".

11. Return JSON only. No markdown. No explanation outside JSON.

EVIDENCE BOUNDARY RULES:

1. Never infer production deployment duration from general technology experience.
   Example:
   - "3 years of GenAI experience" does NOT mean "3 years deployed in production".
   - "3 years of RAG experience" does NOT mean a RAG system has been in production for 3 years.

2. Never infer production user counts, traffic, scale, latency, ROI, revenue impact,
   cost savings, uptime, SLA, business metrics, or deployment duration from general
   experience fields.

3. Questions asking for exact production facts require explicit matching evidence in
   the candidate context. If exact matching evidence is absent:
   action = "manual_review"
   semantic_answer = null

4. Distinguish carefully between:
   - years of experience with a technology
   - duration of a specific system in production
   - number of production users
   - business impact or ROI
   These are separate facts and must never be substituted for one another.

5. Do not convert a broad experience value into an answer for a narrower factual claim.

6. For descriptive or factual questions, use only directly supported facts from the
   candidate context. If answering requires extrapolation, assumption, reinterpretation,
   or fabrication, return manual_review.

7. Confidence measures confidence that the answer is factually supported by the provided
   candidate context, not confidence that the answer sounds plausible.

Required JSON structure:

{
  "category": "capability",
  "action": "answer",
  "semantic_answer": "Yes",
  "confidence": 0.95,
  "reasoning": "Short explanation"
}
""".strip()


class LLMQuestionResolver:
    def __init__(
        self,
        client: OMLXClient | None = None,
        confidence_threshold: float = 0.85,
    ):
        self.client = client or OMLXClient()
        self.confidence_threshold = confidence_threshold

    def resolve(
        self,
        question: dict,
        profile: dict,
    ) -> LLMQuestionDecision:
        question_text = (
            question.get("questionName") or question.get("question") or ""
        ).strip()

        question_type = (
            question.get("questionType") or question.get("type") or ""
        ).strip()

        options = question.get("answerOption") or {}

        candidate_context = self._build_candidate_context(profile)

        user_prompt = f"""
Recruiter question:
{question_text}

Question type:
{question_type}

Available answer options:
{json.dumps(options, ensure_ascii=False)}

Candidate context:
{json.dumps(candidate_context, ensure_ascii=False)}

Return the JSON decision.
""".strip()

        raw_response = self.client.chat(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0.0,
            max_tokens=500,
        )

        decision = self._parse_decision(raw_response)

        if (
            decision.action == "answer"
            and decision.confidence < self.confidence_threshold
        ):
            return LLMQuestionDecision(
                category=decision.category,
                action="manual_review",
                semantic_answer=None,
                confidence=decision.confidence,
                reasoning=(
                    f"LLM confidence {decision.confidence:.2f} "
                    f"is below threshold "
                    f"{self.confidence_threshold:.2f}"
                ),
            )

        return decision

    def _parse_decision(
        self,
        raw_response: str,
    ) -> LLMQuestionDecision:
        cleaned = raw_response.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```json")
            cleaned = cleaned.removeprefix("```")
            cleaned = cleaned.removesuffix("```")
            cleaned = cleaned.strip()

        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            return LLMQuestionDecision(
                category="unknown",
                action="manual_review",
                semantic_answer=None,
                confidence=0.0,
                reasoning=f"Invalid JSON returned by LLM: {exc}",
            )

        try:
            return LLMQuestionDecision.model_validate(payload)
        except Exception as exc:
            return LLMQuestionDecision(
                category="unknown",
                action="manual_review",
                semantic_answer=None,
                confidence=0.0,
                reasoning=f"Invalid LLM decision schema: {exc}",
            )

    @staticmethod
    def _build_candidate_context(
        profile: dict,
    ) -> dict[str, Any]:
        allowed_keys = (
            "current_location",
            "preferred_location",
            "relocation_preferences",
            "notice_period_days",
            "current_ctc_lpa",
            "expected_ctc_lpa",
            "total_experience_years",
            "ai_experience_years",
            "genai_experience_years",
            "rag_experience_years",
            "llm_experience_years",
            "agentic_ai_experience_years",
            "machine_learning_experience_years",
            "python_experience_years",
            "azure_experience_years",
            "aws_experience_years",
            "cloud_experience_years",
            "vector_db_experience_years",
            "prompt_engineering_experience_years",
            "ai_evaluation_experience_years",
            "api_development_experience_years",
            "llm_frameworks",
            "vector_databases",
            "preferred_cloud_platform",
            "docker_usage",
            "genai_application_summary",
            "mlops_summary",
        )

        return {
            key: profile[key]
            for key in allowed_keys
            if key in profile and profile[key] not in (None, "")
        }
