"""Generate GraphML from a domain model."""

from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx

from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
from ontolog.export.rendering.renderer import GraphmlRenderer, Renderer
from ontolog.export.view import ExportView, export_view
from ontolog.models.domain import Field, ProbabilisticDomainModel, Relationship


def _node_id(kind: str, name: str) -> str:
    return f"{kind}:{name}"


def _build_export_graph(view: ExportView) -> nx.DiGraph:
    graph = nx.DiGraph()
    slug_to_name = {entity.slug: entity.name for entity in view.entities}
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
        _add_has_field_edge(graph, domain_field, slug_to_name)
    for relationship in view.relationships:
        _add_relationship_edge(graph, relationship)
    return graph


def _add_has_field_edge(
    graph: nx.DiGraph,
    domain_field: Field,
    slug_to_name: dict[str, str],
) -> None:
    """Link a field node to its owning entity when known."""
    if domain_field.entity_slug is None:
        return
    entity_name = slug_to_name.get(domain_field.entity_slug)
    if entity_name is None:
        return
    source = _node_id("entity", entity_name)
    target = _node_id("field", domain_field.name)
    if source not in graph:
        return
    graph.add_edge(source, target, kind="has_field")


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
