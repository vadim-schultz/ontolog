"""Evidence graph backed by NetworkX."""

from __future__ import annotations

import json
from typing import Any

import networkx as nx

from ontolog.errors import InferenceError
from ontolog.models.evidence import Edge, Evidence, Node

_GRAPH_JSON_VERSION = 1
_NODE_DATA_KEY = "data"


def _node_from_attrs(attrs: dict[str, Any]) -> Node:
    return Node.model_validate(attrs[_NODE_DATA_KEY])


def _edge_from_attrs(attrs: dict[str, Any]) -> Edge:
    return Edge.model_validate(attrs[_NODE_DATA_KEY])


class EvidenceGraph:
    """Mutable evidence graph wrapping a NetworkX directed graph."""

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()

    @property
    def nx_graph(self) -> nx.DiGraph:
        """Read-only access to the underlying NetworkX graph."""
        return self._graph

    def add_node(self, node: Node) -> None:
        """Add a node; raise if the id already exists."""
        if self._graph.has_node(node.id):
            msg = f"duplicate node: {node.id}"
            raise InferenceError(msg)
        self._graph.add_node(node.id, **{_NODE_DATA_KEY: node.model_dump(mode="json")})

    def add_edge(self, edge: Edge) -> None:
        """Add an edge; endpoints must exist and the pair must be unique."""
        if not self._graph.has_node(edge.source_id):
            msg = f"missing source node: {edge.source_id}"
            raise InferenceError(msg)
        if not self._graph.has_node(edge.target_id):
            msg = f"missing target node: {edge.target_id}"
            raise InferenceError(msg)
        if self._graph.has_edge(edge.source_id, edge.target_id):
            msg = f"duplicate edge: {edge.source_id} -> {edge.target_id}"
            raise InferenceError(msg)
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            **{_NODE_DATA_KEY: edge.model_dump(mode="json")},
        )

    def get_node(self, node_id: str) -> Node | None:
        if not self._graph.has_node(node_id):
            return None
        return _node_from_attrs(self._graph.nodes[node_id])

    def get_edge(self, source_id: str, target_id: str) -> Edge | None:
        if not self._graph.has_edge(source_id, target_id):
            return None
        return _edge_from_attrs(self._graph.edges[source_id, target_id])

    def nodes(self) -> list[Node]:
        return [_node_from_attrs(self._graph.nodes[node_id]) for node_id in self._graph.nodes]

    def edges(self) -> list[Edge]:
        return [
            _edge_from_attrs(self._graph.edges[source_id, target_id])
            for source_id, target_id in self._graph.edges
        ]

    def node_count(self) -> int:
        return int(self._graph.number_of_nodes())

    def edge_count(self) -> int:
        return int(self._graph.number_of_edges())

    def attach_evidence_to_node(self, node_id: str, evidence: Evidence) -> None:
        """Append evidence to an existing node."""
        node = self.get_node(node_id)
        if node is None:
            msg = f"unknown node: {node_id}"
            raise InferenceError(msg)
        updated = node.model_copy(update={"evidence": (*node.evidence, evidence)})
        self._graph.nodes[node_id][_NODE_DATA_KEY] = updated.model_dump(mode="json")

    def attach_evidence_to_edge(
        self,
        source_id: str,
        target_id: str,
        evidence: Evidence,
    ) -> None:
        """Append evidence to an existing edge."""
        edge = self.get_edge(source_id, target_id)
        if edge is None:
            msg = f"unknown edge: {source_id} -> {target_id}"
            raise InferenceError(msg)
        updated = edge.model_copy(update={"evidence": (*edge.evidence, evidence)})
        self._graph.edges[source_id, target_id][_NODE_DATA_KEY] = updated.model_dump(mode="json")

    def to_json(self, *, indent: int | None = 2) -> str:
        """Serialize the graph to a versioned JSON document."""
        payload = {
            "version": _GRAPH_JSON_VERSION,
            "nodes": [node.model_dump(mode="json") for node in self.nodes()],
            "edges": [edge.model_dump(mode="json") for edge in self.edges()],
        }
        return json.dumps(payload, indent=indent)

    @classmethod
    def from_json(cls, data: str) -> EvidenceGraph:
        """Deserialize a graph from JSON produced by :meth:`to_json`."""
        payload = json.loads(data)
        version = payload.get("version")
        if version != _GRAPH_JSON_VERSION:
            msg = f"unsupported graph JSON version: {version}"
            raise InferenceError(msg)

        graph = cls()
        for node_data in payload["nodes"]:
            graph.add_node(Node.model_validate(node_data))
        for edge_data in payload["edges"]:
            graph.add_edge(Edge.model_validate(edge_data))
        return graph
