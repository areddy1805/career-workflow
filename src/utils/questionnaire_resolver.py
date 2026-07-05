import re
from datetime import date, datetime
from typing import Any

# ==============================================================================
# Public resolver
# ==============================================================================


def resolve_answer(
    question: dict,
    profile: dict,
) -> Any:
    text = (question.get("questionName") or "").strip()
    q = normalize(text)

    # ------------------------------------------------------------------
    # Compensation
    # ------------------------------------------------------------------

    if "expected" in q and ("ctc" in q or "salary" in q or "compensation" in q):
        if "inr" in q or "annual" in q:
            return profile.get("expected_ctc_inr")

        return profile.get("expected_ctc_lpa")

    if "current" in q and ("ctc" in q or "salary" in q or "compensation" in q):
        if "inr" in q or "annual" in q:
            return profile.get("current_ctc_inr")

        return profile.get("current_ctc_lpa")

    # ------------------------------------------------------------------
    # Notice period / joining
    # ------------------------------------------------------------------

    if "notice period" in q:
        return profile.get("notice_period_days")

    if "how soon can you join" in q or "when can you join" in q or "joining time" in q:
        return profile.get("notice_period_days")

    if "last working day" in q:
        return profile.get("last_working_day")

    # ------------------------------------------------------------------
    # Sensitive personal fields
    # ------------------------------------------------------------------

    if "pan number" in q or q == "pan":
        return profile.get("pan_number")

    if "date of birth" in q or "dob" in q:
        return profile.get("date_of_birth")

    if "whatsapp number" in q or "whatsapp mobile" in q:
        return profile.get("whatsapp_number")

    # ------------------------------------------------------------------
    # Overall experience
    # ------------------------------------------------------------------

    if (
        "total years of experience" in q
        or "total experience" in q
        or "overall experience" in q
        or "total years experience" in q
    ):
        return profile.get("total_experience_years")

    # ------------------------------------------------------------------
    # Specific technical experience
    # Order matters.
    # ------------------------------------------------------------------

    if contains_experience_question(q):

        if "mcp connector" in q:
            return profile.get("mcp_connector_experience_years")

        if re.search(r"\bmcp\b", q):
            return profile.get("mcp_experience_years")

        if "retrieval augmented generation" in q or re.search(r"\brag\b", q):
            return profile.get("rag_experience_years")

        if "agentic ai" in q or "aiagents" in q or "ai agents" in q or "ai agent" in q:
            return profile.get("agentic_ai_experience_years")

        if "large language model" in q or re.search(r"\bllm\b", q):
            return profile.get("llm_experience_years")

        if "generative ai" in q or "gen ai" in q or "genai" in q or "gen-ai" in q:
            return profile.get("genai_experience_years")

        if "vector database" in q:
            return profile.get("vector_db_experience_years")

        if "chatbot" in q:
            return profile.get("chatbot_experience_years")

        if "natural language processing" in q or re.search(r"\bnlp\b", q):
            return profile.get("nlp_experience_years")

        if "prompt engineering" in q:
            return profile.get("prompt_engineering_experience_years")

        if "ai evaluation" in q:
            return profile.get("ai_evaluation_experience_years")

        if "machine learning" in q or "deep learning" in q:
            return profile.get("machine_learning_experience_years")

        if (
            "artificial intelligence" in q
            or "ai automation" in q
            or "intelligent ai assistant" in q
            or "gen ai application" in q
            or "ai/ ml" in q
            or "ai/ml" in q
            or "aiml" in q
        ):
            return profile.get("ai_experience_years")

        if "python" in q:
            return profile.get("python_experience_years")

        if "typescript" in q:
            return profile.get("typescript_experience_years")

        if "angular" in q:
            return profile.get("angular_experience_years")

        if "node.js" in q or "nodejs" in q or re.search(r"\bnode\b", q):
            return profile.get("node_experience_years")

        if ".net" in q or "dotnet" in q:
            return profile.get("dotnet_experience_years")

        if "api development" in q:
            return profile.get("api_development_experience_years")

        if re.search(r"\bsql\b", q):
            return profile.get("sql_experience_years")

        if "data bricks" in q or "databricks" in q:
            return profile.get("databricks_experience_years")

        if "azure" in q:
            return profile.get("azure_experience_years")

        if re.search(r"\baws\b", q):
            return profile.get("aws_experience_years")

        if "cloud" in q:
            return profile.get("cloud_experience_years")

    # ------------------------------------------------------------------
    # Location / relocation
    # ------------------------------------------------------------------

    if (
        "currently residing in pune" in q
        or "currently living in pune" in q
        or ("relocate" in q and "pune" in q)
    ):
        return profile.get("willing_to_relocate_pune")

    if "south delhi" in q and ("relocate" in q or "staying" in q):
        willing = profile.get("willing_to_relocate_south_delhi")

        if normalize(str(willing)) == "yes":
            return "Willing to relocate in South Delhi"

        return None

    if q == "current location" or "your current location" in q:
        return profile.get("current_location")

    if q == "preferred location" or "preferred location" in q:
        return profile.get("preferred_location")

    if "select the city" in q and (
        "currently residing" in q or "willing to relocate" in q
    ):
        return choose_location_answer(
            question,
            profile,
        )

    if "willing to relocate" in q or "ready to relocate" in q:
        return "Yes"

    # ------------------------------------------------------------------
    # Employment history
    # ------------------------------------------------------------------

    if "ex-employee of infosys" in q or "ex employee of infosys" in q or "ex infy" in q:
        if (
            normalize(
                str(
                    profile.get(
                        "former_infosys_employee",
                        "No",
                    )
                )
            )
            == "no"
        ):
            return "NA"

        return None

    # ------------------------------------------------------------------
    # Offer status
    # ------------------------------------------------------------------

    if "offer in hand" in q or "offers in hand" in q or "holding any offers" in q:
        return profile.get("has_offer_in_hand")

    # ------------------------------------------------------------------
    # Contract / employment type
    # ------------------------------------------------------------------

    if "12 month fte" in q or "interested for 12 month fte" in q:
        return profile.get("accept_fte")

    if (
        "1 year contract" in q
        or "one year contract" in q
        or ("contract role" in q and "1 year" in q)
    ):
        return profile.get("accept_one_year_contract")

    # ------------------------------------------------------------------
    # Work arrangements
    # ------------------------------------------------------------------

    if "working remotely" in q or "comfortable working remotely" in q:
        return profile.get("accept_remote")

    if "alternate saturday" in q:
        return profile.get("willing_alternate_saturdays")

    # ------------------------------------------------------------------
    # Interview policy
    # ------------------------------------------------------------------

    if "hacker rank" in q or "hackerrank" in q:
        return profile.get("willing_hackerrank_test")

    if (
        "f2f interview" in q
        or "face to face interview" in q
        or "in person face to face interview" in q
    ):
        if interview_date_is_past(text):
            return None

        return profile.get("willing_f2f_interview")

    if "available for virtual interview" in q or "available for interview" in q:
        if interview_date_is_past(text):
            return None

        return "Yes"

    # ------------------------------------------------------------------
    # Domain experience
    # ------------------------------------------------------------------

    if "edtech domain" in q:
        return profile.get("edtech_experience")

    # ------------------------------------------------------------------
    # Descriptive recruiter questions
    # ------------------------------------------------------------------

    if "which llm frameworks" in q or "llm frameworks have you worked" in q:
        return profile.get("llm_frameworks")

    if "which vector databases" in q or "vector databases have you worked" in q:
        return profile.get("vector_databases")

    if "which cloud platform" in q and ("azure openai" in q or "aws bedrock" in q):
        return profile.get("preferred_cloud_platform")

    if "how have you used docker" in q or "docker in deploying ai" in q:
        return profile.get("docker_usage")

    if "worked on generative ai" in q and ("rag" in q or "llm" in q):
        return profile.get("genai_application_summary")

    if "hands-on experience with mlops" in q or "hands on experience with mlops" in q:
        return profile.get("mlops_summary")

    if "reason of job change" in q:
        return profile.get("reason_for_job_change")

    # Generic affirmative-policy fallback
    if any(
        phrase in q
        for phrase in (
            "willing to relocate",
            "ready to relocate",
            "available for interview",
            "available to attend",
            "comfortable working",
            "willing to work",
            "can attend",
            "can relocate",
        )
    ):
        if interview_date_is_past(text):
            return None

        return "Yes"

    # Generic experience fallback
    if contains_experience_question(q):
        return profile.get(
            "default_unmapped_experience_years",
            "2",
        )

    # ------------------------------------------------------------------
    # Generic capability / hands-on confirmation
    # ------------------------------------------------------------------

    capability_markers = (
        "have you deployed",
        "have you built",
        "have you worked",
        "have you used",
        "did you use",
        "do you have experience",
        "hands-on experience",
    )

    if any(marker in q for marker in capability_markers):
        return "Yes"

    return None


# ==============================================================================
# Serialization
# ==============================================================================


def serialize_answer(
    question: dict,
    semantic_value: Any,
) -> Any:
    question_type = normalize(question.get("questionType") or "")

    # ------------------------------------------------------------------
    # Text
    # ------------------------------------------------------------------

    if question_type in {
        "text box",
        "text",
        "textarea",
        "text area",
    }:
        return str(semantic_value)

    # ------------------------------------------------------------------
    # Single-select types
    # ------------------------------------------------------------------

    if question_type in {
        "radio button",
        "single select",
        "dropdown",
        "drop down",
        "list menu",
    }:
        option_id = match_option(
            question=question,
            semantic_value=str(semantic_value),
        )

        if option_id is None:
            return None

        return [option_id]

    # ------------------------------------------------------------------
    # Multi-select types
    # ------------------------------------------------------------------

    if question_type in {
        "checkbox",
        "check box",
        "multi select",
        "multiple select",
    }:
        values = (
            semantic_value if isinstance(semantic_value, list) else [semantic_value]
        )

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
    # Unknown type
    # ------------------------------------------------------------------

    return None


# ==============================================================================
# Option matching
# ==============================================================================


def is_numeric(
    value: str,
) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def match_option(
    question: dict,
    semantic_value: str,
) -> str | None:
    options = question.get("answerOption") or {}

    if not options:
        return None

    value = str(semantic_value).strip()
    value_lower = normalize(value)

    question_text = normalize(question.get("questionName") or "")

    # ------------------------------------------------------------------
    # Exact label match
    # ------------------------------------------------------------------

    for option_id, label in options.items():
        if normalize(str(label)) == value_lower:
            return str(option_id)

    # ------------------------------------------------------------------
    # Yes / No
    # ------------------------------------------------------------------

    if value_lower in {"yes", "no"}:
        for option_id, label in options.items():
            if normalize(str(label)) == value_lower:
                return str(option_id)

        return None

    # ------------------------------------------------------------------
    # Text/location option matching
    # ------------------------------------------------------------------

    if not is_numeric(value):
        location_match = match_location_option(
            options=options,
            semantic_value=value,
        )

        if location_match is not None:
            return location_match

        return None

    # ------------------------------------------------------------------
    # Numeric semantic value
    # ------------------------------------------------------------------

    numeric_value = float(value)

    # ------------------------------------------------------------------
    # Joining availability
    #
    # Must be handled before generic numeric matching.
    # ------------------------------------------------------------------

    if "how soon can you join" in question_text:
        return match_joining_window_option(
            options=options,
            days=numeric_value,
        )

    # ------------------------------------------------------------------
    # Notice period
    #
    # CRITICAL:
    # This branch terminates here even when no option matches.
    #
    # A 30-day notice period must NEVER fall through into another matcher.
    # ------------------------------------------------------------------

    if "notice period" in question_text:
        return match_notice_period_option(
            options=options,
            days=numeric_value,
        )

    # ------------------------------------------------------------------
    # Experience questions
    # ------------------------------------------------------------------

    if (
        "experience" in question_text
        or "years" in question_text
        or " exp " in f" {question_text} "
    ):
        return match_experience_option(
            options=options,
            years=numeric_value,
        )

    # ------------------------------------------------------------------
    # Unknown numeric select question
    #
    # Do not guess.
    # ------------------------------------------------------------------

    return None


# ==============================================================================
# Notice-period matching
# ==============================================================================


def match_notice_period_option(
    options: dict,
    days: float,
) -> str | None:
    """
    Match notice-period days only to a semantically correct option.

    Important:
    Never fall through to an incorrect larger bucket merely because the
    exact bucket is absent.
    """

    normalized = {
        str(option_id): str(label).strip().lower()
        for option_id, label in options.items()
    }

    # ------------------------------------------------------------------
    # 15 days or less
    # ------------------------------------------------------------------

    if days <= 15:
        for option_id, text in normalized.items():
            if "15 day" in text and ("less" in text or "or less" in text):
                return option_id

        return None

    # ------------------------------------------------------------------
    # 1 month / 30 days
    # ------------------------------------------------------------------

    if days <= 30:
        for option_id, text in normalized.items():
            if "1 month" in text or "30 day" in text:
                return option_id

        return None

    # ------------------------------------------------------------------
    # 2 months / 60 days
    # ------------------------------------------------------------------

    if days <= 60:
        for option_id, text in normalized.items():
            if "2 month" in text or "60 day" in text:
                return option_id

        return None

    # ------------------------------------------------------------------
    # 3 months / 90 days
    # ------------------------------------------------------------------

    if days <= 90:
        for option_id, text in normalized.items():
            if "3 month" in text or "90 day" in text:
                return option_id

        return None

    # ------------------------------------------------------------------
    # More than 3 months
    # ------------------------------------------------------------------

    for option_id, text in normalized.items():
        if "more than 3 month" in text or "above 3 month" in text or ">3 month" in text:
            return option_id

    return None


# ==============================================================================
# Experience matching
# ==============================================================================


def match_experience_option(
    options: dict,
    years: float,
) -> str | None:
    for option_id, label in options.items():
        text = normalize(str(label))

        if "no experience" in text and years <= 0:
            return str(option_id)

        # Less than 2
        match = re.search(
            r"less than\s*(\d+(?:\.\d+)?)",
            text,
        )

        if match:
            upper = float(match.group(1))

            if years < upper:
                return str(option_id)

        # <4 years
        match = re.search(
            r"<\s*(\d+(?:\.\d+)?)\s*years?",
            text,
        )

        if match:
            upper = float(match.group(1))

            if years < upper:
                return str(option_id)

        # More than 4
        match = re.search(
            r"more than\s*(\d+(?:\.\d+)?)",
            text,
        )

        if match:
            lower = float(match.group(1))

            if years > lower:
                return str(option_id)

        # >10 years
        match = re.search(
            r">\s*(\d+(?:\.\d+)?)\s*years?",
            text,
        )

        if match:
            lower = float(match.group(1))

            if years > lower:
                return str(option_id)

        # 4-6 years
        # 2 - 4 years
        match = re.search(
            r"(\d+(?:\.\d+)?)" r"\s*-\s*" r"(\d+(?:\.\d+)?)" r"(?:\s*years?)?",
            text,
        )

        if match:
            lower = float(match.group(1))
            upper = float(match.group(2))

            if lower <= years <= upper:
                return str(option_id)

        # Exact numeric label.
        match = re.fullmatch(
            r"(\d+(?:\.\d+)?)\s*(?:years?)?",
            text,
        )

        if match:
            exact = float(match.group(1))

            if years == exact:
                return str(option_id)

    return None


# ==============================================================================
# Location selection
# ==============================================================================


def choose_location_answer(
    question: dict,
    profile: dict,
) -> str | list[str] | None:
    options = question.get("answerOption") or {}

    if not options:
        return None

    preferred = [
        normalize(location)
        for location in profile.get(
            "relocation_preferences",
            [],
        )
    ]

    current = normalize(profile.get("current_location") or "")

    ranked_locations = []

    if current:
        ranked_locations.append(current)

    for location in preferred:
        if location not in ranked_locations:
            ranked_locations.append(location)

    for wanted_location in ranked_locations:
        for _, label in options.items():
            label_normalized = normalize(str(label))

            if (
                wanted_location == label_normalized
                or wanted_location in label_normalized
                or label_normalized in wanted_location
            ):
                return str(label)

    return None


# ==============================================================================
# Date-aware interview handling
# ==============================================================================


MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def extract_date_from_text(
    text: str,
) -> date | None:
    normalized = normalize(text)

    pattern = re.compile(
        r"\b"
        r"(\d{1,2})"
        r"(?:st|nd|rd|th)?"
        r"\s+"
        r"(" + "|".join(MONTHS.keys()) + r")"
        r"(?:\s+(\d{4}))?"
        r"\b"
    )

    match = pattern.search(normalized)

    if not match:
        return None

    day = int(match.group(1))
    month = MONTHS[match.group(2)]

    if match.group(3):
        year = int(match.group(3))
    else:
        year = datetime.now().year

    try:
        return date(
            year,
            month,
            day,
        )
    except ValueError:
        return None


def interview_date_is_past(
    text: str,
) -> bool:
    extracted = extract_date_from_text(text)

    if extracted is None:
        return False

    return extracted < date.today()


# ==============================================================================
# Helpers
# ==============================================================================


def contains_experience_question(
    q: str,
) -> bool:
    return (
        "experience" in q
        or "years" in q
        or "relevant exp" in q
        or "hands-on" in q
        or "hands on" in q
    )


def normalize(
    value: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(value).strip().lower(),
    )


def match_location_option(
    options: dict,
    semantic_value: str,
) -> str | None:
    wanted = normalize(semantic_value)

    if not wanted:
        return None

    for option_id, label in options.items():
        candidate = normalize(str(label))

        if wanted == candidate or wanted in candidate or candidate in wanted:
            return str(option_id)

    return None


def match_joining_window_option(
    options: dict,
    days: float,
) -> str | None:
    """
    Match joining availability against recruiter-defined day ranges.

    Boundary policy:
    Prefer the narrowest matching interval.
    Example:
        30 days -> "Within 15 - 30 Days"
        rather than "Within 30 - 60 Days"
    """

    candidates = []

    for option_id, label in options.items():
        text = normalize(str(label))

        # Within 15 Days
        match = re.search(
            r"within\s+(\d+)\s*days?",
            text,
        )

        if match and "-" not in text:
            upper = float(match.group(1))

            if days <= upper:
                candidates.append(
                    (
                        upper,
                        str(option_id),
                    )
                )

            continue

        # Within 15 - 30 Days
        match = re.search(
            r"within\s+" r"(\d+(?:\.\d+)?)" r"\s*-\s*" r"(\d+(?:\.\d+)?)" r"\s*days?",
            text,
        )

        if match:
            lower = float(match.group(1))
            upper = float(match.group(2))

            if lower <= days <= upper:
                candidates.append(
                    (
                        upper - lower,
                        str(option_id),
                    )
                )

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0])

    return candidates[0][1]
