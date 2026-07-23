"""Tests for Pydantic source export."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from helpers import aggregate_fixture
from ontolog.config import ConfidenceThresholds, OntologConfig, default_config
from ontolog.export.formats import ExportFormat
from ontolog.export.registry import export_domain_model

EXPORT_CONFIG = OntologConfig(confidence=ConfidenceThresholds(export=0.6))


def test_generates_entity_classes(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    source = export_domain_model(model, ExportFormat.PYDANTIC)
    assert "class Controlboard" in source
    assert "class Interface" in source


def test_controlboard_nested_fields(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    source = export_domain_model(model, ExportFormat.PYDANTIC)
    interface_block = re.search(r"class Interface\(BaseModel\):.*?(?=\nclass |\Z)", source, re.S)
    assert interface_block is not None
    assert "destination:" in interface_block.group(0)
    assert "DomainFields" not in source
    assert "UnscopedFields" not in source


def test_controlboard_composition(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    source = export_domain_model(model, ExportFormat.PYDANTIC)
    controlboard_block = re.search(
        r"class Controlboard\(BaseModel\):.*?(?=\nclass |\Z)",
        source,
        re.S,
    )
    assert controlboard_block is not None
    assert "packet: Packet = Field(" in controlboard_block.group(0)
    packet_block = re.search(r"class Packet\(BaseModel\):.*?(?=\nclass |\Z)", source, re.S)
    assert packet_block is not None
    assert "interface: Interface = Field(" in packet_block.group(0)


def test_controlboard_no_field_duplication_across_children(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    source = export_domain_model(model, ExportFormat.PYDANTIC)
    assert source.count("destination: IPv4Address") == 1
    assert source.count("payload: str") == 1


def test_field_description_includes_confidence(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    source = export_domain_model(model, ExportFormat.PYDANTIC)
    assert re.search(
        r"destination: IPv4Address = Field\(description='IPv4 address \(confidence=[0-9.]+\)'\)",
        source,
    )


def test_generates_typed_fields(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    source = export_domain_model(model, ExportFormat.PYDANTIC)
    assert "from ipaddress import IPv4Address" in source
    assert re.search(
        r"destination: IPv4Address = Field\(description='IPv4 address \(confidence=[0-9.]+\)'\)",
        source,
    )
    assert re.search(
        r"payload: str = Field\(\s*"
        r"description='hexadecimal string \(confidence=[0-9.]+\)',\s*"
        r"pattern='\^\[0-9a-fA-F\]\+\$',\s*"
        r"\)",
        source,
        re.S,
    )


def test_openssh_export_with_default_threshold(tmp_path: Path) -> None:
    model = aggregate_fixture("loghub/openssh_2k.log", tmp_path, config=default_config())
    source = export_domain_model(model, ExportFormat.PYDANTIC)
    assert "class Sshd(BaseModel):" in source
    assert re.search(
        r"uid: int = Field\(description='integer \(confidence=[0-9.]+\)'\)",
        source,
    )
    assert re.search(
        r"rhost: IPv4Address = Field\(description='IPv4 address \(confidence=[0-9.]+\)'\)",
        source,
    )


def test_openssh_export_passes_ruff(tmp_path: Path) -> None:
    if shutil.which("ruff") is None:
        pytest.skip("ruff not installed")
    model = aggregate_fixture("loghub/openssh_2k.log", tmp_path, config=EXPORT_CONFIG)
    source = export_domain_model(model, ExportFormat.PYDANTIC)
    assert "*: " not in source
    path = tmp_path / "generated_openssh.py"
    path.write_text(source, encoding="utf-8")
    result = subprocess.run(
        ["ruff", "check", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_openssh_uid_is_int(tmp_path: Path) -> None:
    model = aggregate_fixture("loghub/openssh_2k.log", tmp_path, config=EXPORT_CONFIG)
    source = export_domain_model(model, ExportFormat.PYDANTIC)
    assert re.search(
        r"uid: int = Field\(description='integer \(confidence=[0-9.]+\)'\)",
        source,
    )
    assert re.search(
        r"euid: int = Field\(description='integer \(confidence=[0-9.]+\)'\)",
        source,
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
