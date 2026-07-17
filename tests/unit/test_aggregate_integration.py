"""Integration tests for domain model aggregation."""

from __future__ import annotations

from pathlib import Path

from helpers import infer_fixture
from ontolog.config import ConfidenceThresholds, default_config
from ontolog.inference.aggregate import aggregate_inference_result
from ontolog.inference.builder import build_domain_model
from ontolog.models.candidate import InferenceResult
from ontolog.models.domain import ProbabilisticDomainModel
from ontolog.models.evidence import Evidence


def test_export_eligible_threshold() -> None:
    thresholds = ConfidenceThresholds(export=0.7)
    from ontolog.models.candidate import FieldCandidate

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
    aggregated = aggregate_inference_result(
        InferenceResult(fields=(low, high)),
        weights=default_config().source_weights,
        thresholds=thresholds,
    )
    destination = next(field for field in aggregated.fields if field.name == "destination")
    payload = next(field for field in aggregated.fields if field.name == "payload")
    assert not destination.type_name.export_eligible
    assert payload.type_name.export_eligible


def test_json_export_includes_provenance(tmp_path: Path) -> None:
    inference = infer_fixture("controlboard.log", tmp_path)
    model = aggregate_inference_result(
        inference,
        weights=default_config().source_weights,
        thresholds=default_config().confidence,
    )
    payload = model.model_dump()
    destination = next(field for field in payload["fields"] if field["name"] == "destination")
    type_claim = destination["type_name"]
    assert "confidence" in type_claim
    assert "evidence" in type_claim
    assert type_claim["evidence"][0]["source"]
    assert "export_eligible" in type_claim


def test_aggregate_is_reproducible() -> None:
    evidence = (Evidence(source="regex", score=0.9, explanation="ipv4"),)
    from ontolog.models.candidate import EntityCandidate

    candidate = EntityCandidate(
        name="ControlBoard",
        slug="controlboard",
        confidence=0.9,
        graph_node_id="entity:controlboard",
        evidence=evidence,
    )
    result = InferenceResult(entities=(candidate,))
    config = default_config()
    first = aggregate_inference_result(
        result,
        weights=config.source_weights,
        thresholds=config.confidence,
    )
    second = aggregate_inference_result(
        result,
        weights=config.source_weights,
        thresholds=config.confidence,
    )
    assert first.model_dump() == second.model_dump()


def test_infer_fixture_produces_stable_model(tmp_path: Path) -> None:
    config = default_config()
    first_dir = tmp_path / "run-a"
    second_dir = tmp_path / "run-b"
    first_dir.mkdir()
    second_dir.mkdir()
    first_inference = infer_fixture("controlboard.log", first_dir)
    second_inference = infer_fixture("controlboard.log", second_dir)
    first = aggregate_inference_result(
        first_inference,
        weights=config.source_weights,
        thresholds=config.confidence,
    )
    second = aggregate_inference_result(
        second_inference,
        weights=config.source_weights,
        thresholds=config.confidence,
    )
    assert first.model_dump() == second.model_dump()


def test_build_domain_model(tmp_path: Path) -> None:
    from helpers import extract_fixture_to_store

    store_path = tmp_path / "ontolog.db"
    extract_fixture_to_store("controlboard.log", store_path)
    model = build_domain_model(store_path, config=default_config())
    assert isinstance(model, ProbabilisticDomainModel)
    entity_slugs = {entity.slug for entity in model.entities}
    assert entity_slugs >= {"controlboard", "interface"}
