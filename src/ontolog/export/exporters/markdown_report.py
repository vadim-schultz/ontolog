"""Generate human-readable Markdown reports from a domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ontolog.export.formats import ExportFormat
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


def _entity_context(entity: Entity, *, include_provenance: bool) -> dict[str, object]:
    return {
        "name": entity.name,
        "confidence": entity.confidence,
        "provenance": _provenance_lines(entity.evidence) if include_provenance else [],
    }


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
        "type_value": claim.value,
        "type_confidence": claim.confidence,
        "alternatives": [
            {"value": alternative.value, "confidence": alternative.confidence}
            for alternative in claim.alternatives
        ],
        "provenance": _provenance_lines(claim.evidence) if include_provenance else [],
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


def _render_context(view: ExportView, options: ExportOptions) -> Mapping[str, object]:
    include_provenance = options.include_provenance
    return {
        "include_provenance": include_provenance,
        "entities": [
            _entity_context(entity, include_provenance=include_provenance)
            for entity in view.entities
        ],
        "events": [
            _event_context(event, include_provenance=include_provenance) for event in view.events
        ],
        "fields": [
            _field_context(field, include_provenance=include_provenance) for field in view.fields
        ],
        "relationships": [
            _relationship_context(relationship, include_provenance=include_provenance)
            for relationship in view.relationships
        ],
        "state_machines": [
            _state_machine_context(machine, include_provenance=include_provenance)
            for machine in view.state_machines
        ],
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
