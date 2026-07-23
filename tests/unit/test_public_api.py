"""Tests for the public library API."""

from __future__ import annotations

import pytest

from helpers import FIXTURES
from ontolog import InferOutput, infer
from ontolog.config import default_config
from ontolog.ingestion.formats import LogFormat


@pytest.mark.parametrize("export_format", ["mermaid", "markdown", "json-schema"])
def test_infer_returns_infer_output(export_format: str) -> None:
    output = infer(FIXTURES / "controlboard.log", format=export_format)

    assert isinstance(output, InferOutput)
    assert output.artifact
    assert len(output.model.entities) >= 2
    assert len(output.model.events) >= 3


def test_infer_uses_custom_config() -> None:
    config = default_config()
    output = infer(
        FIXTURES / "controlboard.log",
        format="markdown",
        config=config,
        log_format=LogFormat.PLAIN,
    )

    assert len(output.model.fields) >= 1
