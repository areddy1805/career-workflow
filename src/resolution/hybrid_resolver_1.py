from dataclasses import dataclass
from typing import Any

from src.llm.question_resolver import LLMQuestionResolver
from src.utils.questionnaire_resolver import (
    resolve_answer,
    serialize_answer,
)


@dataclass
class HybridResolution:
    status: str
    source: str
    semantic_answer: Any = None
    serialized_answer: Any = None
    confidence: float | None = None
    reasoning: str | None = None

    @property
    def resolved(self) -> bool:
        return self.status == "resolved"


class HybridQuestionResolver:
    """
    Resolution order:

        deterministic resolver
                ↓ unresolved
        LLM fallback
                ↓
        LLM safety gate
                ↓
        questionnaire serialization
                ↓
        resolved OR manual review

    The LLM never overrides a deterministic answer.
    """

    def __init__(
        self,
        llm_resolver: LLMQuestionResolver | None = None,
    ):
        self.llm_resolver = (
            llm_resolver
            or LLMQuestionResolver()
        )

    def resolve(
        self,
        question: dict,
        profile: dict,
    ) -> HybridResolution:
        # ==============================================================
        # Layer 1: deterministic resolver
        # ==============================================================

        deterministic_value = resolve_answer(
            question=question,
            profile=profile,
        )

        if deterministic_value is not None:
            serialized = serialize_answer(
                question=question,
                semantic_value=deterministic_value,
            )

            if serialized is not None:
                return HybridResolution(
                    status="resolved",
                    source="deterministic",
                    semantic_answer=deterministic_value,
                    serialized_answer=serialized,
                    confidence=1.0,
                    reasoning="Resolved by deterministic questionnaire rules.",
                )

            return HybridResolution(
                status="manual_review",
                source="deterministic_serialization_failure",
                semantic_answer=deterministic_value,
                serialized_answer=None,
                confidence=1.0,
                reasoning=(
                    "Deterministic resolver produced a semantic answer, "
                    "but it could not be safely mapped to the questionnaire "
                    "answer format."
                ),
            )

        # ==============================================================
        # Layer 2: LLM fallback
        # ==============================================================

        try:
            decision = self.llm_resolver.resolve(
                question=question,
                profile=profile,
            )

        except Exception as exc:
            return HybridResolution(
                status="manual_review",
                source="llm_error",
                semantic_answer=None,
                serialized_answer=None,
                confidence=0.0,
                reasoning=f"LLM fallback failed: {type(exc).__name__}: {exc}",
            )

        # ==============================================================
        # Layer 3: LLM policy/confidence gate
        # ==============================================================

        if not decision.is_safe_to_auto_answer():
            return HybridResolution(
                status="manual_review",
                source="llm_abstain",
                semantic_answer=decision.semantic_answer,
                serialized_answer=None,
                confidence=decision.confidence,
                reasoning=decision.reasoning,
            )

        if decision.semantic_answer is None:
            return HybridResolution(
                status="manual_review",
                source="llm_empty_answer",
                semantic_answer=None,
                serialized_answer=None,
                confidence=decision.confidence,
                reasoning=(
                    "LLM marked the question answerable but returned "
                    "no semantic answer."
                ),
            )

        # ==============================================================
        # Layer 4: serialization validation
        # ==============================================================

        serialized = serialize_answer(
            question=question,
            semantic_value=decision.semantic_answer,
        )

        if serialized is None:
            return HybridResolution(
                status="manual_review",
                source="llm_serialization_failure",
                semantic_answer=decision.semantic_answer,
                serialized_answer=None,
                confidence=decision.confidence,
                reasoning=(
                    f"{decision.reasoning} "
                    "The semantic answer could not be safely mapped to "
                    "the questionnaire answer format."
                ),
            )

        # ==============================================================
        # Layer 5: accepted LLM answer
        # ==============================================================

        return HybridResolution(
            status="resolved",
            source="llm",
            semantic_answer=decision.semantic_answer,
            serialized_answer=serialized,
            confidence=decision.confidence,
            reasoning=decision.reasoning,
        )
