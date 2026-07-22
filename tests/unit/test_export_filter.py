"""Tests for export view filtering and registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from helpers import aggregate_fixture
from ontolog.config import ConfidenceThresholds, OntologConfig, default_config
from ontolog.errors import ExportError
from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
from ontolog.export.registry import (
    export_domain_model,
    parse_export_format,
    registered_formats,
)
from ontolog.export.view import export_view
from ontolog.inference.aggregate import aggregate_inference_result
from ontolog.models.candidate import FieldCandidate, InferenceResult
from ontolog.models.evidence import Evidence

EXPORT_CONFIG = OntologConfig(confidence=ConfidenceThresholds(export=0.6))


def test_export_view_includes_entity_with_eligible_fields() -> None:
    """Export entities that carry export-eligible fields even when below entity threshold."""
    from ontolog.models.domain import Entity, Field, ProbabilisticClaim, ProbabilisticDomainModel

    model = ProbabilisticDomainModel(
        entities=(
            Entity(
                name="Sshd",
                slug="sshd",
                confidence=0.68,
                evidence=(),
                export_eligible=False,
            ),
        ),
        fields=(
            Field(
                name="uid",
                graph_node_id="field:cluster_1:uid",
                entity_slug="sshd",
                type_name=ProbabilisticClaim(
                    value="int",
                    confidence=1.0,
                    evidence=(),
                    export_eligible=True,
                ),
            ),
        ),
    )
    view = export_view(model, ExportOptions())
    assert [entity.slug for entity in view.entities] == ["sshd"]
    assert {field.name for field in view.fields} == {"uid"}


def test_export_view_default_filters_ineligible() -> None:
    thresholds = ConfidenceThresholds(export=0.7)
    low = FieldCandidate(
        name="destination",
        type_name="ipv4",
        confidence=0.69,
        graph_node_id="field:destination",
        evidence=(Evidence(source="regex", score=0.69, explanation="ipv4"),),
    )
    high = FieldCandidate(
        name="payload",
        type_name="hex",
        confidence=0.95,
        graph_node_id="field:payload",
        evidence=(Evidence(source="regex", score=0.95, explanation="hex"),),
    )
    model = aggregate_inference_result(
        InferenceResult(fields=(low, high)),
        weights=default_config().source_weights,
        thresholds=thresholds,
    )
    view = export_view(model, ExportOptions())
    field_names = {field.name for field in view.fields}
    assert "payload" in field_names
    assert "destination" not in field_names


def test_export_view_include_ineligible() -> None:
    thresholds = ConfidenceThresholds(export=0.7)
    low = FieldCandidate(
        name="destination",
        type_name="ipv4",
        confidence=0.69,
        graph_node_id="field:destination",
        evidence=(Evidence(source="regex", score=0.69, explanation="ipv4"),),
    )
    model = aggregate_inference_result(
        InferenceResult(fields=(low,)),
        weights=default_config().source_weights,
        thresholds=thresholds,
    )
    view = export_view(model, ExportOptions(include_ineligible=True))
    assert {field.name for field in view.fields} == {"destination"}


def test_export_view_preserves_order(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path)
    view = export_view(model, ExportOptions())
    entity_slugs = [entity.slug for entity in view.entities]
    assert entity_slugs == sorted(entity_slugs)


def test_exporter_registry_lists_formats() -> None:
    formats = registered_formats()
    assert ExportFormat.PYDANTIC in formats
    assert ExportFormat.JSON_SCHEMA in formats
    assert ExportFormat.MERMAID in formats
    assert ExportFormat.MARKDOWN in formats
    assert ExportFormat.GRAPHML in formats
    assert len(formats) == 5


def test_exporter_for_unknown_raises() -> None:
    with pytest.raises(ExportError, match="unknown export format"):
        parse_export_format("not-a-format")


def test_export_domain_model_pydantic_stub(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    output = export_domain_model(model, ExportFormat.PYDANTIC)
    assert "class Controlboard" in output


def test_high_export_threshold_reduces_output(tmp_path: Path) -> None:
    strict = OntologConfig(confidence=ConfidenceThresholds(export=0.99))
    model = aggregate_fixture("controlboard.log", tmp_path, config=strict)
    default_output = export_domain_model(model, ExportFormat.MARKDOWN)
    full_output = export_domain_model(
        model,
        ExportFormat.MARKDOWN,
        options=ExportOptions(include_ineligible=True),
    )
    assert len(full_output) >= len(default_output)
