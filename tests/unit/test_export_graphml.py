"""Tests for GraphML export."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from helpers import aggregate_fixture
from ontolog.config import ConfidenceThresholds, OntologConfig
from ontolog.export.formats import ExportFormat
from ontolog.export.registry import export_domain_model

EXPORT_CONFIG = OntologConfig(confidence=ConfidenceThresholds(export=0.6))


def test_graphml_well_formed_xml(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    output = export_domain_model(model, ExportFormat.GRAPHML)
    ET.fromstring(output)


def test_graphml_node_count(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    output = export_domain_model(model, ExportFormat.GRAPHML)
    root = ET.fromstring(output)
    namespace = {"g": "http://graphml.graphdrawing.org/xmlns"}
    nodes = root.findall(".//g:node", namespace)
    assert len(nodes) >= 3


def test_graphml_edges_from_relationships(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    output = export_domain_model(model, ExportFormat.GRAPHML)
    assert "entity:Controlboard" in output
    assert "entity:Interface" in output


def test_graphml_has_field_edges(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    output = export_domain_model(model, ExportFormat.GRAPHML)
    assert 'source="entity:Interface"' in output
    assert 'target="field:destination"' in output
    assert "has_field" in output
