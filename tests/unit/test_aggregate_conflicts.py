"""Tests for tier-priority conflict resolution during aggregation."""

from __future__ import annotations

from ontolog.config import EvidenceSourceWeights, default_config
from ontolog.inference.aggregate import aggregate_inference_result
from ontolog.models.candidate import FieldCandidate, InferenceResult
from ontolog.models.evidence import Evidence


def test_deterministic_beats_llm_despite_lower_raw_score() -> None:
    llm = FieldCandidate(
        name="destination",
        type_name="string",
        confidence=0.99,
        graph_node_id="field:destination",
        evidence=(Evidence(source="openai", score=0.99, explanation="guessed string"),),
    )
    deterministic = FieldCandidate(
        name="destination",
        type_name="ipv4",
        confidence=0.95,
        graph_node_id="field:destination",
        evidence=(Evidence(source="regex", score=0.95, explanation="ipv4"),),
    )
    model = aggregate_inference_result(
        InferenceResult(fields=(llm, deterministic)),
        weights=default_config().source_weights,
        thresholds=default_config().confidence,
    )
    assert model.fields[0].type_name.value == "ipv4"


def test_human_beats_deterministic_despite_lower_raw_score() -> None:
    deterministic = FieldCandidate(
        name="destination",
        type_name="ipv4",
        confidence=0.95,
        graph_node_id="field:destination",
        evidence=(Evidence(source="regex", score=0.95, explanation="ipv4"),),
    )
    human = FieldCandidate(
        name="destination",
        type_name="string",
        confidence=0.7,
        graph_node_id="field:destination",
        evidence=(Evidence(source="human", score=0.7, explanation="corrected"),),
    )
    model = aggregate_inference_result(
        InferenceResult(fields=(deterministic, human)),
        weights=default_config().source_weights,
        thresholds=default_config().confidence,
    )
    assert model.fields[0].type_name.value == "string"


def test_tier_priority_not_overridden_by_weight_config() -> None:
    weights = EvidenceSourceWeights(human=1.0, deterministic=0.1, llm=0.9)
    llm = FieldCandidate(
        name="destination",
        type_name="string",
        confidence=0.99,
        graph_node_id="field:destination",
        evidence=(Evidence(source="llm", score=0.99, explanation="guessed"),),
    )
    deterministic = FieldCandidate(
        name="destination",
        type_name="ipv4",
        confidence=0.5,
        graph_node_id="field:destination",
        evidence=(Evidence(source="regex", score=0.5, explanation="ipv4"),),
    )
    model = aggregate_inference_result(
        InferenceResult(fields=(llm, deterministic)),
        weights=weights,
        thresholds=default_config().confidence,
    )
    assert model.fields[0].type_name.value == "ipv4"
