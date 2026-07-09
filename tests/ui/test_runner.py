from __future__ import annotations

import sys

import pytest

from control_center.runner import (
    LIVE_CONFIRMATION,
    build_pipeline_command,
)


def test_build_dry_pipeline_command():
    command = build_pipeline_command(
        live=False,
        max_applications=500,
    )

    assert command[0] == sys.executable

    assert "--max-applications" in command

    assert "500" in command

    assert "--live" not in command

    assert "--confirm-live" not in command


def test_build_live_pipeline_command():
    command = build_pipeline_command(
        live=True,
        max_applications=3,
    )

    assert "--live" in command

    assert "--confirm-live" in command

    assert LIVE_CONFIRMATION in command

    assert "--max-applications" in command

    assert "3" in command


def test_build_live_canary_command():
    command = build_pipeline_command(
        live=True,
        max_applications=3,
        canary=True,
    )

    assert "--live" in command

    assert "--canary" in command


@pytest.mark.parametrize(
    "limit",
    [
        0,
        -1,
    ],
)
def test_reject_invalid_application_limit(
    limit,
):
    with pytest.raises(ValueError):
        build_pipeline_command(
            live=False,
            max_applications=limit,
        )
