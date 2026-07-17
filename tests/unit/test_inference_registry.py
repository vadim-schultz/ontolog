"""Tests for inference registry and orchestrator."""

from __future__ import annotations

from ontolog.config import InferenceConfig, InferenceKind, default_config
from ontolog.evidence.graph import EvidenceGraph
from ontolog.inference.base import inference_registry
from ontolog.inference.entities import EntityInferencePass
from ontolog.inference.runner import run_inference
from ontolog.models.candidate import EntityCandidate, InferenceResult
from ontolog.models.evidence import Evidence
from ontolog.models.finding import ProviderInput


def test_entity_candidate_construct() -> None:
    evidence = Evidence(source="namespace", score=0.8, explanation="entity")
    candidate = EntityCandidate(
        name="Controlboard",
        slug="controlboard",
        confidence=0.8,
        graph_node_id="entity:controlboard",
        evidence=(evidence,),
    )
    assert candidate.slug == "controlboard"


def test_inference_result_empty() -> None:
    result = InferenceResult()
    assert result.entities == ()
    assert result.events == ()
    assert result.fields == ()
    assert result.relationships == ()
    assert result.state_machines == ()


def test_registry_default_all_enabled() -> None:
    passes = inference_registry(default_config().inference)
    assert len(passes) == 5


def test_registry_respects_disabled() -> None:
    config = InferenceConfig(
        enabled=frozenset(kind for kind in InferenceKind if kind != InferenceKind.STATES)
    )
    passes = inference_registry(config)
    assert all(inference_pass.name != "states" for inference_pass in passes)
    assert len(passes) == 4


def test_run_inference_empty_graph() -> None:
    graph = EvidenceGraph()
    result = run_inference(
        graph,
        ProviderInput(),
        inference_registry(default_config().inference),
        thresholds=default_config().confidence,
    )
    assert result == InferenceResult()


def test_run_inference_merges_pass_outputs() -> None:
    graph = EvidenceGraph()
    result = run_inference(
        graph,
        ProviderInput(),
        (EntityInferencePass(),),
        thresholds=default_config().confidence,
    )
    assert result.entities == ()
