"""Tests for Markdown report export."""

from __future__ import annotations

from pathlib import Path

from helpers import aggregate_fixture
from ontolog.config import ConfidenceThresholds, OntologConfig, default_config
from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
from ontolog.export.registry import export_domain_model
from ontolog.inference.aggregate import aggregate_inference_result
from ontolog.models.candidate import FieldCandidate, InferenceResult
from ontolog.models.evidence import Evidence

EXPORT_CONFIG = OntologConfig(confidence=ConfidenceThresholds(export=0.6))


def test_report_lists_entities(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    report = export_domain_model(model, ExportFormat.MARKDOWN)
    assert "# Entities" in report
    assert "Controlboard" in report
    assert "confidence" in report


def test_report_lists_fields_with_alternatives() -> None:
    ipv4 = FieldCandidate(
        name="destination",
        type_name="ipv4",
        confidence=0.95,
        graph_node_id="field:destination",
        evidence=(Evidence(source="regex", score=0.95, explanation="ipv4"),),
    )
    string_type = FieldCandidate(
        name="destination",
        type_name="string",
        confidence=0.6,
        graph_node_id="field:destination",
        evidence=(Evidence(source="llm", score=0.6, explanation="guessed"),),
    )
    model = aggregate_inference_result(
        InferenceResult(fields=(ipv4, string_type)),
        weights=default_config().source_weights,
        thresholds=default_config().confidence,
    )
    report = export_domain_model(
        model,
        ExportFormat.MARKDOWN,
        options=ExportOptions(include_ineligible=True),
    )
    assert "alternative `string`" in report


def test_report_omits_ineligible_by_default(tmp_path: Path) -> None:
    strict = OntologConfig(confidence=ConfidenceThresholds(export=0.99))
    model = aggregate_fixture("controlboard.log", tmp_path, config=strict)
    report = export_domain_model(model, ExportFormat.MARKDOWN)
    assert "PacketSent" not in report
    assert "PacketReceived" not in report


def test_report_provenance_optional(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path)
    report = export_domain_model(
        model,
        ExportFormat.MARKDOWN,
        options=ExportOptions(include_provenance=True),
    )
    assert "`namespace`" in report or "`regex`" in report
