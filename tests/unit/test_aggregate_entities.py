"""Tests for entity and pipeline aggregation."""

from __future__ import annotations

from pathlib import Path

from helpers import infer_fixture
from ontolog.config import default_config
from ontolog.inference.aggregate import aggregate_inference_result
from ontolog.models.candidate import EntityCandidate
from ontolog.models.evidence import Evidence


def test_single_entity_candidate_maps_to_entity() -> None:
    from ontolog.models.candidate import InferenceResult

    evidence = (Evidence(source="namespace", score=0.8, explanation="process entity"),)
    candidate = EntityCandidate(
        name="ControlBoard",
        slug="controlboard",
        confidence=0.8,
        graph_node_id="entity:controlboard",
        evidence=evidence,
    )
    model = aggregate_inference_result(
        InferenceResult(entities=(candidate,)),
        weights=default_config().source_weights,
        thresholds=default_config().confidence,
    )
    entity = model.entities[0]
    assert entity.slug == "controlboard"
    assert entity.name == "ControlBoard"
    assert entity.confidence > 0
    assert entity.evidence == evidence


def test_controlboard_aggregation_entities_and_events(tmp_path: Path) -> None:
    inference = infer_fixture("controlboard.log", tmp_path)
    model = aggregate_inference_result(
        inference,
        weights=default_config().source_weights,
        thresholds=default_config().confidence,
    )
    entity_slugs = {entity.slug for entity in model.entities}
    event_slugs = {event.slug for event in model.events}
    assert entity_slugs >= {"controlboard", "interface"}
    assert any("sent" in slug for slug in event_slugs)
    assert any("received" in slug for slug in event_slugs)


def test_controlboard_aggregation_relationship(tmp_path: Path) -> None:
    inference = infer_fixture("controlboard.log", tmp_path)
    model = aggregate_inference_result(
        inference,
        weights=default_config().source_weights,
        thresholds=default_config().confidence,
    )
    owns = next(relationship for relationship in model.relationships if relationship.kind == "owns")
    assert owns.source_name == "Controlboard"
    assert owns.target_name == "Interface"


def test_order_lifecycle_state_machine(tmp_path: Path) -> None:
    inference = infer_fixture("order_lifecycle.log", tmp_path)
    model = aggregate_inference_result(
        inference,
        weights=default_config().source_weights,
        thresholds=default_config().confidence,
    )
    assert model.state_machines
    machine = model.state_machines[0]
    assert set(machine.states) >= {"created", "validated", "running", "completed"}
    pairs = {(transition.from_state, transition.to_state) for transition in machine.transitions}
    assert ("created", "validated") in pairs
    assert ("validated", "running") in pairs
    assert ("running", "completed") in pairs
