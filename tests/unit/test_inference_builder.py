"""Tests for build_inference_result."""

from __future__ import annotations

from pathlib import Path

from helpers import extract_fixture_to_store
from ontolog.config import InferenceConfig, InferenceKind, default_config
from ontolog.evidence.graph import EvidenceGraph
from ontolog.inference.builder import (
    build_inference_context_from_store,
    build_inference_result,
    build_inference_result_from_store,
)
from ontolog.storage import SqliteTemplateStore


def test_build_inference_result_runs_pipeline(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    extract_fixture_to_store("controlboard.log", store_path)
    result = build_inference_result(store_path, config=default_config())
    assert result.entities
    assert result.events
    assert result.fields


def test_build_inference_result_respects_config(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    extract_fixture_to_store("controlboard.log", store_path)
    config = default_config().model_copy(
        update={
            "inference": InferenceConfig(enabled=frozenset({InferenceKind.ENTITIES})),
        }
    )
    result = build_inference_result(store_path, config=config)
    assert result.entities
    assert result.events == ()
    assert result.fields == ()


def test_build_inference_context_from_store_returns_graph(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    extract_fixture_to_store("controlboard.log", store_path)
    with SqliteTemplateStore(store_path) as store:
        context = build_inference_context_from_store(store, config=default_config())
    assert isinstance(context.graph, EvidenceGraph)
    assert context.graph.node_count() > 0
    assert context.result.entities


def test_build_inference_result_from_store_matches_context_result(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    extract_fixture_to_store("controlboard.log", store_path)
    with SqliteTemplateStore(store_path) as store:
        context = build_inference_context_from_store(store, config=default_config())
        result = build_inference_result_from_store(store, config=default_config())
    assert result == context.result
