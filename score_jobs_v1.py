import csv
import re
from pathlib import Path


INPUT_FILE = Path("data/raw_jobs.csv")
OUTPUT_FILE = Path("data/scored_jobs.csv")


AI_POSITIVE = {
    "generative ai": 8,
    "genai": 8,
    "gen ai": 8,
    "llm": 8,
    "large language model": 8,
    "rag": 9,
    "retrieval augmented generation": 9,
    "agentic ai": 9,
    "ai agent": 8,
    "langchain": 6,
    "langgraph": 7,
    "semantic kernel": 7,
    "azure openai": 8,
    "azure ai": 7,
    "prompt engineering": 4,
    "vector database": 5,
    "vector db": 5,
    "reranking": 5,
    "embedding": 4,
    "python": 4,
    "fastapi": 5,
    "api development": 4,
    "rest api": 3,
    "docker": 3,
    "azure": 3,
}


FULLSTACK_POSITIVE = {
    "angular": 10,
    "typescript": 8,
    "javascript": 7,
    "node.js": 10,
    "nodejs": 10,
    "express.js": 8,
    "expressjs": 8,
    "mongodb": 7,
    "mean stack": 10,
    "full stack": 6,
    "fullstack": 6,
    "rest api": 5,
    "microservices": 3,
    "rxjs": 5,
    "html": 3,
    "css": 3,
    "bootstrap": 2,
    "docker": 2,
    "azure": 2,
}


HARD_REJECT_TITLE_TERMS = [
    "data scientist",
    "data science",
    "computer vision engineer",
    "simulation engineer",
    "thermal engineer",
    "autocad",
    "embedded engineer",
    "firmware engineer",
]


STRONG_NEGATIVE_TERMS = {
    "spring boot": -10,
    "java developer": -10,
    ".net developer": -10,
    "c# developer": -10,
    "php developer": -10,
    "salesforce developer": -12,
    "sap": -12,
    "embedded systems": -12,
    "matlab": -10,
    "simulink": -10,
}


ALLOWED_LOCATION_TERMS = [
    "pune",
    "remote",
    "india",
]


def normalize(value):
    return re.sub(
        r"\s+",
        " ",
        (value or "").lower(),
    ).strip()


def combined_text(row):
    return normalize(
        " ".join(
            [
                row.get("title", ""),
                row.get("tags", ""),
                row.get("description", ""),
            ]
        )
    )


def weighted_score(text, weights):
    score = 0
    matches = []

    for term, weight in weights.items():
        if term in text:
            score += weight
            matches.append(term)

    return score, matches


def negative_score(text):
    score = 0
    matches = []

    for term, penalty in STRONG_NEGATIVE_TERMS.items():
        if term in text:
            score += penalty
            matches.append(term)

    return score, matches


def location_status(location):
    location_text = normalize(location)

    if any(
        term in location_text
        for term in ALLOWED_LOCATION_TERMS
    ):
        return "ACCEPT"

    return "REVIEW"


def classify(row):
    title = normalize(row["title"])
    text = combined_text(row)

    for term in HARD_REJECT_TITLE_TERMS:
        if term in title:
            return {
                "decision": "REJECT",
                "track": "NONE",
                "score": -100,
                "reason": f"hard reject title: {term}",
                "matches": "",
                "location_status": location_status(
                    row["location"]
                ),
            }

    ai_score, ai_matches = weighted_score(
        text,
        AI_POSITIVE,
    )

    fs_score, fs_matches = weighted_score(
        text,
        FULLSTACK_POSITIVE,
    )

    penalty, negative_matches = negative_score(text)

    ai_score += penalty
    fs_score += penalty

    if ai_score >= fs_score:
        track = "AI"
        score = ai_score
        matches = ai_matches
    else:
        track = "FULLSTACK"
        score = fs_score
        matches = fs_matches

    loc_status = location_status(row["location"])

    if score >= 30:
        decision = "SHORTLIST"
    elif score >= 15:
        decision = "BORDERLINE"
    else:
        decision = "REJECT"

    if negative_matches:
        reason = (
            "negative terms: "
            + ", ".join(negative_matches)
        )
    else:
        reason = ""

    return {
        "decision": decision,
        "track": track,
        "score": score,
        "reason": reason,
        "matches": ", ".join(matches),
        "location_status": loc_status,
    }


def main():
    with INPUT_FILE.open(
        encoding="utf-8",
        newline="",
    ) as file:
        jobs = list(csv.DictReader(file))

    output_rows = []

    for job in jobs:
        result = classify(job)

        output_rows.append(
            {
                **job,
                **result,
            }
        )

    output_rows.sort(
        key=lambda row: int(row["score"]),
        reverse=True,
    )

    fieldnames = list(output_rows[0].keys())

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(output_rows)

    counts = {}

    for row in output_rows:
        key = (
            row["decision"],
            row["track"],
            row["location_status"],
        )

        counts[key] = counts.get(key, 0) + 1

    print("=" * 80)
    print("SCORING SUMMARY")
    print("=" * 80)

    for key, count in sorted(counts.items()):
        print(
            f"{key[0]:<12} "
            f"{key[1]:<10} "
            f"{key[2]:<8} "
            f"{count:>4}"
        )

    print("\nTOP 30 JOBS")
    print("=" * 80)

    for row in output_rows[:30]:
        print(
            f'{row["score"]:>3} | '
            f'{row["track"]:<9} | '
            f'{row["location_status"]:<6} | '
            f'{row["title"]} | '
            f'{row["company"]} | '
            f'{row["location"]}'
        )


if __name__ == "__main__":
    main()
