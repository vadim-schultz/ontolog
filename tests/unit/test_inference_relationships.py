"""Tests for relationship inference."""

from __future__ import annotations

from pathlib import Path

from helpers import load_fixture_graph
from ontolog.config import default_config
from ontolog.inference.relationships import RelationshipInferencePass
from ontolog.inference.runner import run_inference


def test_owns_from_has_field(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (RelationshipInferencePass(),),
        thresholds=default_config().confidence,
    )
    owns = {
        (relationship.source_name, relationship.target_name)
        for relationship in result.relationships
        if relationship.kind == "owns"
    }
    assert ("Controlboard", "Packet") in owns
    assert ("Packet", "Interface") in owns


def test_owns_confidence(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (RelationshipInferencePass(),),
        thresholds=default_config().confidence,
    )
    owns = next(
        relationship for relationship in result.relationships if relationship.kind == "owns"
    )
    assert owns.confidence >= 0.6


def test_co_occurrence_not_duplicated_as_owns(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (RelationshipInferencePass(),),
        thresholds=default_config().confidence,
    )
    kinds = {relationship.kind for relationship in result.relationships}
    assert kinds <= {"owns"}
