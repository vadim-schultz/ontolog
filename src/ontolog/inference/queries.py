"""Read-only helpers over evidence graphs."""

from __future__ import annotations

from ontolog.evidence.graph import EvidenceGraph
from ontolog.models.evidence import Edge, Evidence, Node, NodeKind


def nodes_by_kind(graph: EvidenceGraph, kind: NodeKind) -> tuple[Node, ...]:
    """Return all nodes of ``kind``."""
    return tuple(node for node in graph.nodes() if node.kind == kind)


def edges_with_label(graph: EvidenceGraph, label: str) -> tuple[Edge, ...]:
    """Return edges whose label matches ``label``."""
    return tuple(edge for edge in graph.edges() if edge.label == label)


def field_type_name(graph: EvidenceGraph, field_node_id: str) -> str | None:
    """Return the type label for ``field_node_id`` via a ``has_type`` edge."""
    for edge in graph.edges():
        if edge.source_id != field_node_id or edge.label != "has_type":
            continue
        type_node = graph.get_node(edge.target_id)
        if type_node is not None:
            return type_node.label
    return None


def entity_fields(graph: EvidenceGraph, entity_node_id: str) -> tuple[str, ...]:
    """Return field node ids linked from ``entity_node_id`` via ``has_field``."""
    field_ids: list[str] = []
    for edge in graph.edges():
        if edge.source_id == entity_node_id and edge.label == "has_field":
            field_ids.append(edge.target_id)
    return tuple(field_ids)


def max_evidence_score(
    item: Node | Edge,
    *,
    source: str | None = None,
) -> float:
    """Return the highest evidence score on ``item``, optionally filtered by ``source``."""
    scores = [
        evidence.score for evidence in item.evidence if source is None or evidence.source == source
    ]
    return max(scores, default=0.0)


def collect_evidence(item: Node | Edge) -> tuple[Evidence, ...]:
    """Return all evidence attached to ``item``."""
    return item.evidence
