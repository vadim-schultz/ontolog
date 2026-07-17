"""Tests for Pydantic source export."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from helpers import aggregate_fixture
from ontolog.config import ConfidenceThresholds, OntologConfig
from ontolog.export.formats import ExportFormat
from ontolog.export.registry import export_domain_model

EXPORT_CONFIG = OntologConfig(confidence=ConfidenceThresholds(export=0.6))


def test_generates_entity_classes(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    source = export_domain_model(model, ExportFormat.PYDANTIC)
    assert "class Controlboard" in source
    assert "class Interface" in source


def test_generates_typed_fields(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    source = export_domain_model(model, ExportFormat.PYDANTIC)
    assert "from ipaddress import IPv4Address" in source
    assert "destination: IPv4Address = Field(description='IPv4 address')" in source
    assert (
        "payload: str = Field(description='hexadecimal string', pattern='^[0-9a-fA-F]+$')" in source
    )


def test_omits_ineligible_entities(tmp_path: Path) -> None:
    strict = OntologConfig(confidence=ConfidenceThresholds(export=0.99))
    model = aggregate_fixture("controlboard.log", tmp_path, config=strict)
    source = export_domain_model(model, ExportFormat.PYDANTIC)
    assert "class ControlBoard" not in source


def test_generated_code_passes_ruff(tmp_path: Path) -> None:
    if shutil.which("ruff") is None:
        pytest.skip("ruff not installed")
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    source = export_domain_model(model, ExportFormat.PYDANTIC)
    path = tmp_path / "generated.py"
    path.write_text(source, encoding="utf-8")
    result = subprocess.run(
        ["ruff", "check", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_generated_code_passes_mypy(tmp_path: Path) -> None:
    if shutil.which("mypy") is None:
        pytest.skip("mypy not installed")
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    source = export_domain_model(model, ExportFormat.PYDANTIC)
    path = tmp_path / "generated.py"
    path.write_text(source, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "mypy", str(path), "--strict"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
