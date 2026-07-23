"""Shared entity hierarchy layout for exporters."""

from __future__ import annotations

from dataclasses import dataclass

from ontolog.export.view import ExportView
from ontolog.models.domain import Entity, Field, Relationship


@dataclass(frozen=True)
class EntityLayout:
    """Entity hierarchy with fields grouped by owning entity slug."""

    entities: tuple[Entity, ...]
    fields_by_slug: dict[str, tuple[Field, ...]]
    children_by_slug: dict[str, tuple[str, ...]]
    root_slugs: tuple[str, ...]
    slug_to_entity: dict[str, Entity]

    def fields_for(self, entity_slug: str) -> tuple[Field, ...]:
        """Return fields owned by ``entity_slug``."""
        return self.fields_by_slug.get(entity_slug, ())


def entity_layout(view: ExportView) -> EntityLayout:
    """Build a hierarchical layout from export view data."""
    slug_to_entity = {entity.slug: entity for entity in view.entities}
    fields_by_slug = _group_fields_by_entity(view.fields)
    children_by_slug = _children_by_parent(view.relationships, slug_to_entity)
    child_slugs = {child for children in children_by_slug.values() for child in children}
    root_slugs = tuple(
        entity.slug for entity in view.entities if entity.slug not in child_slugs
    )
    return EntityLayout(
        entities=view.entities,
        fields_by_slug=fields_by_slug,
        children_by_slug=children_by_slug,
        root_slugs=root_slugs,
        slug_to_entity=slug_to_entity,
    )


def _group_fields_by_entity(fields: tuple[Field, ...]) -> dict[str, tuple[Field, ...]]:
    groups: dict[str, list[Field]] = {}
    for field in fields:
        if field.entity_slug is None:
            continue
        groups.setdefault(field.entity_slug, []).append(field)
    return {slug: tuple(items) for slug, items in groups.items()}


def _children_by_parent(
    relationships: tuple[Relationship, ...],
    slug_to_entity: dict[str, Entity],
) -> dict[str, tuple[str, ...]]:
    children: dict[str, list[str]] = {}
    name_to_slug = {entity.name: entity.slug for entity in slug_to_entity.values()}
    for relationship in relationships:
        if relationship.kind != "owns":
            continue
        parent_slug = name_to_slug.get(relationship.source_name)
        child_slug = name_to_slug.get(relationship.target_name)
        if parent_slug is None or child_slug is None:
            continue
        if child_slug not in children.setdefault(parent_slug, []):
            children[parent_slug].append(child_slug)
    return {parent: tuple(child_list) for parent, child_list in children.items()}
