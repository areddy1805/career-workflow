import csv
import json
import os
import random
import time

from datetime import UTC, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

from config.candidate_profile import (
    CANDIDATE_PROFILE,
)

from src.application.response_classifier import (
    ApplyStatus,
    classify_apply_response,
)

from src.application.response_store import (
    save_response,
)

from src.client.job_client import (
    NaukriJobClient,
)

from src.client.naukri_client import (
    NaukriLoginClient,
)

from src.models.models import Job

from src.resolution.hybrid_resolver import (
    HybridQuestionResolver,
)

from src.utils.questionnaire_telemetry import (
    log_unresolved_questions,
)

# ==============================================================================
# Configuration
# ==============================================================================


MAX_APPLICATIONS = 5

SCAN_LIMIT = 20

SLEEP_BETWEEN_JOBS_MIN = 4
SLEEP_BETWEEN_JOBS_MAX = 8


SCORED_JOBS_FILE = Path("data/scored_jobs.csv")

APPLICATION_LOG_FILE = Path("data/application_log.csv")


# Increment whenever resolver behavior materially changes.
# MANUAL_REVIEW and VALIDATION_ERROR entries from an older resolver version
# become immediately eligible for retry.
RESOLVER_VERSION = 5


PRIORITY_ORDER = {
    "P1": 1,
    "P2": 2,
    "P3": 3,
}


LOCATION_ORDER = {
    "PUNE": 1,
    "REMOTE": 2,
    "INDIA": 3,
    "OTHER": 4,
}


PERMANENT_TERMINAL_STATUSES = {
    "APPLIED",
    "ALREADY_APPLIED",
    "EXTERNAL",
    "BLOCKED",
}


RETRY_COOLDOWN_HOURS = {
    "MANUAL_REVIEW": 24,
    "VALIDATION_ERROR": 24,
    "RETRYABLE": 6,
    "UNKNOWN_FAILURE": 72,
    "FAILED": 6,
}


HYBRID_QUESTION_RESOLVER = HybridQuestionResolver()


# ==============================================================================
# Application log
# ==============================================================================


LOG_FIELDS = [
    "job_id",
    "title",
    "company",
    "priority",
    "subtrack",
    "location",
    "status",
    "reason",
    "resolver_version",
    "applied_at",
]


def ensure_log_file():
    APPLICATION_LOG_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not APPLICATION_LOG_FILE.exists():
        with APPLICATION_LOG_FILE.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=LOG_FIELDS,
            )

            writer.writeheader()

        return

    migrate_log_schema_if_needed()


def migrate_log_schema_if_needed():
    with APPLICATION_LOG_FILE.open(
        encoding="utf-8",
        newline="",
    ) as f:
        reader = csv.DictReader(f)

        existing_fields = reader.fieldnames or []

        rows = list(reader)

    if existing_fields == LOG_FIELDS:
        return

    migrated_rows = []

    for row in rows:
        migrated = {field: row.get(field, "") for field in LOG_FIELDS}

        if not migrated["resolver_version"]:
            migrated["resolver_version"] = "1"

        migrated_rows.append(migrated)

    backup_path = APPLICATION_LOG_FILE.with_suffix(".pre_schema_migration.csv")

    if not backup_path.exists():
        APPLICATION_LOG_FILE.replace(backup_path)

    with APPLICATION_LOG_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=LOG_FIELDS,
        )

        writer.writeheader()
        writer.writerows(migrated_rows)


def load_application_log() -> list[dict]:
    ensure_log_file()

    with APPLICATION_LOG_FILE.open(
        encoding="utf-8",
        newline="",
    ) as f:
        return list(csv.DictReader(f))


def append_log(
    row: dict,
    status: str,
    reason: str = "",
):
    ensure_log_file()

    record = {
        "job_id": row["job_id"],
        "title": row["title"],
        "company": row["company"],
        "priority": row["priority"],
        "subtrack": row["subtrack"],
        "location": row["location"],
        "status": status,
        "reason": reason,
        "resolver_version": str(RESOLVER_VERSION),
        "applied_at": datetime.now(UTC).isoformat(),
    }

    with APPLICATION_LOG_FILE.open(
        "a",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=LOG_FIELDS,
        )

        writer.writerow(record)


# ==============================================================================
# Retry state
# ==============================================================================


def parse_timestamp(
    value: str,
) -> datetime | None:
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(value)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)

        return parsed

    except ValueError:
        return None


def latest_log_by_job() -> dict[str, dict]:
    rows = load_application_log()

    latest = {}

    for row in rows:
        job_id = row.get("job_id")

        if not job_id:
            continue

        timestamp = parse_timestamp(row.get("applied_at", ""))

        existing = latest.get(job_id)

        if existing is None:
            latest[job_id] = row
            continue

        existing_timestamp = parse_timestamp(
            existing.get(
                "applied_at",
                "",
            )
        )

        if timestamp is not None and (
            existing_timestamp is None or timestamp > existing_timestamp
        ):
            latest[job_id] = row

    return latest


def should_retry_job(
    latest_record: dict | None,
) -> bool:
    if latest_record is None:
        return True

    status = latest_record.get(
        "status",
        "",
    )

    if status in PERMANENT_TERMINAL_STATUSES:
        return False

    # Resolver improvements should immediately retry resolver-dependent states.
    if status in {
        "MANUAL_REVIEW",
        "VALIDATION_ERROR",
    }:
        try:
            previous_version = int(latest_record.get("resolver_version") or 1)
        except ValueError:
            previous_version = 1

        if previous_version < RESOLVER_VERSION:
            return True

    cooldown_hours = RETRY_COOLDOWN_HOURS.get(status)

    if cooldown_hours is None:
        return True

    timestamp = parse_timestamp(
        latest_record.get(
            "applied_at",
            "",
        )
    )

    if timestamp is None:
        return True

    retry_at = timestamp + timedelta(hours=cooldown_hours)

    return datetime.now(UTC) >= retry_at


def get_pending_jobs(
    jobs: list[dict],
) -> list[dict]:
    latest = latest_log_by_job()

    return [row for row in jobs if should_retry_job(latest.get(row["job_id"]))]


def count_permanent_terminal_jobs() -> int:
    latest = latest_log_by_job()

    return sum(
        1 for row in latest.values() if row.get("status") in PERMANENT_TERMINAL_STATUSES
    )


# ==============================================================================
# Job loading
# ==============================================================================


def load_eligible_jobs() -> list[dict]:
    if not SCORED_JOBS_FILE.exists():
        raise RuntimeError(f"Missing file: {SCORED_JOBS_FILE}")

    with SCORED_JOBS_FILE.open(
        encoding="utf-8",
        newline="",
    ) as f:
        rows = list(csv.DictReader(f))

    eligible = [row for row in rows if row.get("eligible") == "YES"]

    eligible.sort(
        key=lambda row: (
            PRIORITY_ORDER.get(
                row.get("priority"),
                99,
            ),
            LOCATION_ORDER.get(
                row.get("location_group"),
                99,
            ),
            -int(row.get("score") or 0),
        )
    )

    return eligible


def row_to_job(
    row: dict,
) -> Job:
    tags = [tag.strip() for tag in (row.get("tags") or "").split(",") if tag.strip()]

    return Job(
        job_id=row["job_id"],
        title=row["title"],
        company=row["company"],
        location=row["location"],
        experience=row.get(
            "experience",
            "",
        ),
        salary=row.get(
            "salary",
            "",
        ),
        posted_date=row.get(
            "posted_date",
            "",
        ),
        apply_link=row.get(
            "apply_link",
            "",
        ),
        description=row.get(
            "description",
            "",
        ),
        tags=tags,
    )


# ==============================================================================
# Questionnaire handling
# ==============================================================================


def resolve_questionnaire(
    questionnaire: list[dict],
) -> tuple[dict, list[dict]]:
    answers = {}
    unresolved = []

    for question in questionnaire:
        question_id = question.get("questionId")

        if not question_id:
            unresolved.append(question)
            continue

        resolution = HYBRID_QUESTION_RESOLVER.resolve(
            question=question,
            profile=CANDIDATE_PROFILE,
        )

        if not resolution.resolved:
            unresolved_question = dict(question)
            unresolved_question["_resolution_source"] = resolution.source
            unresolved_question["_resolution_confidence"] = resolution.confidence
            unresolved_question["_resolution_reasoning"] = resolution.reasoning
            unresolved.append(unresolved_question)
            continue

        answers[str(question_id)] = resolution.serialized_answer

    return answers, unresolved


def format_unresolved_questions(
    questions: list[dict],
) -> str:
    parts = []

    for question in questions:
        name = question.get("questionName") or "Unknown question"

        question_type = question.get("questionType") or "Unknown type"

        parts.append(f"{name} [{question_type}]")

    return " | ".join(parts)


# ==============================================================================
# Response helpers
# ==============================================================================


def extract_job_result(
    response: dict,
) -> dict:
    jobs = response.get("jobs") or []

    if not jobs:
        return {}

    return jobs[0]


def response_is_success(
    response: dict,
    job_id: str,
) -> bool:
    apply_status = response.get("applyStatus") or {}

    status = apply_status.get(str(job_id))

    if status == 200:
        return True

    for item in response.get("jobs") or []:
        if str(item.get("jobId")) == str(job_id) and item.get("status") == 200:
            return True

    return False


def response_is_already_applied(
    response: dict,
) -> bool:
    text = json.dumps(
        response,
        ensure_ascii=False,
    ).lower()

    return "already applied" in text or "already apply" in text


def save_classified_response(
    job_id: str,
    stage: str,
    response: dict,
    status: str,
) -> str:
    return save_response(
        job_id=job_id,
        stage=f"{stage}_{status.lower()}",
        response=response,
    )


# ==============================================================================
# Interactive chatbot / Recruiter QUP handling
# ==============================================================================


MAX_CHATBOT_STEPS = 20
MAX_CONSECUTIVE_UNKNOWN_FAILURES = 3


def extract_chatbot_response(response: dict) -> dict:
    """
    Normalize both chatbot response shapes:
    nested chatbotResponse from initial apply and direct chatbot state
    returned by the respond endpoint.
    """
    if not isinstance(response, dict):
        return {}

    chatbot = response.get("chatbotResponse")

    if isinstance(chatbot, dict) and chatbot:
        return chatbot

    chatbot_markers = (
        "currentConversationName",
        "currentNodeName",
        "conversation_session_id",
        "speechResponse",
        "options",
        "isApply",
    )

    if any(marker in response for marker in chatbot_markers):
        return response

    return {}


def chatbot_prompt_text(chatbot: dict) -> str:
    parts = []

    for item in chatbot.get("speechResponse") or []:
        if isinstance(item, dict):
            value = item.get("response")
            if value:
                parts.append(str(value))
        elif item:
            parts.append(str(item))

    if parts:
        return " ".join(parts).strip()

    return str(
        chatbot.get("currentNodeName") or chatbot.get("currentConversationName") or ""
    ).strip()


def chatbot_options(chatbot: dict) -> list[dict]:
    return [
        option for option in (chatbot.get("options") or []) if isinstance(option, dict)
    ]


def is_upload_option(option: dict) -> bool:
    return str(option.get("type") or "").strip().lower() == "upload"


def find_skip_upload_option(options: list[dict]) -> dict | None:
    markers = ("later", "skip", "not now", "do it later")

    for option in options:
        text = " ".join(
            str(option.get(field) or "") for field in ("name", "value")
        ).lower()

        if any(marker in text for marker in markers):
            return option

    return None


def option_answer_id(option: dict) -> str:
    for field in ("id", "optionId", "answerId", "key"):
        value = option.get(field)
        if value is not None and str(value):
            return str(value)

    return "-1"


def option_answer_text(option: dict) -> str:
    return str(option.get("value") or option.get("name") or "").strip()


def build_chatbot_question(chatbot: dict) -> dict:
    options = chatbot_options(chatbot)
    answer_options = {}

    for index, option in enumerate(options):
        key = option_answer_id(option)
        if key == "-1":
            key = str(index)
        answer_options[key] = option_answer_text(option)

    input_data = chatbot.get("input") or {}
    input_type = str(input_data.get("type") or "").lower()

    return {
        "questionId": str(
            chatbot.get("currentNode")
            or chatbot.get("currentNodeName")
            or chatbot.get("currentConversationName")
            or "chatbot_question"
        ),
        "questionName": chatbot_prompt_text(chatbot),
        "questionType": "radio" if answer_options else (input_type or "text box"),
        "answerOption": answer_options,
    }


def resolve_chatbot_answer(chatbot: dict) -> tuple[str, str] | None:
    options = chatbot_options(chatbot)

    if options and any(is_upload_option(option) for option in options):
        skip_option = find_skip_upload_option(options)
        if skip_option is None:
            return None

        return (
            option_answer_text(skip_option),
            option_answer_id(skip_option),
        )

    question = build_chatbot_question(chatbot)

    resolution = HYBRID_QUESTION_RESOLVER.resolve(
        question=question,
        profile=CANDIDATE_PROFILE,
    )

    if not resolution.resolved:
        return None

    semantic_answer = resolution.semantic_answer

    if not options:
        return str(semantic_answer), "-1"

    target = str(semantic_answer).strip().lower()

    for option in options:
        option_text = option_answer_text(option)

        if option_text.lower() == target:
            return option_text, option_answer_id(option)

    serialized = resolution.serialized_answer

    if serialized is None:
        return None

    if isinstance(serialized, list):
        serialized_value = serialized[0] if serialized else None
    else:
        serialized_value = serialized

    if serialized_value is None:
        return None

    serialized_text = str(serialized_value)

    for index, option in enumerate(options):
        option_id = option_answer_id(option)
        effective_id = option_id if option_id != "-1" else str(index)

        if serialized_text == effective_id:
            return option_answer_text(option), option_id

    return str(semantic_answer), "-1"


def run_interactive_chatbot_flow(
    jc: NaukriJobClient,
    job: Job,
    row: dict,
    initial_response: dict,
) -> tuple[str, str]:
    response = initial_response

    for step in range(1, MAX_CHATBOT_STEPS + 1):
        chatbot = extract_chatbot_response(response)

        if not chatbot:
            path = save_classified_response(
                job_id=job.job_id,
                stage=f"chatbot_step_{step}",
                response=response,
                status="UNKNOWN_FAILURE",
            )
            return (
                "UNKNOWN_FAILURE",
                f"chatbot response missing at step {step}; response={path}",
            )

        conversation_name = str(chatbot.get("currentConversationName") or "").strip()

        node_name = str(chatbot.get("currentNodeName") or "").strip()

        data_committed = chatbot.get("dataCommitted") is True
        is_leaf = chatbot.get("isLeafNode") is True

        print(
            f"[CHATBOT] Step {step}: "
            f"{conversation_name or 'unknown conversation'} / "
            f"{node_name or 'unknown node'}"
        )

        options = chatbot_options(chatbot)

        is_resume_upload_node = (
            conversation_name == "RecruiterQUP_keySkillsResumeUpload"
            or node_name.lower() == "resume upload"
            or any(is_upload_option(option) for option in options)
        )

        if data_committed and is_leaf and not is_resume_upload_node:
            return (
                "APPLIED",
                "interactive questionnaire committed at terminal node",
            )

        answer = resolve_chatbot_answer(chatbot)

        if answer is None:
            path = save_classified_response(
                job_id=job.job_id,
                stage=f"chatbot_unresolved_step_{step}",
                response=response,
                status="MANUAL_REVIEW",
            )

            prompt = chatbot_prompt_text(chatbot) or node_name or conversation_name

            return (
                "MANUAL_REVIEW",
                f"unresolved chatbot question: {prompt}; response={path}",
            )

        answer_text, answer_id = answer
        print(f"[CHATBOT] Answer: {answer_text}")

        try:
            response = jc.respond_to_chatbot(
                answer_text=answer_text,
                answer_id=answer_id,
                conversation_name=conversation_name,
                status="Fresh",
            )
        except Exception as exc:
            return (
                "FAILED",
                f"chatbot step {step} failed: {exc}",
            )

        if response_is_already_applied(response):
            return (
                "ALREADY_APPLIED",
                "platform reports existing application during chatbot flow",
            )

        next_chatbot = extract_chatbot_response(response)

        if next_chatbot:
            next_options = chatbot_options(next_chatbot)
            next_conversation = str(
                next_chatbot.get("currentConversationName") or ""
            ).strip()
            next_node = str(next_chatbot.get("currentNodeName") or "").strip()

            next_is_resume_upload = (
                next_conversation == "RecruiterQUP_keySkillsResumeUpload"
                or next_node.lower() == "resume upload"
                or any(is_upload_option(option) for option in next_options)
            )

            if (
                next_chatbot.get("dataCommitted") is True
                and next_chatbot.get("isLeafNode") is True
                and not next_is_resume_upload
            ):
                return (
                    "APPLIED",
                    "interactive questionnaire committed at terminal node",
                )
        else:
            classification = classify_apply_response(response)
            if classification.status == ApplyStatus.APPLIED:
                return ("APPLIED", classification.reason)
            if classification.status == ApplyStatus.ALREADY_APPLIED:
                return ("ALREADY_APPLIED", classification.reason)
            path = save_classified_response(
                job_id=job.job_id,
                stage=f"chatbot_step_{step + 1}",
                response=response,
                status=classification.status.value,
            )
            return (
                classification.status.value,
                f"{classification.reason}; response={path}",
            )

    path = save_classified_response(
        job_id=job.job_id,
        stage="chatbot_max_steps",
        response=response,
        status="UNKNOWN_FAILURE",
    )

    return (
        "UNKNOWN_FAILURE",
        f"chatbot exceeded {MAX_CHATBOT_STEPS} steps; response={path}",
    )


# ==============================================================================
# Single-job workflow
# ==============================================================================


def process_job(
    jc: NaukriJobClient,
    row: dict,
) -> str:
    job = row_to_job(row)

    print("\n" + "=" * 110)

    print(f'{row["priority"]} | ' f'{row["subtrack"]} | ' f'{row["location_group"]}')

    print(f"Job:      {job.title}")

    print(f"Company:  {job.company}")

    print(f"Location: {job.location}")

    print(f"Job ID:   {job.job_id}")

    sid = datetime.now(UTC).strftime("%Y%m%d%H%M%S") + "0000000"

    # ------------------------------------------------------------------
    # 1. External apply check
    # ------------------------------------------------------------------

    print("[CHECK] Fetching job details...")

    try:
        external = jc.is_external_apply(
            job.job_id,
            sid,
        )

    except Exception as exc:
        reason = f"job detail check failed: " f"{exc}"

        append_log(
            row,
            "FAILED",
            reason,
        )

        print(f"[FAILED] {reason}")

        return "FAILED"

    if external:
        append_log(
            row,
            "EXTERNAL",
            "external company application",
        )

        print("[EXTERNAL] Skipped")

        return "EXTERNAL"

    # ------------------------------------------------------------------
    # 2. Initial apply
    # ------------------------------------------------------------------

    print("[APPLY] Starting application workflow...")

    try:
        initial = jc.apply_job(
            job,
            mandatory_skills=[],
            optional_skills=[],
            sid=sid,
            source="search",
        )

    except Exception as exc:
        reason = f"initial apply failed: " f"{exc}"

        append_log(
            row,
            "FAILED",
            reason,
        )

        print(f"[FAILED] {reason}")

        return "FAILED"

    # ------------------------------------------------------------------
    # 3. Already applied
    # ------------------------------------------------------------------

    if response_is_already_applied(initial):
        append_log(
            row,
            "ALREADY_APPLIED",
            "platform reports existing application",
        )

        print("[ALREADY_APPLIED]")

        return "ALREADY_APPLIED"

    # ------------------------------------------------------------------
    # 4. Immediate success
    # ------------------------------------------------------------------

    if response_is_success(
        initial,
        job.job_id,
    ):
        append_log(
            row,
            "APPLIED",
            "application completed without questionnaire",
        )

        print("[APPLIED] No questionnaire required")

        return "APPLIED"

    # ------------------------------------------------------------------
    # 5. Standard questionnaire takes precedence over chatbot/QUP
    # ------------------------------------------------------------------

    job_result = extract_job_result(initial)
    questionnaire = job_result.get("questionnaire") or []

    if questionnaire:
        print(f"[QUESTIONNAIRE] {len(questionnaire)} question(s)")
    else:
        initial_chatbot = extract_chatbot_response(initial)

        if initial_chatbot:
            print("[INTERACTIVE_REQUIRED] Entering chatbot/QUP flow")
            status, reason = run_interactive_chatbot_flow(
                jc=jc,
                job=job,
                row=row,
                initial_response=initial,
            )
            append_log(row, status, reason)
            print(f"[{status}] {reason}")
            return status

        initial_classification = classify_apply_response(initial)

        if initial_classification.status == ApplyStatus.INTERACTIVE_REQUIRED:
            print("[INTERACTIVE_REQUIRED] Entering chatbot/QUP flow")
            status, reason = run_interactive_chatbot_flow(
                jc=jc,
                job=job,
                row=row,
                initial_response=initial,
            )
            append_log(row, status, reason)
            print(f"[{status}] {reason}")
            return status

        response_path = save_classified_response(
            job_id=job.job_id,
            stage="initial_apply",
            response=initial,
            status=initial_classification.status.value,
        )
        reason = f"{initial_classification.reason}; response={response_path}"
        append_log(row, initial_classification.status.value, reason)
        print(
            f"[{initial_classification.status.value}] {initial_classification.reason}"
        )
        print(f"[RESPONSE SAVED] {response_path}")
        return initial_classification.status.value

    # ------------------------------------------------------------------
    # 6. Resolve questionnaire
    # ------------------------------------------------------------------

    answers, unresolved = resolve_questionnaire(questionnaire)

    if unresolved:
        reason = format_unresolved_questions(unresolved)

        log_unresolved_questions(
            row=row,
            questions=unresolved,
        )

        append_log(
            row,
            "MANUAL_REVIEW",
            reason,
        )

        print("[MANUAL_REVIEW]")

        for question in unresolved:
            name = question.get("questionName") or "Unknown question"

            question_type = question.get("questionType") or "Unknown type"

            print(f"  - {name} " f"[{question_type}]")

        return "MANUAL_REVIEW"

    print("[QUESTIONNAIRE] " "All answers resolved")

    for question in questionnaire:
        question_id = str(question["questionId"])

        print(f'{question.get("questionName")} ' f"-> {answers[question_id]}")

    # ------------------------------------------------------------------
    # 7. Submit questionnaire
    # ------------------------------------------------------------------

    try:
        final = jc.submit_questionnaire_answers(
            job=job,
            answers=answers,
            sid=sid,
            source="search",
        )

    except Exception as exc:
        reason = "questionnaire submit failed: " f"{exc}"

        append_log(
            row,
            "FAILED",
            reason,
        )

        print(f"[FAILED] {reason}")

        return "FAILED"

    # ------------------------------------------------------------------
    # 8. Final success
    # ------------------------------------------------------------------

    if response_is_success(
        final,
        job.job_id,
    ):
        append_log(
            row,
            "APPLIED",
            "questionnaire resolved and submitted",
        )

        print("[APPLIED] Questionnaire submitted successfully")

        return "APPLIED"

    # ------------------------------------------------------------------
    # 9. Final already applied
    # ------------------------------------------------------------------

    if response_is_already_applied(final):
        append_log(
            row,
            "ALREADY_APPLIED",
            "platform reports existing application",
        )

        print("[ALREADY_APPLIED]")

        return "ALREADY_APPLIED"

    # ------------------------------------------------------------------
    # 10. Classify unexpected final response
    # ------------------------------------------------------------------

    classification = classify_apply_response(final)

    if classification.status == ApplyStatus.INTERACTIVE_REQUIRED:
        print("[INTERACTIVE_REQUIRED] Continuing with chatbot/QUP flow")
        status, reason = run_interactive_chatbot_flow(
            jc=jc,
            job=job,
            row=row,
            initial_response=final,
        )
        append_log(row, status, reason)
        print(f"[{status}] {reason}")
        return status

    response_path = save_classified_response(
        job_id=job.job_id,
        stage="questionnaire_submit",
        response=final,
        status=classification.status.value,
    )

    reason = f"{classification.reason}; " f"response={response_path}"

    append_log(
        row,
        classification.status.value,
        reason,
    )

    print(f"[{classification.status.value}] " f"{classification.reason}")

    print(f"[RESPONSE SAVED] " f"{response_path}")

    return classification.status.value


# ==============================================================================
# Main
# ==============================================================================


def main():
    load_dotenv(".env", override=True)

    username = os.getenv("NAUKRI_USERNAME")

    password = os.getenv("NAUKRI_PASSWORD")

    if not username or not password:
        raise RuntimeError("USERNAME or PASSWORD missing from .env")

    ensure_log_file()

    jobs = load_eligible_jobs()

    pending_jobs = get_pending_jobs(jobs)

    permanent_terminal_count = count_permanent_terminal_jobs()

    print("=" * 110)

    print("AI JOB APPLICATION RUNNER")

    print("=" * 110)

    print(f"Eligible jobs:       " f"{len(jobs)}")

    print(f"Permanent terminal:  " f"{permanent_terminal_count}")

    print(f"Pending candidates:  " f"{len(pending_jobs)}")

    print(f"Success batch limit: " f"{MAX_APPLICATIONS}")

    print(
        "Scan limit:          "
        f"{SCAN_LIMIT if SCAN_LIMIT is not None else 'unlimited'}"
    )

    print(f"Resolver version:    " f"{RESOLVER_VERSION}")

    print("\n[1] Logging in...")

    client = NaukriLoginClient(
        username,
        password,
    )

    client.login()

    print("[OK] Login successful")

    jc = NaukriJobClient(client)

    successful_applications = 0
    scanned_jobs = 0
    consecutive_unknown_failures = 0

    counters = {status.value: 0 for status in ApplyStatus}

    counters["MANUAL_REVIEW"] = 0
    counters["EXTERNAL"] = 0

    for row in pending_jobs:
        if successful_applications >= MAX_APPLICATIONS:
            print("\n[LIMIT] Successful application " "batch limit reached")

            break

        if SCAN_LIMIT is not None and scanned_jobs >= SCAN_LIMIT:
            print(f"\n[SCAN LIMIT] " f"Inspected {scanned_jobs} " f"candidate jobs")

            break

        status = process_job(
            jc,
            row,
        )

        counters.setdefault(
            status,
            0,
        )

        counters[status] += 1

        # External redirects do not consume the useful candidate scan budget.
        if status != "EXTERNAL":
            scanned_jobs += 1

        if status == "APPLIED":
            successful_applications += 1

        if status == "UNKNOWN_FAILURE":
            consecutive_unknown_failures += 1
        else:
            consecutive_unknown_failures = 0

        if consecutive_unknown_failures >= MAX_CONSECUTIVE_UNKNOWN_FAILURES:
            print(
                "\n[CIRCUIT BREAKER] "
                f"{consecutive_unknown_failures} consecutive UNKNOWN_FAILURE results. Aborting run."
            )
            break

        print(
            "\nProgress: "
            f"{successful_applications}/"
            f"{MAX_APPLICATIONS} "
            "successful applications"
        )

        time.sleep(random.uniform(SLEEP_BETWEEN_JOBS_MIN, SLEEP_BETWEEN_JOBS_MAX))

    print("\n" + "=" * 110)

    print("RUN SUMMARY")

    print("=" * 110)

    for status, count in counters.items():
        if count > 0:
            print(f"{status:<20} " f"{count}")

    print(f"\nCandidate jobs scanned: " f"{scanned_jobs}")

    print("Successful applications this run: " f"{successful_applications}")


if __name__ == "__main__":
    main()
