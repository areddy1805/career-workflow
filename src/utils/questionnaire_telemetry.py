import csv
import json
from datetime import UTC, datetime
from pathlib import Path

TELEMETRY_FILE = Path("data/questionnaire_telemetry.csv")


FIELDS = [
    "observed_at",
    "job_id",
    "title",
    "company",
    "priority",
    "subtrack",
    "question_id",
    "question",
    "question_type",
    "category",
    "mandatory",
    "answer_options",
]


def ensure_telemetry_file():
    TELEMETRY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if TELEMETRY_FILE.exists():
        return

    with TELEMETRY_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=FIELDS,
        )

        writer.writeheader()


def log_unresolved_questions(
    row: dict,
    questions: list[dict],
):
    ensure_telemetry_file()

    observed_at = datetime.now(UTC).isoformat()

    with TELEMETRY_FILE.open(
        "a",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=FIELDS,
        )

        for question in questions:
            writer.writerow(
                {
                    "observed_at": observed_at,
                    "job_id": row.get(
                        "job_id",
                        "",
                    ),
                    "title": row.get(
                        "title",
                        "",
                    ),
                    "company": row.get(
                        "company",
                        "",
                    ),
                    "priority": row.get(
                        "priority",
                        "",
                    ),
                    "subtrack": row.get(
                        "subtrack",
                        "",
                    ),
                    "question_id": question.get(
                        "questionId",
                        "",
                    ),
                    "question": question.get(
                        "questionName",
                        "",
                    ),
                    "question_type": question.get(
                        "questionType",
                        "",
                    ),
                    "category": question.get(
                        "category",
                        "",
                    ),
                    "mandatory": question.get(
                        "isMandatory",
                        "",
                    ),
                    "answer_options": json.dumps(
                        question.get("answerOption") or {},
                        ensure_ascii=False,
                    ),
                }
            )
