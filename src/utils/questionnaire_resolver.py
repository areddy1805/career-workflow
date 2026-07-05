import re
from typing import Any


def resolve_answer(
    question: dict,
    profile: dict,
) -> str | None:
    """
    Resolve a questionnaire question into a semantic answer.

    This function returns human/profile values only.

    Examples:
        Python experience -> "3"
        Notice period      -> "30"
        Relocation         -> "Yes"
        Expected CTC INR   -> "2600000"

    Payload-specific conversion is handled separately by serialize_answer().
    """

    text = (question.get("questionName") or "").strip()
    q = text.lower()

    # ------------------------------------------------------------------
    # Compensation
    # ------------------------------------------------------------------

    if "expected" in q and ("ctc" in q or "salary" in q):
        if "inr" in q or "annual" in q:
            return str(profile["expected_ctc_inr"])

        return str(profile["expected_ctc_lpa"])

    if "current" in q and ("ctc" in q or "salary" in q):
        if "inr" in q or "annual" in q:
            return str(profile["current_ctc_inr"])

        return str(profile["current_ctc_lpa"])

    # ------------------------------------------------------------------
    # Notice period
    # ------------------------------------------------------------------

    if "notice period" in q:
        return str(profile["notice_period_days"])

    # ------------------------------------------------------------------
    # Total experience
    # ------------------------------------------------------------------

    if (
        "total years of experience" in q
        or "total year of experience" in q
        or "total experience" in q
        or "overall experience" in q
        or "overall years of experience" in q
    ):
        return str(profile["total_experience_years"])

    # ------------------------------------------------------------------
    # Specific skill experience
    #
    # Keep specific skills before broad AI matching.
    # ------------------------------------------------------------------

    if "python" in q and ("experience" in q or "exp" in q):
        return str(profile["python_experience_years"])

    if "typescript" in q and ("experience" in q or "exp" in q):
        return str(profile["typescript_experience_years"])

    if "angular" in q and ("experience" in q or "exp" in q):
        return str(profile["angular_experience_years"])

    if ("node.js" in q or "nodejs" in q or "node js" in q or "node" in q) and (
        "experience" in q or "exp" in q
    ):
        return str(profile["node_experience_years"])

    # ------------------------------------------------------------------
    # LLM experience
    # ------------------------------------------------------------------

    if "llm" in q and ("experience" in q or "exp" in q):
        return str(profile["llm_experience_years"])

    # ------------------------------------------------------------------
    # Generative AI experience
    # ------------------------------------------------------------------

    if ("generative ai" in q or "gen ai" in q or "genai" in q) and (
        "experience" in q or "exp" in q
    ):
        return str(profile["genai_experience_years"])

    # ------------------------------------------------------------------
    # Broad AI experience
    # ------------------------------------------------------------------

    if (
        "artificial intelligence" in q
        or "ai/ml" in q
        or "aiml" in q
        or "ai automation" in q
        or "intelligent ai assistant" in q
        or "intelligent ai assistants" in q
        or "gen ai application" in q
        or "genai application" in q
    ) and ("experience" in q or "exp" in q):
        return str(profile["genai_experience_years"])

    # ------------------------------------------------------------------
    # Location / relocation
    # ------------------------------------------------------------------

    if (
        "willing to relocate" in q
        or "ready to relocate" in q
        or "currently residing in pune" in q
        or "currently living in" in q
    ):
        return "Yes"

    # ------------------------------------------------------------------
    # Unknown question
    #
    # Never fabricate an answer.
    # Returning None sends the job to manual review.
    # ------------------------------------------------------------------

    return None


def serialize_answer(
    question: dict,
    semantic_value: Any,
) -> Any:
    """
    Convert a semantic answer into the exact payload representation
    expected by the apply workflow.

    Examples:

        Text Box:
            semantic: "2600000"
            payload:  "2600000"

        Radio Button:
            semantic: "3"
            matched option: "<4 years"
            payload: ["2"]

        Checkbox / Multi Select:
            semantic: ["Python", "Azure"]
            payload:  ["1", "3"]
    """

    question_type = (question.get("questionType") or "").strip().lower()

    # ------------------------------------------------------------------
    # Text answers
    # ------------------------------------------------------------------

    if question_type in {
        "text box",
        "textbox",
        "text",
    }:
        return str(semantic_value)

    # ------------------------------------------------------------------
    # Single-select answers
    # ------------------------------------------------------------------

    if question_type in {
        "radio button",
        "radio",
        "single select",
        "single-select",
        "dropdown",
        "drop down",
    }:
        option_id = match_option(
            question=question,
            semantic_value=str(semantic_value),
        )

        if option_id is None:
            return None

        return [option_id]

    # ------------------------------------------------------------------
    # Multi-select answers
    # ------------------------------------------------------------------

    if question_type in {
        "checkbox",
        "check box",
        "multi select",
        "multi-select",
        "multiple select",
    }:
        if isinstance(semantic_value, list):
            values = semantic_value
        else:
            values = [semantic_value]

        selected = []

        for value in values:
            option_id = match_option(
                question=question,
                semantic_value=str(value),
            )

            if option_id is None:
                return None

            selected.append(option_id)

        return selected

    # ------------------------------------------------------------------
    # Unknown payload structure
    #
    # Do not guess.
    # ------------------------------------------------------------------

    return None


def match_option(
    question: dict,
    semantic_value: str,
) -> str | None:
    """
    Match a semantic answer to a questionnaire option ID.

    Matching order:

        1. Exact option-label match
        2. Yes/No match
        3. Notice-period bucket match
        4. Experience bucket match
    """

    options = question.get("answerOption") or {}

    if not options:
        return None

    value = str(semantic_value).strip()
    value_lower = value.lower()

    # ------------------------------------------------------------------
    # Exact label match
    # ------------------------------------------------------------------

    for option_id, label in options.items():
        if str(label).strip().lower() == value_lower:
            return str(option_id)

    # ------------------------------------------------------------------
    # Yes / No
    # ------------------------------------------------------------------

    if value_lower in {"yes", "no"}:
        for option_id, label in options.items():
            label_lower = str(label).strip().lower()

            if label_lower == value_lower:
                return str(option_id)

    # ------------------------------------------------------------------
    # Numeric semantic value
    # ------------------------------------------------------------------

    try:
        numeric_value = float(value)
    except (ValueError, TypeError):
        return None

    question_text = (question.get("questionName") or "").lower()

    # ------------------------------------------------------------------
    # Notice-period matching
    #
    # Only use notice matching for actual notice-period questions.
    # ------------------------------------------------------------------

    if "notice period" in question_text:
        notice_match = match_notice_period_option(
            options=options,
            days=numeric_value,
        )

        if notice_match is not None:
            return notice_match

        return None

    # ------------------------------------------------------------------
    # Experience bucket matching
    # ------------------------------------------------------------------

    if "experience" in question_text or "exp" in question_text:
        experience_match = match_experience_option(
            options=options,
            years=numeric_value,
        )

        if experience_match is not None:
            return experience_match

    return None


def match_notice_period_option(
    options: dict,
    days: float,
) -> str | None:
    """
    Match notice-period days to an available option.

    Example:

        days = 30

        options:
            1 -> Serving Notice Period
            2 -> 15 days or less
            3 -> 1 month
            4 -> 2 months
            5 -> 3 months
            6 -> More than 3 months

        result:
            "3"
    """

    for option_id, label in options.items():
        text = str(label).strip().lower()

        if "serving notice" in text:
            continue

        if "15 days" in text and days <= 15:
            return str(option_id)

        if "1 month" in text and 15 < days <= 30:
            return str(option_id)

        if "2 months" in text and 30 < days <= 60:
            return str(option_id)

        if "3 months" in text and "more than" not in text and days > 60 and days <= 90:
            return str(option_id)

        if "more than 3 months" in text and days > 90:
            return str(option_id)

    return None


def match_experience_option(
    options: dict,
    years: float,
) -> str | None:
    """
    Match numeric years of experience to an available experience bucket.

    Supported examples:

        No experience
        <4 years
        < 4 years
        4-6 years
        4 - 6 years
        >10 years
        > 10 years
    """

    for option_id, label in options.items():
        text = str(label).strip().lower()

        # --------------------------------------------------------------
        # No experience
        # --------------------------------------------------------------

        if "no experience" in text and years <= 0:
            return str(option_id)

        # --------------------------------------------------------------
        # Less-than bucket
        #
        # Example:
        #   <4 years
        # --------------------------------------------------------------

        match = re.search(
            r"<\s*(\d+(?:\.\d+)?)\s*years?",
            text,
        )

        if match:
            upper = float(match.group(1))

            if years < upper:
                return str(option_id)

        # --------------------------------------------------------------
        # Greater-than bucket
        #
        # Example:
        #   >10 years
        # --------------------------------------------------------------

        match = re.search(
            r">\s*(\d+(?:\.\d+)?)\s*years?",
            text,
        )

        if match:
            lower = float(match.group(1))

            if years > lower:
                return str(option_id)

        # --------------------------------------------------------------
        # Range bucket
        #
        # Example:
        #   4-6 years
        # --------------------------------------------------------------

        match = re.search(
            r"(\d+(?:\.\d+)?)" r"\s*-\s*" r"(\d+(?:\.\d+)?)" r"\s*years?",
            text,
        )

        if match:
            lower = float(match.group(1))
            upper = float(match.group(2))

            if lower <= years <= upper:
                return str(option_id)

    return None
