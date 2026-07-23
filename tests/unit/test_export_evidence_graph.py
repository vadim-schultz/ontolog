"""Tests for evidence-graph export."""

from __future__ import annotations

from pathlib import Path

import pytest

from helpers import extract_fixture_to_store
from ontolog.config import default_config
from ontolog.errors import ExportError
from ontolog.evidence.graph import EvidenceGraph
from ontolog.export.formats import ExportFormat
from ontolog.export.registry import export_with_graph, exporter_for
from ontolog.inference.builder import build_domain_model_with_graph_from_store
from ontolog.storage import SqliteTemplateStore


def test_evidence_graph_export_round_trips(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    extract_fixture_to_store("controlboard.log", store_path)
    with SqliteTemplateStore(store_path) as store:
        model, context = build_domain_model_with_graph_from_store(store, config=default_config())
    artifact = export_with_graph(
        model,
        context.graph,
        context.data,
        ExportFormat.EVIDENCE_GRAPH,
    )
    restored = EvidenceGraph.from_json(artifact)
    assert restored.node_count() == context.graph.node_count()
    assert restored.edge_count() == context.graph.edge_count()
    assert restored.node_count() > 0


def test_exporter_for_evidence_graph_raises() -> None:
    with pytest.raises(ExportError, match="graph-aware export"):
        exporter_for(ExportFormat.EVIDENCE_GRAPH)
