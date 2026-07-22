"""Tests for entity inference."""

from __future__ import annotations

from pathlib import Path

from helpers import load_fixture_graph
from ontolog.config import default_config
from ontolog.evidence.graph import EvidenceGraph
from ontolog.inference.entities import EntityInferencePass
from ontolog.inference.runner import run_inference
from ontolog.models.finding import ProviderInput


def test_process_entity_promoted(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (EntityInferencePass(),),
        thresholds=default_config().confidence,
    )
    slugs = {entity.slug for entity in result.entities}
    assert "controlboard" in slugs


def test_interface_field_yields_interface_entity(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (EntityInferencePass(),),
        thresholds=default_config().confidence,
    )
    slugs = {entity.slug for entity in result.entities}
    assert "interface" in slugs


def test_entity_confidence_from_namespace_evidence(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("controlboard.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (EntityInferencePass(),),
        thresholds=default_config().confidence,
    )
    controlboard = next(entity for entity in result.entities if entity.slug == "controlboard")
    assert any(evidence.source == "namespace" for evidence in controlboard.evidence)


def test_unknown_entity_not_invented() -> None:
    graph = EvidenceGraph()
    result = run_inference(
        graph,
        ProviderInput(),
        (EntityInferencePass(),),
        thresholds=default_config().confidence,
    )
    assert result.entities == ()


def test_order_entity_from_events(tmp_path: Path) -> None:
    graph, data = load_fixture_graph("order_lifecycle.log", tmp_path)
    result = run_inference(
        graph,
        data,
        (EntityInferencePass(),),
        thresholds=default_config().confidence,
    )
    slugs = {entity.slug for entity in result.entities}
    assert "order" in slugs
    assert "orderservice" in slugs
