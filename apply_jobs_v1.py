import csv
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from config.candidate_profile import CANDIDATE_PROFILE
from src.client.job_client import NaukriJobClient
from src.client.naukri_client import NaukriLoginClient
from src.models.models import Job
from src.utils.questionnaire_resolver import resolve_answer

# ==============================================================================
# Configuration
# ==============================================================================

SCORED_JOBS_FILE = Path("data/scored_jobs.csv")
APPLICATION_LOG_FILE = Path("data/application_log.csv")

MAX_APPLICATIONS = 5

SLEEP_BETWEEN_JOBS = 5

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

TERMINAL_STATUSES = {
    "APPLIED",
    "ALREADY_APPLIED",
    "MANUAL_REVIEW",
    "EXTERNAL",
}


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
    "applied_at",
]


def ensure_log_file():
    APPLICATION_LOG_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if APPLICATION_LOG_FILE.exists():
        return

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
    record = {
        "job_id": row["job_id"],
        "title": row["title"],
        "company": row["company"],
        "priority": row["priority"],
        "subtrack": row["subtrack"],
        "location": row["location"],
        "status": status,
        "reason": reason,
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


def load_terminal_job_ids() -> set[str]:
    rows = load_application_log()

    return {row["job_id"] for row in rows if row["status"] in TERMINAL_STATUSES}


# ==============================================================================
# Job loading and ordering
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


def row_to_job(row: dict) -> Job:
    tags = [tag.strip() for tag in (row.get("tags") or "").split(",") if tag.strip()]

    return Job(
        job_id=row["job_id"],
        title=row["title"],
        company=row["company"],
        location=row["location"],
        experience=row.get("experience", ""),
        salary=row.get("salary", ""),
        posted_date=row.get("posted_date", ""),
        apply_link=row.get("apply_link", ""),
        description=row.get("description", ""),
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
        question_id = question["questionId"]

        answer = resolve_answer(
            question,
            CANDIDATE_PROFILE,
        )

        if answer is None:
            unresolved.append(question)
            continue

        answers[question_id] = answer

    return answers, unresolved


def format_unresolved_questions(
    questions: list[dict],
) -> str:
    names = [
        question.get("questionName") or "Unknown question" for question in questions
    ]

    return " | ".join(names)


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

    status = apply_status.get(job_id)

    if status == 200:
        return True

    jobs = response.get("jobs") or []

    for item in jobs:
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
    # 1. Check external apply
    # ------------------------------------------------------------------

    print("[CHECK] Fetching job details...")

    try:
        external = jc.is_external_apply(
            job.job_id,
            sid,
        )

    except Exception as e:
        reason = f"job detail check failed: {e}"

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
    # 2. Start apply workflow
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

    except Exception as e:
        reason = f"initial apply failed: {e}"

        append_log(
            row,
            "FAILED",
            reason,
        )

        print(f"[FAILED] {reason}")

        return "FAILED"

    # ------------------------------------------------------------------
    # 3. Already applied detection
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
    # 5. Questionnaire
    # ------------------------------------------------------------------

    job_result = extract_job_result(initial)

    questionnaire = job_result.get("questionnaire") or []

    if not questionnaire:
        reason = "apply response was neither success nor questionnaire workflow"

        append_log(
            row,
            "FAILED",
            reason,
        )

        print(f"[FAILED] {reason}")

        return "FAILED"

    print(f"[QUESTIONNAIRE] " f"{len(questionnaire)} question(s)")

    answers, unresolved = resolve_questionnaire(questionnaire)

    if unresolved:
        reason = format_unresolved_questions(unresolved)

        append_log(
            row,
            "MANUAL_REVIEW",
            reason,
        )

        print("[MANUAL_REVIEW]")

        for question in unresolved:
            print("  - " + (question.get("questionName") or "Unknown question"))

        return "MANUAL_REVIEW"

    print("[QUESTIONNAIRE] All answers resolved")

    for question in questionnaire:
        question_id = question["questionId"]

        print(f'  {question.get("questionName")} ' f"-> {answers[question_id]}")

    # ------------------------------------------------------------------
    # 6. Submit questionnaire
    # ------------------------------------------------------------------

    try:
        final = jc.submit_questionnaire_answers(
            job=job,
            answers=answers,
            sid=sid,
            source="search",
        )

    except Exception as e:
        reason = f"questionnaire submit failed: {e}"

        append_log(
            row,
            "FAILED",
            reason,
        )

        print(f"[FAILED] {reason}")

        return "FAILED"

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

    if response_is_already_applied(final):
        append_log(
            row,
            "ALREADY_APPLIED",
            "platform reports existing application",
        )

        print("[ALREADY_APPLIED]")

        return "ALREADY_APPLIED"

    reason = "questionnaire submission returned unknown response"

    append_log(
        row,
        "FAILED",
        reason,
    )

    print("[FAILED] Unknown final response")

    print(
        json.dumps(
            final,
            indent=2,
            ensure_ascii=False,
        )
    )

    return "FAILED"


# ==============================================================================
# Main
# ==============================================================================


def main():
    load_dotenv(".env")

    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")

    if not username or not password:
        raise RuntimeError("USERNAME or PASSWORD missing from .env")

    ensure_log_file()

    jobs = load_eligible_jobs()

    terminal_job_ids = load_terminal_job_ids()

    pending_jobs = [row for row in jobs if row["job_id"] not in terminal_job_ids]

    print("=" * 110)
    print("AI JOB APPLICATION RUNNER")
    print("=" * 110)

    print(f"Eligible jobs:       {len(jobs)}")
    print(f"Previously terminal: {len(terminal_job_ids)}")
    print(f"Pending candidates:  {len(pending_jobs)}")
    print(f"Success batch limit: {MAX_APPLICATIONS}")

    print("\n[1] Logging in...")

    client = NaukriLoginClient(
        username,
        password,
    )

    client.login()

    print("[OK] Login successful")

    jc = NaukriJobClient(client)

    successful_applications = 0

    counters = {
        "APPLIED": 0,
        "ALREADY_APPLIED": 0,
        "MANUAL_REVIEW": 0,
        "EXTERNAL": 0,
        "FAILED": 0,
    }

    for row in pending_jobs:
        if successful_applications >= MAX_APPLICATIONS:
            print("\n[LIMIT] Successful application batch limit reached")

            break

        status = process_job(
            jc,
            row,
        )

        if status in counters:
            counters[status] += 1

        if status == "APPLIED":
            successful_applications += 1

        print(
            f"\nProgress: "
            f"{successful_applications}/"
            f"{MAX_APPLICATIONS} successful applications"
        )

        time.sleep(SLEEP_BETWEEN_JOBS)

    print("\n" + "=" * 110)
    print("RUN SUMMARY")
    print("=" * 110)

    for status, count in counters.items():
        print(f"{status:<20} {count}")

    print(f"\nSuccessful applications this run: " f"{successful_applications}")


if __name__ == "__main__":
    main()
