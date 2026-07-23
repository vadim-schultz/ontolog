"""Generate JSON Schema from a domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from ontolog.export.formats import ExportFormat
from ontolog.export.layout import EntityLayout, entity_layout
from ontolog.export.options import ExportOptions
from ontolog.export.rendering.formatting import confidence_suffix
from ontolog.export.rendering.renderer import JsonRenderer, Renderer
from ontolog.export.typemapping.type_map import json_schema_for
from ontolog.export.view import ExportView, export_view
from ontolog.models.domain import Entity, Field, ProbabilisticDomainModel
from ontolog.types import JsonValue


def _entity_schema(entity: Entity, layout: EntityLayout) -> dict[str, JsonValue]:
    """Return a nested JSON Schema object for ``entity``."""
    properties: dict[str, JsonValue] = {}
    for domain_field in layout.fields_for(entity.slug):
        properties[domain_field.name] = _field_property(domain_field)
    for child_slug in layout.children_by_slug.get(entity.slug, ()):
        child = layout.slug_to_entity.get(child_slug)
        if child is None:
            continue
        properties[_child_property_name(child)] = _entity_schema(child, layout)
    return {
        "type": "object",
        "description": f"Inferred entity {confidence_suffix(entity.confidence)}",
        "properties": properties,
        "additionalProperties": False,
    }


def _child_property_name(entity: Entity) -> str:
    """Return the JSON property name for a nested child entity."""
    return entity.slug


def _field_property(field: Field) -> dict[str, JsonValue]:
    schema = json_schema_for(field.type_name.value)
    schema["description"] = (
        f"Inferred field type {field.type_name.value} "
        f"{confidence_suffix(field.type_name.confidence)}"
    )
    return cast("dict[str, JsonValue]", schema)


def _build_schema(view: ExportView) -> dict[str, JsonValue]:
    layout = entity_layout(view)
    properties: dict[str, JsonValue] = {}
    for root_slug in layout.root_slugs:
        entity = layout.slug_to_entity.get(root_slug)
        if entity is None:
            continue
        properties[entity.name] = _entity_schema(entity, layout)
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
