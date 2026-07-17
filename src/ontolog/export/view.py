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


def _filter_entities(
    entities: tuple[Entity, ...],
    *,
    include_ineligible: bool,
) -> tuple[Entity, ...]:
    if include_ineligible:
        return entities
    return tuple(entity for entity in entities if entity.export_eligible)


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
        entities=_filter_entities(model.entities, include_ineligible=include_ineligible),
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
