"""Tests for field aggregation and alternatives."""

from __future__ import annotations

from pathlib import Path

from helpers import infer_fixture
from ontolog.config import default_config
from ontolog.inference.aggregate import aggregate_inference_result
from ontolog.models.candidate import FieldCandidate, InferenceResult
from ontolog.models.evidence import Evidence


def test_conflicting_field_types_produce_alternative() -> None:
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
    field = model.fields[0]
    assert field.type_name.value == "ipv4"
    assert len(field.type_name.alternatives) == 1
    assert field.type_name.alternatives[0].value == "string"


def test_higher_weighted_confidence_wins_primary() -> None:
    weak = FieldCandidate(
        name="destination",
        type_name="string",
        confidence=0.99,
        graph_node_id="field:destination",
        evidence=(Evidence(source="llm", score=0.99, explanation="guessed"),),
    )
    strong = FieldCandidate(
        name="destination",
        type_name="ipv4",
        confidence=0.8,
        graph_node_id="field:destination",
        evidence=(Evidence(source="regex", score=0.8, explanation="ipv4"),),
    )
    model = aggregate_inference_result(
        InferenceResult(fields=(weak, strong)),
        weights=default_config().source_weights,
        thresholds=default_config().confidence,
    )
    assert model.fields[0].type_name.value == "ipv4"


def test_controlboard_field_types(tmp_path: Path) -> None:
    inference = infer_fixture("controlboard.log", tmp_path)
    model = aggregate_inference_result(
        inference,
        weights=default_config().source_weights,
        thresholds=default_config().confidence,
    )
    destination = next(field for field in model.fields if field.name == "destination")
    payload = next(field for field in model.fields if field.name == "payload")
    assert destination.type_name.value == "ipv4"
    assert payload.type_name.value == "hex"
    assert not destination.type_name.alternatives
    assert not payload.type_name.alternatives
