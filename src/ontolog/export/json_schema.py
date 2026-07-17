"""Generate JSON Schema from a domain model."""

from __future__ import annotations

import json

from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
from ontolog.export.type_map import json_schema_for
from ontolog.export.view import ExportView, export_view
from ontolog.models.domain import Entity, Field, ProbabilisticDomainModel


def _entity_def(entity: Entity) -> dict[str, object]:
    return {
        "type": "object",
        "description": f"Inferred entity (confidence={entity.confidence:.2f})",
        "additionalProperties": False,
    }


def _field_property(field: Field) -> dict[str, object]:
    schema = json_schema_for(field.type_name.value)
    schema["description"] = (
        f"Inferred field type {field.type_name.value} (confidence={field.type_name.confidence:.2f})"
    )
    return schema


def _build_schema(view: ExportView) -> dict[str, object]:
    properties: dict[str, object] = {}
    for entity in view.entities:
        properties[entity.name] = _entity_def(entity)
    for field in view.fields:
        properties[field.name] = _field_property(field)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }


class JsonSchemaExporter:
    """Export a domain model as JSON Schema."""

    @property
    def format_name(self) -> ExportFormat:
        """Return the exporter format identifier."""
        return ExportFormat.JSON_SCHEMA

    def export(
        self,
        model: ProbabilisticDomainModel,
        *,
        options: ExportOptions,
    ) -> str:
        """Serialize ``model`` as JSON Schema."""
        view = export_view(model, options)
        return json.dumps(_build_schema(view), indent=2)
