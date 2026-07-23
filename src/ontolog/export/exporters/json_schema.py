"""Generate JSON Schema from a domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
from ontolog.export.rendering.formatting import confidence_suffix
from ontolog.export.rendering.renderer import JsonRenderer, Renderer
from ontolog.export.typemapping.type_map import json_schema_for
from ontolog.export.view import ExportView, export_view
from ontolog.models.domain import Entity, Field, ProbabilisticDomainModel
from ontolog.types import JsonValue


def _entity_def(entity: Entity) -> dict[str, JsonValue]:
    return {
        "type": "object",
        "description": f"Inferred entity {confidence_suffix(entity.confidence)}",
        "additionalProperties": False,
    }


def _field_property(field: Field) -> dict[str, JsonValue]:
    schema = json_schema_for(field.type_name.value)
    schema["description"] = (
        f"Inferred field type {field.type_name.value} "
        f"{confidence_suffix(field.type_name.confidence)}"
    )
    return cast("dict[str, JsonValue]", schema)


def _build_schema(view: ExportView) -> dict[str, JsonValue]:
    properties: dict[str, JsonValue] = {}
    for entity in view.entities:
        properties[entity.name] = _entity_def(entity)
    for domain_field in view.fields:
        properties[domain_field.name] = _field_property(domain_field)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }


@dataclass(frozen=True)
class JsonSchemaExporter:
    """Export a domain model as JSON Schema."""

    format_name: ExportFormat = ExportFormat.JSON_SCHEMA
    renderer: Renderer[JsonValue] = field(default_factory=JsonRenderer)

    def export(
        self,
        model: ProbabilisticDomainModel,
        *,
        options: ExportOptions,
    ) -> str:
        """Serialize ``model`` as JSON Schema."""
        view = export_view(model, options)
        return self.renderer.render(_build_schema(view))
