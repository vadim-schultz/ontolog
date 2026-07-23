"""Order-of-occurrence hierarchy from log templates."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from itertools import pairwise

from ontolog.inference.event_nouns import event_noun_from_slug
from ontolog.models.finding import ProviderInput
from ontolog.models.template import Template
from ontolog.providers.ids import slugify

_EVENT_PREFIX = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)")
_PARAM_PATTERN = re.compile(r"(\w+)=")

STRUCTURAL_FIELD_LABELS: frozenset[str] = frozenset({"interface", "segment"})


@dataclass(frozen=True)
class HierarchyIndex:
    """Maps fields to owning entities and collects chained ``owns`` edges."""

    field_owners: dict[tuple[str, str], str]
    owns_edges: frozenset[tuple[str, str]]
    owns_counts: dict[tuple[str, str], int]

    def field_owner(self, template_id: str, field_name: str) -> str | None:
        """Return the owning entity slug for a template field."""
        return self.field_owners.get((template_id, field_name))

    def owner_for_field_node(self, field_node_id: str) -> str | None:
        """Return the owning entity slug for a graph field node id."""
        template_id, field_name = _parse_field_node_id(field_node_id)
        return self.field_owner(template_id, field_name)


def ordered_entity_chain(template_text: str, *, process_slug: str | None) -> tuple[str, ...]:
    """Return entity slugs in template occurrence order."""
    slugs: list[str] = []
    if process_slug is not None:
        slugs.append(process_slug)
    event_slug = _event_slug_from_template(template_text)
    if event_slug is not None:
        noun = event_noun_from_slug(event_slug)
        if noun is not None:
            slugs.append(noun)
    for param_name in _parameter_names(template_text):
        if param_name.lower() in STRUCTURAL_FIELD_LABELS:
            slugs.append(slugify(param_name))
    return tuple(slugs)


def owner_slug_for_field(
    template_text: str,
    field_name: str,
    *,
    process_slug: str | None,
) -> str | None:
    """Return the nearest preceding entity slug that owns ``field_name``."""
    if field_name.lower() in STRUCTURAL_FIELD_LABELS:
        return None
    return _last_entity_before_field(template_text, field_name, process_slug=process_slug)


def build_hierarchy_index(data: ProviderInput) -> HierarchyIndex:
    """Build field ownership and chained ``owns`` edges from templates."""
    field_owners: dict[tuple[str, str], str] = {}
    owns_counter: Counter[tuple[str, str]] = Counter()
    process_by_template = _process_slug_by_template(data)
    for template in data.templates:
        process_slug = process_by_template.get(template.id)
        chain = ordered_entity_chain(template.template, process_slug=process_slug)
        _index_owns_chain(chain, owns_counter)
        _index_field_owners(template, process_slug, field_owners)
    return HierarchyIndex(
        field_owners=field_owners,
        owns_edges=frozenset(owns_counter),
        owns_counts=dict(owns_counter),
    )


def _index_owns_chain(
    chain: tuple[str, ...],
    owns_counter: Counter[tuple[str, str]],
) -> None:
    """Accumulate ``owns`` edge counts from an entity chain."""
    for parent_slug, child_slug in pairwise(chain):
        owns_counter[(parent_slug, child_slug)] += 1


def _index_field_owners(
    template: Template,
    process_slug: str | None,
    field_owners: dict[tuple[str, str], str],
) -> None:
    """Record field-to-entity ownership for one template."""
    for param_name in _parameter_names(template.template):
        owner = owner_slug_for_field(
            template.template,
            param_name,
            process_slug=process_slug,
        )
        if owner is None:
            continue
        field_owners[(template.id, param_name)] = owner


def _process_slug_by_template(data: ProviderInput) -> dict[str, str]:
    """Return the most common process slug for each template id."""
    counts: dict[str, Counter[str]] = {}
    for occurrence in data.occurrences:
        if occurrence.process is None:
            continue
        slug = slugify(occurrence.process)
        counts.setdefault(occurrence.template_id, Counter())[slug] += 1
    return {template_id: counter.most_common(1)[0][0] for template_id, counter in counts.items()}


def _last_entity_before_field(
    template_text: str,
    field_name: str,
    *,
    process_slug: str | None,
) -> str | None:
    """Walk template tokens and return the entity active at ``field_name``."""
    last_entity = _initial_entity_state(template_text, process_slug=process_slug)
    for param_name in _parameter_names(template_text):
        last_entity, found = _advance_entity_state(
            param_name,
            field_name,
            last_entity,
        )
        if found:
            return last_entity
    return last_entity


def _initial_entity_state(
    template_text: str,
    *,
    process_slug: str | None,
) -> str | None:
    """Return the entity slug active before the first parameter."""
    last_entity: str | None = None
    if process_slug is not None:
        last_entity = process_slug
    event_slug = _event_slug_from_template(template_text)
    if event_slug is not None:
        noun = event_noun_from_slug(event_slug)
        if noun is not None:
            last_entity = noun
    return last_entity


def _advance_entity_state(
    param_name: str,
    field_name: str,
    last_entity: str | None,
) -> tuple[str | None, bool]:
    """Update entity state for one parameter; return whether ``field_name`` was found."""
    if param_name.lower() in STRUCTURAL_FIELD_LABELS:
        return slugify(param_name), False
    if param_name == field_name:
        return last_entity, True
    return last_entity, False


def _event_slug_from_template(template_text: str) -> str | None:
    match = _EVENT_PREFIX.match(template_text.strip())
    if match is None:
        return None
    return slugify(match.group(1))


def _parameter_names(template_text: str) -> list[str]:
    return _PARAM_PATTERN.findall(template_text)


def _parse_field_node_id(field_node_id: str) -> tuple[str, str]:
    _, template_id, param_name = field_node_id.split(":", maxsplit=2)
    return template_id, param_name
