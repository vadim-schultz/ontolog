"""Generate human-readable Markdown reports from a domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ontolog.export.formats import ExportFormat
from ontolog.export.layout import EntityLayout, entity_layout
from ontolog.export.options import ExportOptions
from ontolog.export.rendering.renderer import Renderer
from ontolog.export.rendering.templating import Jinja2Renderer
from ontolog.export.view import ExportView, export_view
from ontolog.models.domain import (
    Entity,
    Event,
    Field,
    ProbabilisticDomainModel,
    Relationship,
    StateMachine,
)
from ontolog.models.evidence import Evidence

if TYPE_CHECKING:
    from collections.abc import Mapping


def _provenance_lines(evidence: tuple[Evidence, ...]) -> list[str]:
    return [f"- `{item.source}` ({item.score:.2f}): {item.explanation}" for item in evidence]


def _event_context(event: Event, *, include_provenance: bool) -> dict[str, object]:
    verbs = ", ".join(sorted(event.verbs)) if event.verbs else "none"
    return {
        "name": event.name,
        "confidence": event.confidence,
        "verbs": verbs,
        "provenance": _provenance_lines(event.evidence) if include_provenance else [],
    }


def _field_context(field: Field, *, include_provenance: bool) -> dict[str, object]:
    claim = field.type_name
    return {
        "name": field.name,
        "entity_slug": field.entity_slug,
        "type_value": claim.value,
        "type_confidence": claim.confidence,
        "alternatives": [
            {"value": alternative.value, "confidence": alternative.confidence}
            for alternative in claim.alternatives
        ],
        "provenance": _provenance_lines(claim.evidence) if include_provenance else [],
    }


def _entity_tree_context(
    entity: Entity,
    layout: EntityLayout,
    *,
    include_provenance: bool,
) -> dict[str, object]:
    """Return a nested entity context including owned fields and children."""
    children = [
        _entity_tree_context(child, layout, include_provenance=include_provenance)
        for child_slug in layout.children_by_slug.get(entity.slug, ())
        if (child := layout.slug_to_entity.get(child_slug)) is not None
    ]
    return {
        "name": entity.name,
        "confidence": entity.confidence,
        "fields": [
            _field_context(field, include_provenance=include_provenance)
            for field in layout.fields_for(entity.slug)
        ],
        "children": children,
        "provenance": _provenance_lines(entity.evidence) if include_provenance else [],
    }


def _relationship_context(
    relationship: Relationship,
    *,
    include_provenance: bool,
) -> dict[str, object]:
    return {
        "source_name": relationship.source_name,
        "target_name": relationship.target_name,
        "kind": relationship.kind,
        "confidence": relationship.confidence,
        "provenance": _provenance_lines(relationship.evidence) if include_provenance else [],
    }


def _state_machine_context(
    machine: StateMachine,
    *,
    include_provenance: bool,
) -> dict[str, object]:
    return {
        "name": machine.name,
        "confidence": machine.confidence,
        "states": ", ".join(machine.states),
        "provenance": _provenance_lines(machine.evidence) if include_provenance else [],
    }


def _entity_trees_context(
    layout: EntityLayout,
    *,
    include_provenance: bool,
) -> list[dict[str, object]]:
    """Return nested entity tree contexts for root entities."""
    return [
        _entity_tree_context(
            layout.slug_to_entity[root_slug],
            layout,
            include_provenance=include_provenance,
        )
        for root_slug in layout.root_slugs
        if root_slug in layout.slug_to_entity
    ]


def _events_context(
    view: ExportView,
    *,
    include_provenance: bool,
) -> list[dict[str, object]]:
    """Return event contexts for the report."""
    return [_event_context(event, include_provenance=include_provenance) for event in view.events]


def _unscoped_fields_context(
    view: ExportView,
    *,
    include_provenance: bool,
) -> list[dict[str, object]]:
    """Return field contexts for fields without entity scope."""
    return [
        _field_context(field, include_provenance=include_provenance)
        for field in view.fields
        if field.entity_slug is None
    ]


def _relationships_context(
    view: ExportView,
    *,
    include_provenance: bool,
) -> list[dict[str, object]]:
    """Return relationship contexts for the report."""
    return [
        _relationship_context(relationship, include_provenance=include_provenance)
        for relationship in view.relationships
    ]


def _state_machines_context(
    view: ExportView,
    *,
    include_provenance: bool,
) -> list[dict[str, object]]:
    """Return state machine contexts for the report."""
    return [
        _state_machine_context(machine, include_provenance=include_provenance)
        for machine in view.state_machines
    ]


def _render_context(view: ExportView, options: ExportOptions) -> Mapping[str, object]:
    include_provenance = options.include_provenance
    layout = entity_layout(view)
    return {
        "include_provenance": include_provenance,
        "entity_trees": _entity_trees_context(layout, include_provenance=include_provenance),
        "events": _events_context(view, include_provenance=include_provenance),
        "unscoped_fields": _unscoped_fields_context(view, include_provenance=include_provenance),
        "relationships": _relationships_context(view, include_provenance=include_provenance),
        "state_machines": _state_machines_context(view, include_provenance=include_provenance),
    }


@dataclass(frozen=True)
class MarkdownReportExporter:
    """Export a domain model as a Markdown report."""

    format_name: ExportFormat = ExportFormat.MARKDOWN
    renderer: Renderer[Mapping[str, object]] = field(
        default_factory=lambda: Jinja2Renderer("markdown_report.md.j2"),
    )

    def export(
        self,
        model: ProbabilisticDomainModel,
        *,
        options: ExportOptions,
    ) -> str:
        """Return a Markdown report for ``model``."""
        view = export_view(model, options)
        report = self.renderer.render(_render_context(view, options))
        return report.rstrip() + "\n"
