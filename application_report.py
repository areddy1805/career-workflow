from __future__ import annotations

import argparse
import os
from typing import Any

from src.application.ledger import ApplicationLedger


def print_table(
    headers: list[str],
    rows: list[list[Any]],
) -> None:
    if not rows:
        print("No records.")
        return

    widths = [len(header) for header in headers]

    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(
                widths[index],
                len(str(value)),
            )

    header_line = "  ".join(
        header.ljust(widths[index]) for index, header in enumerate(headers)
    )

    separator = "  ".join("-" * width for width in widths)

    print(header_line)
    print(separator)

    for row in rows:
        print(
            "  ".join(
                str(value).ljust(widths[index]) for index, value in enumerate(row)
            )
        )


def print_lifecycle_summary(
    ledger: ApplicationLedger,
) -> None:
    print("APPLICATION LIFECYCLE")
    print()

    summary = ledger.lifecycle_summary()

    order = (
        "SUBMITTED",
        "VIEWED",
        "SHORTLISTED",
        "INTERVIEW",
        "REJECTED",
        "OFFER",
        "UNKNOWN",
    )

    rows = [
        [
            stage,
            summary.get(stage, 0),
        ]
        for stage in order
    ]

    print_table(
        ["Stage", "Count"],
        rows,
    )


def print_funnel(
    ledger: ApplicationLedger,
    dimension: str,
) -> None:
    print(f"FUNNEL BY {dimension.upper()}")

    print()

    data = ledger.funnel_breakdown(dimension)

    rows = [
        [
            row["dimension_value"],
            row["total"],
            row["submitted"],
            row["viewed"],
            row["shortlisted"],
            row["interview"],
            row["rejected"],
            row["offer"],
        ]
        for row in data
    ]

    print_table(
        [
            dimension.title(),
            "Total",
            "Submitted",
            "Viewed",
            "Shortlisted",
            "Interview",
            "Rejected",
            "Offer",
        ],
        rows,
    )


def print_stale(
    ledger: ApplicationLedger,
    days: int,
) -> None:
    print(f"STALE APPLICATIONS > {days} DAYS")

    print()

    data = ledger.stale_applications(stale_after_days=days)

    rows = [
        [
            row["job_id"],
            row["title"],
            row["company"],
            row["priority"],
            row["subtrack"],
            row["lifecycle_stage"],
            row["server_status"] or "",
        ]
        for row in data
    ]

    print_table(
        [
            "Job ID",
            "Title",
            "Company",
            "Priority",
            "Subtrack",
            "Lifecycle",
            "Server Status",
        ],
        rows,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=("Application lifecycle and " "conversion reporting")
    )

    parser.add_argument(
        "--dimension",
        choices=(
            "priority",
            "subtrack",
            "company",
        ),
        default="priority",
    )

    parser.add_argument(
        "--stale-days",
        type=int,
        default=int(
            os.getenv(
                "STALE_APPLICATION_DAYS",
                "14",
            )
        ),
    )

    args = parser.parse_args()

    ledger = ApplicationLedger(
        os.getenv(
            "APPLICATION_LEDGER_PATH",
            "data/application_ledger.db",
        )
    )

    print_lifecycle_summary(ledger)

    print()
    print()

    print_funnel(
        ledger,
        args.dimension,
    )

    print()
    print()

    print_stale(
        ledger,
        args.stale_days,
    )


if __name__ == "__main__":
    main()
