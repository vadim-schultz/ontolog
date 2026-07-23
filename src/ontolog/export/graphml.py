"""Generate GraphML from a domain model."""

from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx

from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
from ontolog.export.renderer import GraphmlRenderer, Renderer
from ontolog.export.view import ExportView, export_view
from ontolog.models.domain import ProbabilisticDomainModel, Relationship


def _node_id(kind: str, name: str) -> str:
    return f"{kind}:{name}"


def _build_export_graph(view: ExportView) -> nx.DiGraph:
    graph = nx.DiGraph()
    for entity in view.entities:
        node = _node_id("entity", entity.name)
        graph.add_node(node, kind="entity", label=entity.name, confidence=entity.confidence)
    for event in view.events:
        node = _node_id("event", event.name)
        graph.add_node(node, kind="event", label=event.name, confidence=event.confidence)
    for domain_field in view.fields:
        node = _node_id("field", domain_field.name)
        graph.add_node(
            node,
            kind="field",
            label=domain_field.name,
            type_name=domain_field.type_name.value,
            confidence=domain_field.type_name.confidence,
        )
    for relationship in view.relationships:
        _add_relationship_edge(graph, relationship)
    return graph


def _add_relationship_edge(graph: nx.DiGraph, relationship: Relationship) -> None:
    source = _node_id("entity", relationship.source_name)
    target = _node_id("entity", relationship.target_name)
    if source not in graph:
        graph.add_node(source, kind="entity", label=relationship.source_name)
    if target not in graph:
        graph.add_node(target, kind="entity", label=relationship.target_name)
    graph.add_edge(
        source,
        target,
        kind=relationship.kind,
        confidence=relationship.confidence,
    )


@dataclass(frozen=True)
class GraphMlExporter:
    """Export a domain model as GraphML."""

    format_name: ExportFormat = ExportFormat.GRAPHML
    renderer: Renderer[nx.DiGraph] = field(default_factory=GraphmlRenderer)

    def export(
        self,
        model: ProbabilisticDomainModel,
        *,
        options: ExportOptions,
    ) -> str:
        """Return GraphML XML for ``model``."""
        view = export_view(model, options)
        graph = _build_export_graph(view)
        return self.renderer.render(graph)
