"""Tests for the unified infer pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from helpers import FIXTURES
from ontolog import InferOutput, infer
from ontolog.export import ExportOptions
from ontolog.ingestion.formats import LogFormat


def test_infer_returns_infer_output_with_mermaid() -> None:
    output = infer(FIXTURES / "controlboard.log", format="mermaid")

    assert isinstance(output, InferOutput)
    assert "erDiagram" in output.artifact
    assert len(output.model.entities) >= 2


def test_infer_requires_export_format() -> None:
    with pytest.raises(TypeError):
        infer(FIXTURES / "controlboard.log")  # type: ignore[call-arg]


def test_infer_respects_log_format() -> None:
    output = infer(
        FIXTURES / "controlboard.log",
        format="markdown",
        log_format=LogFormat.PLAIN,
    )

    assert len(output.model.fields) >= 1


def test_infer_export_all_includes_more_than_default() -> None:
    default_output = infer(FIXTURES / "controlboard.log", format="markdown")
    all_output = infer(
        FIXTURES / "controlboard.log",
        format="markdown",
        export_options=ExportOptions(include_ineligible=True),
    )

    assert len(all_output.artifact) >= len(default_output.artifact)


def test_infer_uses_ephemeral_store(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    infer(FIXTURES / "controlboard.log", format="mermaid")

    assert not (tmp_path / "ontolog.db").exists()
