from __future__ import annotations

import argparse
import json

from src.orchestration import (
    CareerWorkflowPipeline,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run the Career Workflow orchestration pipeline"
        )
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "Enable live application submission. "
            "Default is dry-run."
        ),
    )

    parser.add_argument(
        "--max-applications",
        type=int,
        default=3,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    pipeline = CareerWorkflowPipeline(
        dry_run=not args.live,
        max_applications=(
            args.max_applications
        ),
    )

    result = pipeline.run()

    print()
    print(
        json.dumps(
            result.to_dict(),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
