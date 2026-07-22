"""Generate Pydantic model source from a domain model."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ontolog.export.enum_codegen import enum_class_name, enum_class_source
from ontolog.export.enum_slug import is_enum_type_slug
from ontolog.export.formats import ExportFormat
from ontolog.export.identifiers import is_valid_field_name, to_python_identifier
from ontolog.export.options import ExportOptions
from ontolog.export.type_map import (
    pydantic_names_for,
    python_field_type,
    python_imports_for,
    type_description_for,
)
from ontolog.export.view import ExportView, export_view
from ontolog.models.domain import Entity, Field, ProbabilisticDomainModel, Relationship

_MAX_FIELD_LINE_LENGTH = 100


@dataclass(frozen=True)
class _PydanticLayout:
    """Prepared entity, field, and relationship groupings for code generation."""

    entities: tuple[Entity, ...]
    fields: tuple[Field, ...]
    fields_by_slug: dict[str | None, tuple[Field, ...]]
    owns_map: dict[str, list[tuple[str, Relationship]]]
    slug_to_entity: dict[str, Entity]
    enum_names: dict[str, str]


def _class_name(entity: Entity) -> str:
    return entity.name.replace(" ", "")


def field_description(field: Field) -> str:
    """Return a Pydantic field description including type and confidence."""
    base = type_description_for(field.type_name.value)
    return f"{base} (confidence={field.type_name.confidence:.2f})"


def _exportable_fields(fields: tuple[Field, ...]) -> tuple[Field, ...]:
    return tuple(field for field in fields if is_valid_field_name(field.name))


def _group_fields_by_entity(fields: tuple[Field, ...]) -> dict[str | None, tuple[Field, ...]]:
    groups: dict[str | None, list[Field]] = {}
    for field in _exportable_fields(fields):
        groups.setdefault(field.entity_slug, []).append(field)
    return {key: tuple(items) for key, items in groups.items()}


def _owns_children(
    relationships: tuple[Relationship, ...],
    entities: tuple[Entity, ...],
) -> dict[str, list[tuple[str, Relationship]]]:
    name_to_slug = {entity.name: entity.slug for entity in entities}
    children: dict[str, dict[str, Relationship]] = defaultdict(dict)
    for relationship in relationships:
        if relationship.kind != "owns":
            continue
        parent_slug = name_to_slug.get(relationship.source_name)
        child_slug = name_to_slug.get(relationship.target_name)
        if parent_slug is None or child_slug is None:
            continue
        existing = children[parent_slug].get(child_slug)
        if existing is None or relationship.confidence > existing.confidence:
            children[parent_slug][child_slug] = relationship
    return {parent_slug: list(child_map.items()) for parent_slug, child_map in children.items()}


def _relocate_owned_fields(
    fields_by_slug: dict[str | None, tuple[Field, ...]],
    owns_map: dict[str, list[tuple[str, Relationship]]],
) -> dict[str | None, tuple[Field, ...]]:
    relocated: dict[str | None, list[Field]] = {
        slug: list(fields) for slug, fields in fields_by_slug.items()
    }
    for parent_slug, child_entries in owns_map.items():
        parent_fields = relocated.pop(parent_slug, [])
        if not parent_fields:
            continue
        for child_slug, _relationship in child_entries:
            relocated.setdefault(child_slug, []).extend(parent_fields)
    return {slug: tuple(fields) for slug, fields in relocated.items()}


def _entity_emit_order(
    entities: tuple[Entity, ...],
    owns_map: dict[str, list[tuple[str, Relationship]]],
) -> tuple[Entity, ...]:
    slug_to_entity = {entity.slug: entity for entity in entities}
    ordered: list[Entity] = []
    seen: set[str] = set()

    def visit(slug: str) -> None:
        if slug in seen:
            return
        seen.add(slug)
        for child_slug, _relationship in owns_map.get(slug, []):
            visit(child_slug)
        entity = slug_to_entity.get(slug)
        if entity is not None:
            ordered.append(entity)

    for entity in entities:
        visit(entity.slug)
    return tuple(ordered)


def _format_field_line(field_name: str, annotation: str, field_args: list[str]) -> str:
    """Return a field assignment, wrapping ``Field`` when it exceeds Ruff line length."""
    prefix = f"    {field_name}: {annotation} = Field("
    single_line = f"{prefix}{', '.join(field_args)})"
    if len(single_line) <= _MAX_FIELD_LINE_LENGTH:
        return single_line
    indented_args = ",\n        ".join(field_args)
    return f"{prefix}\n        {indented_args},\n    )"


def _field_line(field: Field, *, enum_names: dict[str, str]) -> str:
    field_name = to_python_identifier(field.name)
    if field_name is None:
        return ""
    type_slug = field.type_name.value
    if is_enum_type_slug(type_slug):
        annotation = enum_names[type_slug]
    else:
        annotation = python_field_type(type_slug).annotation
    field_args = [f"description={field_description(field)!r}"]
    mapping = python_field_type(type_slug)
    if mapping.field_pattern is not None:
        field_args.append(f"pattern={mapping.field_pattern!r}")
    return _format_field_line(field_name, annotation, field_args)


def _relationship_field_line(child: Entity, relationship: Relationship) -> str:
    field_name = to_python_identifier(child.slug)
    if field_name is None:
        return ""
    description = f"owns {child.name} (confidence={relationship.confidence:.2f})"
    return f"    {field_name}: {_class_name(child)} = Field(description={description!r})"


def _entity_class(
    entity: Entity,
    fields: tuple[Field, ...],
    composition: tuple[tuple[Entity, Relationship], ...],
    *,
    enum_names: dict[str, str],
) -> str:
    body_lines = [
        line for line in (_field_line(field, enum_names=enum_names) for field in fields) if line
    ]
    body_lines.extend(
        line
        for line in (_relationship_field_line(child, rel) for child, rel in composition)
        if line
    )
    lines = [
        f"class {_class_name(entity)}(BaseModel):",
        f'    """Inferred entity (confidence={entity.confidence:.2f})."""',
        "",
        "    model_config = ConfigDict(frozen=True)",
    ]
    if body_lines:
        lines.append("")
        lines.extend(body_lines)
    return "\n".join(lines)


def _unscoped_fields_class(
    fields: tuple[Field, ...],
    *,
    enum_names: dict[str, str],
) -> str:
    exportable = _exportable_fields(fields)
    if not exportable:
        return ""
    body = "\n".join(
        line for line in (_field_line(field, enum_names=enum_names) for field in exportable) if line
    )
    return (
        "class UnscopedFields(BaseModel):\n"
        '    """Inferred log fields without entity scope."""\n'
        "\n"
        "    model_config = ConfigDict(frozen=True)\n"
        f"{body}\n"
    )


def _enum_names_for_entity(entity: Entity, fields: tuple[Field, ...]) -> dict[str, str]:
    """Map enum type slugs to generated class names for ``entity``."""
    names: dict[str, str] = {}
    class_name = enum_class_name(entity.name)
    for field in fields:
        type_slug = field.type_name.value
        if is_enum_type_slug(type_slug):
            names[type_slug] = class_name
    return names


def _collect_enum_classes(
    entities: tuple[Entity, ...],
    fields_by_slug: dict[str | None, tuple[Field, ...]],
) -> dict[str, str]:
    """Return enum type slug to class name mappings across entities."""
    enum_names: dict[str, str] = {}
    for entity in entities:
        enum_names.update(
            _enum_names_for_entity(entity, fields_by_slug.get(entity.slug, ())),
        )
    return enum_names


def _enum_class_blocks(enum_names: dict[str, str]) -> list[str]:
    """Return generated StrEnum class source blocks."""
    return [
        enum_class_source(class_name, type_slug) for type_slug, class_name in enum_names.items()
    ]


def _pydantic_layout(view: ExportView) -> _PydanticLayout:
    """Group export view data for Pydantic source generation."""
    owns_map = _owns_children(view.relationships, view.entities)
    fields_by_slug = _relocate_owned_fields(
        _group_fields_by_entity(view.fields),
        owns_map,
    )
    return _PydanticLayout(
        entities=view.entities,
        fields=view.fields,
        fields_by_slug=fields_by_slug,
        owns_map=owns_map,
        slug_to_entity={entity.slug: entity for entity in view.entities},
        enum_names=_collect_enum_classes(view.entities, fields_by_slug),
    )


def _non_enum_type_slugs(fields: tuple[Field, ...]) -> set[str]:
    """Return mapped type slugs that are not generated as StrEnums."""
    return {
        field.type_name.value
        for field in _exportable_fields(fields)
        if not is_enum_type_slug(field.type_name.value)
    }


def _stdlib_import_lines(type_slugs: set[str], *, has_enums: bool) -> list[str]:
    """Return sorted stdlib import lines required by ``type_slugs``."""
    imports = list(python_imports_for(type_slugs))
    if has_enums:
        imports.append("from enum import StrEnum")
    return imports


def _pydantic_import_names(type_slugs: set[str]) -> tuple[str, ...]:
    """Return sorted Pydantic symbols to import for ``type_slugs``."""
    extras = pydantic_names_for(type_slugs)
    return tuple(sorted({"BaseModel", "ConfigDict", "Field", *extras}))


def _header_lines(fields: tuple[Field, ...], enum_names: dict[str, str]) -> list[str]:
    """Return module docstring and import lines."""
    type_slugs = _non_enum_type_slugs(fields)
    stdlib_imports = _stdlib_import_lines(type_slugs, has_enums=bool(enum_names))
    pydantic_imports = _pydantic_import_names(type_slugs)
    lines = ['"""Generated by ontolog — do not edit."""', ""]
    if stdlib_imports:
        lines.extend(stdlib_imports)
        lines.append("")
    lines.extend([f"from pydantic import {', '.join(pydantic_imports)}", "", ""])
    return lines


def _enum_section_lines(enum_names: dict[str, str]) -> list[str]:
    """Return generated StrEnum class blocks."""
    lines: list[str] = []
    for block in _enum_class_blocks(enum_names):
        lines.append(block)
        lines.append("")
    return lines


def _composition_fields(
    entity_slug: str,
    layout: _PydanticLayout,
) -> tuple[tuple[Entity, Relationship], ...]:
    """Return owned child entities as composition fields for ``entity_slug``."""
    child_entries = layout.owns_map.get(entity_slug, ())
    return tuple(
        (layout.slug_to_entity[child_slug], relationship)
        for child_slug, relationship in child_entries
        if child_slug in layout.slug_to_entity
    )


def _entity_section_lines(layout: _PydanticLayout) -> list[str]:
    """Return generated entity model class blocks."""
    lines: list[str] = []
    for entity in _entity_emit_order(layout.entities, layout.owns_map):
        entity_fields = layout.fields_by_slug.get(entity.slug, ())
        composition = _composition_fields(entity.slug, layout)
        lines.append(
            _entity_class(entity, entity_fields, composition, enum_names=layout.enum_names),
        )
        lines.append("")
    return lines


def _unscoped_section_lines(layout: _PydanticLayout) -> list[str]:
    """Return an unscoped fields class when needed."""
    unscoped = _unscoped_fields_class(
        layout.fields_by_slug.get(None, ()),
        enum_names=layout.enum_names,
    )
    return [unscoped] if unscoped else []


def _build_source(model: ProbabilisticDomainModel, options: ExportOptions) -> str:
    layout = _pydantic_layout(export_view(model, options))
    lines = [
        *_header_lines(layout.fields, layout.enum_names),
        *_enum_section_lines(layout.enum_names),
        *_entity_section_lines(layout),
        *_unscoped_section_lines(layout),
    ]
    return "\n".join(lines).rstrip() + "\n"


class PydanticGenExporter:
    """Export a domain model as generated Pydantic source code."""

    @property
    def format_name(self) -> ExportFormat:
        """Return the exporter format identifier."""
        return ExportFormat.PYDANTIC

    def export(
        self,
        model: ProbabilisticDomainModel,
        *,
        options: ExportOptions,
    ) -> str:
        """Return importable Python source for ``model``."""
        return _build_source(model, options)
