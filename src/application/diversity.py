from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DiversityPolicy:
    max_per_company_per_run: int = 2
    max_per_role_family_per_company: int = 1


def normalize_company(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def normalize_role_family(value: str) -> str:
    text = (value or "").lower()
    text = re.sub(r"\b(senior|sr|junior|jr|lead|principal|staff|hiring for|opening at)\b", " ", text)
    text = re.sub(r"[^a-z0-9+#]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def diversify_jobs(jobs: list[Any], *, historical_company_counts: dict[str, int] | None = None,
                   policy: DiversityPolicy | None = None) -> list[Any]:
    policy = policy or DiversityPolicy()
    history = historical_company_counts or {}
    company_run_counts: dict[str, int] = defaultdict(int)
    family_counts: dict[tuple[str, str], int] = defaultdict(int)

    ranked = sorted(
        enumerate(jobs),
        key=lambda pair: (history.get(normalize_company(pair[1].company), 0), pair[0]),
    )
    selected: list[Any] = []
    for _, job in ranked:
        company = normalize_company(job.company)
        family = normalize_role_family(job.title)
        if company_run_counts[company] >= policy.max_per_company_per_run:
            continue
        if family_counts[(company, family)] >= policy.max_per_role_family_per_company:
            continue
        selected.append(job)
        company_run_counts[company] += 1
        family_counts[(company, family)] += 1
    return selected
