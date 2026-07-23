"""Tests for full bundle export."""

from __future__ import annotations

import json
from pathlib import Path

from helpers import extract_fixture_to_store
from ontolog.config import default_config
from ontolog.export.formats import ExportFormat
from ontolog.export.registry import export_with_graph
from ontolog.inference.builder import build_domain_model_with_graph_from_store
from ontolog.storage import SqliteTemplateStore


def test_full_bundle_contains_domain_graph_and_templates(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    extract_fixture_to_store("controlboard.log", store_path)
    with SqliteTemplateStore(store_path) as store:
        model, context = build_domain_model_with_graph_from_store(store, config=default_config())
        data = context.data
        graph = context.graph
    artifact = export_with_graph(model, graph, data, ExportFormat.FULL)
    payload = json.loads(artifact)
    assert payload["schema_version"] == "1"
    assert payload["domain_model"]["entities"]
    assert payload["evidence_graph"]["nodes"]
    assert payload["templates"]
