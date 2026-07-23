"""Filter domain models for export."""

from __future__ import annotations

from dataclasses import dataclass

from ontolog.export.options import ExportOptions
from ontolog.models.domain import (
    Entity,
    Event,
    Field,
    ProbabilisticDomainModel,
    Relationship,
    StateMachine,
)


@dataclass(frozen=True)
class ExportView:
    """Filtered collections ready for export."""

    entities: tuple[Entity, ...]
    events: tuple[Event, ...]
    fields: tuple[Field, ...]
    relationships: tuple[Relationship, ...]
    state_machines: tuple[StateMachine, ...]


def _slugs_eligible_via_relationships(
    relationships: tuple[Relationship, ...],
    eligible_slugs: set[str],
    name_to_slug: dict[str, str],
) -> None:
    """Promote parent entity slugs when an eligible child is owned."""
    for relationship in relationships:
        if relationship.kind != "owns" or not relationship.export_eligible:
            continue
        parent_slug = name_to_slug.get(relationship.source_name)
        child_slug = name_to_slug.get(relationship.target_name)
        if child_slug in eligible_slugs and parent_slug is not None:
            eligible_slugs.add(parent_slug)


def _slugs_eligible_via_fields(
    fields: tuple[Field, ...],
    eligible_slugs: set[str],
) -> None:
    """Promote entity slugs that own eligible fields."""
    for field in fields:
        if field.type_name.export_eligible and field.entity_slug is not None:
            eligible_slugs.add(field.entity_slug)


def _filter_entities(
    entities: tuple[Entity, ...],
    relationships: tuple[Relationship, ...],
    fields: tuple[Field, ...],
    *,
    include_ineligible: bool,
) -> tuple[Entity, ...]:
    if include_ineligible:
        return entities
    eligible_slugs = {entity.slug for entity in entities if entity.export_eligible}
    name_to_slug = {entity.name: entity.slug for entity in entities}
    _slugs_eligible_via_relationships(relationships, eligible_slugs, name_to_slug)
    _slugs_eligible_via_fields(fields, eligible_slugs)
    return tuple(entity for entity in entities if entity.slug in eligible_slugs)


def _filter_events(
    events: tuple[Event, ...],
    *,
    include_ineligible: bool,
) -> tuple[Event, ...]:
    if include_ineligible:
        return events
    return tuple(event for event in events if event.export_eligible)


def _filter_fields(
    fields: tuple[Field, ...],
    *,
    include_ineligible: bool,
) -> tuple[Field, ...]:
    if include_ineligible:
        return fields
    return tuple(field for field in fields if field.type_name.export_eligible)


def _filter_relationships(
    relationships: tuple[Relationship, ...],
    *,
    include_ineligible: bool,
) -> tuple[Relationship, ...]:
    if include_ineligible:
        return relationships
    return tuple(rel for rel in relationships if rel.export_eligible)


def _filter_state_machines(
    state_machines: tuple[StateMachine, ...],
    *,
    include_ineligible: bool,
) -> tuple[StateMachine, ...]:
    if include_ineligible:
        return state_machines
    return tuple(machine for machine in state_machines if machine.export_eligible)


def export_view(
    model: ProbabilisticDomainModel,
    options: ExportOptions,
) -> ExportView:
    """Return export-ready collections from ``model``."""
    include_ineligible = options.include_ineligible
    return ExportView(
        entities=_filter_entities(
            model.entities,
            model.relationships,
            model.fields,
            include_ineligible=include_ineligible,
        ),
        events=_filter_events(model.events, include_ineligible=include_ineligible),
        fields=_filter_fields(model.fields, include_ineligible=include_ineligible),
        relationships=_filter_relationships(
            model.relationships,
            include_ineligible=include_ineligible,
        ),
        state_machines=_filter_state_machines(
            model.state_machines,
            include_ineligible=include_ineligible,
        ),
    )
