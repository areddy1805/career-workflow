from __future__ import annotations

import os

from dotenv import load_dotenv

from src.application.ledger import ApplicationLedger
from src.client.naukri_client import NaukriLoginClient

load_dotenv()


LEDGER_PATH = os.getenv(
    "APPLICATION_LEDGER_PATH",
    "data/application_ledger.db",
)


STALE_APPLICATION_DAYS = int(
    os.getenv(
        "STALE_APPLICATION_DAYS",
        "14",
    )
)


APPLICATION_HISTORY_PAGE_SIZE = int(
    os.getenv(
        "APPLICATION_HISTORY_PAGE_SIZE",
        "50",
    )
)


APPLICATION_HISTORY_DAYS = int(
    os.getenv(
        "APPLICATION_HISTORY_DAYS",
        "90",
    )
)


def build_client() -> NaukriLoginClient:
    """
    Authenticate with Naukri and return the login client.

    Application-history APIs currently belong to NaukriLoginClient,
    not NaukriJobClient.
    """

    username = os.getenv(
        "NAUKRI_USERNAME",
    )

    password = os.getenv(
        "NAUKRI_PASSWORD",
    )

    if not username:
        raise RuntimeError("NAUKRI_USERNAME environment variable is not set")

    if not password:
        raise RuntimeError("NAUKRI_PASSWORD environment variable is not set")

    client = NaukriLoginClient(
        username,
        password,
    )

    client.login()

    return client


def fetch_all_application_history(
    client: NaukriLoginClient,
    *,
    page_size: int = APPLICATION_HISTORY_PAGE_SIZE,
    days: int = APPLICATION_HISTORY_DAYS,
) -> list:
    """
    Fetch and parse all available application-history pages.

    Pagination stops when:
        1. the API returns an empty page,
        2. the page contains fewer items than page_size,
        3. or the server returns a page containing no unseen job IDs.

    The duplicate-page guard prevents an infinite loop if the server
    ignores pageNumber and repeatedly returns the same page.
    """

    history = []

    seen_job_ids: set[str] = set()

    page_number = 1

    while True:
        raw_history = client.get_application_history(
            page_size=page_size,
            days=days,
            page_number=page_number,
        )

        page_history = client.parse_history(
            raw_history,
        )

        if not page_history:
            break

        new_items = [
            item for item in page_history if str(item.job_id) not in seen_job_ids
        ]

        if not new_items:
            break

        history.extend(
            new_items,
        )

        seen_job_ids.update(str(item.job_id) for item in new_items)

        if len(page_history) < page_size:
            break

        page_number += 1

    return history


def print_local_summary(
    ledger: ApplicationLedger,
) -> None:
    print("Local ledger summary:")

    summary = ledger.summary()

    for status, count in sorted(
        summary.items(),
    ):
        print(f"  {status:<24} " f"{count}")


def print_lifecycle_summary(
    ledger: ApplicationLedger,
) -> None:
    print()

    print("Recruiting lifecycle summary:")

    lifecycle = ledger.lifecycle_summary()

    stage_order = (
        "SUBMITTED",
        "VIEWED",
        "SHORTLISTED",
        "INTERVIEW",
        "REJECTED",
        "OFFER",
        "UNKNOWN",
    )

    printed = False

    for stage in stage_order:
        count = lifecycle.get(
            stage,
            0,
        )

        if not count:
            continue

        print(f"  {stage:<24} " f"{count}")

        printed = True

    if not printed:
        print(f"  {'NO_SERVER_STATUS':<24} " f"0")


def print_stale_applications(
    ledger: ApplicationLedger,
) -> None:
    stale = ledger.stale_applications(
        stale_after_days=STALE_APPLICATION_DAYS,
    )

    print()

    print("Stale applications " f"(>{STALE_APPLICATION_DAYS} days) : " f"{len(stale)}")

    if not stale:
        return

    print()

    for application in stale:
        print(
            "  "
            f"{application['job_id']} | "
            f"{application['title']} | "
            f"{application['company']} | "
            f"{application['lifecycle_stage']} | "
            f"{application['server_status'] or 'NO_STATUS'}"
        )


def print_funnel_breakdown(
    ledger: ApplicationLedger,
    *,
    dimension: str,
) -> None:
    rows = ledger.funnel_breakdown(
        dimension,
    )

    print()

    print(f"Lifecycle funnel by {dimension}:")

    if not rows:
        print("  No application data available.")

        return

    print(
        "  "
        f"{dimension.upper():<24} "
        f"{'TOTAL':>5} "
        f"{'SUB':>5} "
        f"{'VIEW':>5} "
        f"{'SHORT':>5} "
        f"{'INT':>5} "
        f"{'REJ':>5} "
        f"{'OFFER':>5}"
    )

    for row in rows:
        print(
            "  "
            f"{str(row['dimension_value']):<24} "
            f"{int(row['total'] or 0):>5} "
            f"{int(row['submitted'] or 0):>5} "
            f"{int(row['viewed'] or 0):>5} "
            f"{int(row['shortlisted'] or 0):>5} "
            f"{int(row['interview'] or 0):>5} "
            f"{int(row['rejected'] or 0):>5} "
            f"{int(row['offer'] or 0):>5}"
        )


def main() -> None:
    client = build_client()

    ledger = ApplicationLedger(
        LEDGER_PATH,
    )

    history = fetch_all_application_history(
        client,
    )

    changed = ledger.reconcile_server_history(
        history,
    )

    print(f"Server applications fetched : " f"{len(history)}")

    print(f"New/changed records         : " f"{changed}")

    print_local_summary(
        ledger,
    )

    print_lifecycle_summary(
        ledger,
    )

    print_stale_applications(
        ledger,
    )

    print_funnel_breakdown(
        ledger,
        dimension="priority",
    )

    print_funnel_breakdown(
        ledger,
        dimension="subtrack",
    )


if __name__ == "__main__":
    main()
