"""Tests for ontolog.evidence.loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from ontolog.errors import StorageError
from ontolog.evidence import load_evidence_graph
from ontolog.models.template import Template
from ontolog.storage import SqliteTemplateStore


def test_load_returns_empty_graph(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    graph = load_evidence_graph(store_path)
    assert graph.node_count() == 0
    assert graph.edge_count() == 0


def test_load_opens_store_at_path(tmp_path: Path) -> None:
    store_path = tmp_path / "nested" / "ontolog.db"
    store_path.parent.mkdir()
    graph = load_evidence_graph(store_path)
    assert graph.node_count() == 0


def test_load_missing_parent_raises_storage_error(tmp_path: Path) -> None:
    store_path = tmp_path / "nested" / "ontolog.db"
    with pytest.raises(StorageError):
        load_evidence_graph(store_path)


def test_load_invalid_path_raises_storage_error(tmp_path: Path) -> None:
    invalid_path = tmp_path / "not-a-database"
    invalid_path.mkdir()
    with pytest.raises(StorageError):
        load_evidence_graph(invalid_path)


def test_load_after_templates_still_empty(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    store = SqliteTemplateStore(store_path)
    try:
        store.upsert_template(Template(id="cluster_1", template="PacketSent destination=<IP>"))
    finally:
        store.close()

    graph = load_evidence_graph(store_path)
    assert graph.node_count() == 0
    assert graph.edge_count() == 0
