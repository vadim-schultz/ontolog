"""Tests for Mermaid export."""

from __future__ import annotations

import re
from pathlib import Path

from helpers import aggregate_fixture
from ontolog.config import ConfidenceThresholds, OntologConfig
from ontolog.export.formats import ExportFormat
from ontolog.export.registry import export_domain_model

EXPORT_CONFIG = OntologConfig(confidence=ConfidenceThresholds(export=0.6))


def test_er_diagram_controlboard(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    output = export_domain_model(model, ExportFormat.MERMAID)
    assert output.startswith("erDiagram")
    assert "Controlboard" in output
    assert "Interface" in output
    assert "owns" in output
    assert "IPv4Address destination" in output or "str destination" in output


def test_er_omits_ineligible_relationship(tmp_path: Path) -> None:
    strict = OntologConfig(confidence=ConfidenceThresholds(export=0.99))
    model = aggregate_fixture("controlboard.log", tmp_path, config=strict)
    output = export_domain_model(model, ExportFormat.MERMAID)
    assert "owns" not in output


def test_state_diagram_order_lifecycle(tmp_path: Path) -> None:
    model = aggregate_fixture("order_lifecycle.log", tmp_path)
    output = export_domain_model(model, ExportFormat.MERMAID)
    assert "stateDiagram-v2" in output
    for state in ("created", "validated", "running", "completed"):
        assert state in output


def test_mermaid_identifiers_sanitized(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path)
    output = export_domain_model(model, ExportFormat.MERMAID)
    for line in output.splitlines():
        if line.strip().startswith("erDiagram"):
            continue
        match = re.search(r"^\s+([A-Za-z_][A-Za-z0-9_]*)\s", line)
        if match:
            assert " " not in match.group(1)
