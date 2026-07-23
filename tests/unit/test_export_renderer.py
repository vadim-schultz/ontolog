"""Tests for export renderers."""

from __future__ import annotations

import json

import networkx as nx

from ontolog.export.renderer import GraphmlRenderer, JsonRenderer


def test_json_renderer_round_trips() -> None:
    output = JsonRenderer().render({"a": 1})
    assert json.loads(output) == {"a": 1}


def test_graphml_renderer_contains_graphml_tag() -> None:
    graph = nx.DiGraph()
    graph.add_node("entity:Example", kind="entity", label="Example")
    output = GraphmlRenderer().render(graph)
    assert "<graphml" in output
