"""Generate Mermaid diagrams from a domain model."""

from __future__ import annotations

from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
from ontolog.export.type_map import python_type_for
from ontolog.export.view import export_view
from ontolog.models.domain import (
    Field,
    ProbabilisticDomainModel,
    Relationship,
    StateMachine,
)

_RELATIONSHIP_CARDINALITY: dict[str, str] = {
    "owns": "||--o{",
}


def _mermaid_id(name: str) -> str:
    sanitized = "".join(char if char.isalnum() else "_" for char in name)
    return sanitized.strip("_") or "node"


def _relationship_line(relationship: Relationship) -> str:
    cardinality = _RELATIONSHIP_CARDINALITY.get(relationship.kind, "}o--o{")
    source = _mermaid_id(relationship.source_name)
    target = _mermaid_id(relationship.target_name)
    return f"    {source} {cardinality} {target} : {relationship.kind}"


def _entity_field_lines(entity_slug: str, fields: tuple[Field, ...]) -> list[str]:
    """Return Mermaid ER attribute lines for ``entity_slug``."""
    lines: list[str] = []
    for field in fields:
        if field.entity_slug != entity_slug:
            continue
        type_name = python_type_for(field.type_name.value)
        lines.append(f"        {type_name} {field.name}")
    return lines


def _er_section(model: ProbabilisticDomainModel, options: ExportOptions) -> str:
    view = export_view(model, options)
    if not view.entities and not view.relationships:
        return ""
    lines = ["erDiagram"]
    for entity in view.entities:
        lines.append(f"    {_mermaid_id(entity.name)} {{")
        field_lines = _entity_field_lines(entity.slug, view.fields)
        if field_lines:
            lines.extend(field_lines)
        else:
            lines.append("        string name")
        lines.append("    }")
    for relationship in view.relationships:
        lines.append(_relationship_line(relationship))
    return "\n".join(lines)


def _state_section(machine: StateMachine) -> str:
    lines = ["stateDiagram-v2"]
    for transition in machine.transitions:
        label = f"{transition.count}" if transition.count > 1 else ""
        if label:
            lines.append(f"    {transition.from_state} --> {transition.to_state} : {label}")
        else:
            lines.append(f"    {transition.from_state} --> {transition.to_state}")
    return "\n".join(lines)


def _build_mermaid(model: ProbabilisticDomainModel, options: ExportOptions) -> str:
    sections: list[str] = []
    er = _er_section(model, options)
    if er:
        sections.append(er)
    view = export_view(model, options)
    for machine in view.state_machines:
        sections.append(_state_section(machine))
    return "\n\n".join(sections) + ("\n" if sections else "")


class MermaidExporter:
    """Export a domain model as Mermaid diagram source."""

    @property
    def format_name(self) -> ExportFormat:
        """Return the exporter format identifier."""
        return ExportFormat.MERMAID

    def export(
        self,
        model: ProbabilisticDomainModel,
        *,
        options: ExportOptions,
    ) -> str:
        """Return Mermaid diagram source for ``model``."""
        return _build_mermaid(model, options)
