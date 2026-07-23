"""Generate Mermaid diagrams from a domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
from ontolog.export.renderer import Renderer
from ontolog.export.templating import Jinja2Renderer
from ontolog.export.type_map import python_type_for
from ontolog.export.view import ExportView, export_view
from ontolog.models.domain import Field, ProbabilisticDomainModel, Relationship, StateMachine

if TYPE_CHECKING:
    from collections.abc import Mapping

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
    return f"{source} {cardinality} {target} : {relationship.kind}"


def _entity_field_lines(entity_slug: str, fields: tuple[Field, ...]) -> list[str]:
    """Return Mermaid ER attribute lines for ``entity_slug``."""
    lines: list[str] = []
    for domain_field in fields:
        if domain_field.entity_slug != entity_slug:
            continue
        type_name = python_type_for(domain_field.type_name.value)
        lines.append(f"{type_name} {domain_field.name}")
    return lines


def _er_context(view: ExportView) -> dict[str, object] | None:
    if not view.entities and not view.relationships:
        return None
    entities: list[dict[str, object]] = []
    for entity in view.entities:
        field_lines = _entity_field_lines(entity.slug, view.fields)
        entities.append(
            {
                "id": _mermaid_id(entity.name),
                "field_lines": field_lines or ["string name"],
            },
        )
    relationships = [
        {"line": _relationship_line(relationship)} for relationship in view.relationships
    ]
    return {"entities": entities, "relationships": relationships}


def _state_machine_context(machine: StateMachine) -> dict[str, object]:
    transitions: list[dict[str, str]] = []
    for transition in machine.transitions:
        label = f"{transition.count}" if transition.count > 1 else ""
        if label:
            line = f"{transition.from_state} --> {transition.to_state} : {label}"
        else:
            line = f"{transition.from_state} --> {transition.to_state}"
        transitions.append({"line": line})
    return {"transitions": transitions}


def _render_context(view: ExportView) -> Mapping[str, object]:
    return {
        "er_diagram": _er_context(view),
        "state_machines": [_state_machine_context(machine) for machine in view.state_machines],
    }


@dataclass(frozen=True)
class MermaidExporter:
    """Export a domain model as Mermaid diagram source."""

    format_name: ExportFormat = ExportFormat.MERMAID
    renderer: Renderer[Mapping[str, object]] = field(
        default_factory=lambda: Jinja2Renderer("mermaid.mmd.j2"),
    )

    def export(
        self,
        model: ProbabilisticDomainModel,
        *,
        options: ExportOptions,
    ) -> str:
        """Return Mermaid diagram source for ``model``."""
        view = export_view(model, options)
        output = self.renderer.render(_render_context(view))
        return output.rstrip() + "\n" if output.strip() else ""
