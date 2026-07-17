"""Generate human-readable Markdown reports from a domain model."""

from __future__ import annotations

from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
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


def _confidence_pct(value: float) -> str:
    return f"{value * 100:.0f}%"


def _provenance_lines(evidence: tuple[Evidence, ...]) -> list[str]:
    return [f"- `{item.source}` ({item.score:.2f}): {item.explanation}" for item in evidence]


def _section_entities(entities: tuple[Entity, ...], *, include_provenance: bool) -> str:
    if not entities:
        return ""
    lines = ["# Entities", ""]
    for entity in entities:
        lines.append(f"- **{entity.name}** — confidence {_confidence_pct(entity.confidence)}")
        if include_provenance and entity.evidence:
            lines.extend(_provenance_lines(entity.evidence))
    lines.append("")
    return "\n".join(lines)


def _section_events(events: tuple[Event, ...], *, include_provenance: bool) -> str:
    if not events:
        return ""
    lines = ["# Events", ""]
    for event in events:
        verbs = ", ".join(sorted(event.verbs)) if event.verbs else "none"
        lines.append(
            f"- **{event.name}** — confidence {_confidence_pct(event.confidence)}; verbs: {verbs}",
        )
        if include_provenance and event.evidence:
            lines.extend(_provenance_lines(event.evidence))
    lines.append("")
    return "\n".join(lines)


def _section_fields(fields: tuple[Field, ...], *, include_provenance: bool) -> str:
    if not fields:
        return ""
    lines = ["# Fields", ""]
    for field in fields:
        claim = field.type_name
        lines.append(
            f"- **{field.name}** → `{claim.value}` "
            f"(confidence {_confidence_pct(claim.confidence)})",
        )
        for alternative in claim.alternatives:
            lines.append(
                f"  - alternative `{alternative.value}` "
                f"({_confidence_pct(alternative.confidence)})",
            )
        if include_provenance and claim.evidence:
            lines.extend(_provenance_lines(claim.evidence))
    lines.append("")
    return "\n".join(lines)


def _section_relationships(
    relationships: tuple[Relationship, ...],
    *,
    include_provenance: bool,
) -> str:
    if not relationships:
        return ""
    lines = ["# Relationships", ""]
    for relationship in relationships:
        lines.append(
            f"- **{relationship.source_name}** "
            f"{relationship.kind} **{relationship.target_name}** "
            f"— confidence {_confidence_pct(relationship.confidence)}",
        )
        if include_provenance and relationship.evidence:
            lines.extend(_provenance_lines(relationship.evidence))
    lines.append("")
    return "\n".join(lines)


def _section_state_machines(
    state_machines: tuple[StateMachine, ...],
    *,
    include_provenance: bool,
) -> str:
    if not state_machines:
        return ""
    lines = ["# State machines", ""]
    for machine in state_machines:
        lines.append(
            f"- **{machine.name}** — confidence {_confidence_pct(machine.confidence)}",
        )
        states = ", ".join(machine.states)
        lines.append(f"  - states: {states}")
        if include_provenance and machine.evidence:
            lines.extend(_provenance_lines(machine.evidence))
    lines.append("")
    return "\n".join(lines)


def _build_report(view: ExportView, options: ExportOptions) -> str:
    sections = [
        _section_entities(view.entities, include_provenance=options.include_provenance),
        _section_events(view.events, include_provenance=options.include_provenance),
        _section_fields(view.fields, include_provenance=options.include_provenance),
        _section_relationships(
            view.relationships,
            include_provenance=options.include_provenance,
        ),
        _section_state_machines(
            view.state_machines,
            include_provenance=options.include_provenance,
        ),
    ]
    return "\n".join(section for section in sections if section).rstrip() + "\n"


class MarkdownReportExporter:
    """Export a domain model as a Markdown report."""

    @property
    def format_name(self) -> ExportFormat:
        """Return the exporter format identifier."""
        return ExportFormat.MARKDOWN

    def export(
        self,
        model: ProbabilisticDomainModel,
        *,
        options: ExportOptions,
    ) -> str:
        """Return a Markdown report for ``model``."""
        view = export_view(model, options)
        return _build_report(view, options)
