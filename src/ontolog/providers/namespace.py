"""Namespace and hierarchy evidence from templates."""

from __future__ import annotations

import re

from ontolog.evidence.graph import EvidenceGraph
from ontolog.models.evidence import Edge, Evidence, Node, NodeKind
from ontolog.models.finding import EvidenceFinding, ProviderInput
from ontolog.models.template import Template, TemplateOccurrence
from ontolog.providers.ids import entity_id, event_id, field_id, slugify

_EVENT_PREFIX = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)")


class NamespaceProvider:
    """Infer entities, events, and fields from template structure."""

    @property
    def name(self) -> str:
        """Return the provider identifier."""
        return "namespace"

    def analyze(
        self,
        graph: EvidenceGraph,
        data: ProviderInput,
    ) -> tuple[EvidenceFinding, ...]:
        """Return namespace hierarchy findings."""
        entity_slugs = _collect_entity_slugs(data.occurrences)
        findings = [
            *_entity_findings(entity_slugs),
            *_event_findings(data.templates),
            *_occurrence_field_findings(data.occurrences),
            *_template_field_findings(data.templates, entity_slugs),
        ]
        return tuple(findings)


def _collect_entity_slugs(occurrences: tuple[TemplateOccurrence, ...]) -> set[str]:
    slugs: set[str] = set()
    for occurrence in occurrences:
        slug = _entity_slug_from_occurrence(occurrence.process)
        if slug is not None:
            slugs.add(slug)
    return slugs


def _entity_findings(entity_slugs: set[str]) -> list[EvidenceFinding]:
    return [_entity_finding(slug) for slug in entity_slugs]


def _event_findings(templates: tuple[Template, ...]) -> list[EvidenceFinding]:
    findings: list[EvidenceFinding] = []
    for template in templates:
        event_slug = _event_slug_from_template(template.template)
        if event_slug is not None:
            findings.append(_event_finding(event_slug))
    return findings


def _occurrence_field_findings(
    occurrences: tuple[TemplateOccurrence, ...],
) -> list[EvidenceFinding]:
    findings: list[EvidenceFinding] = []
    for occurrence in occurrences:
        entity_slug = _entity_slug_from_occurrence(occurrence.process)
        if entity_slug is None:
            continue
        for param in occurrence.parameters:
            findings.append(
                _field_link_finding(
                    entity_slug=entity_slug,
                    template_id=occurrence.template_id,
                    param_name=param.name,
                )
            )
    return findings


def _template_field_findings(
    templates: tuple[Template, ...],
    entity_slugs: set[str],
) -> list[EvidenceFinding]:
    if not entity_slugs:
        return []
    entity_slug = next(iter(entity_slugs))
    findings: list[EvidenceFinding] = []
    for template in templates:
        for token in _parameter_names(template.template):
            findings.append(
                _field_link_finding(
                    entity_slug=entity_slug,
                    template_id=template.id,
                    param_name=token,
                )
            )
    return findings


def _entity_slug_from_occurrence(process: str | None) -> str | None:
    if process is None:
        return None
    return slugify(process)


def _event_slug_from_template(template_text: str) -> str | None:
    match = _EVENT_PREFIX.match(template_text.strip())
    if match is None:
        return None
    return slugify(match.group(1))


def _parameter_names(template_text: str) -> list[str]:
    return re.findall(r"(\w+)=", template_text)


def _entity_finding(slug: str) -> EvidenceFinding:
    node_id = entity_id(slug)
    evidence = Evidence(
        source="namespace",
        score=0.8,
        explanation=f"Entity inferred from process name {slug!r}",
    )
    node = Node(
        id=node_id, kind=NodeKind.ENTITY, label=slug.replace("_", " ").title(), evidence=(evidence,)
    )
    return EvidenceFinding(evidence=evidence, node=node)


def _event_finding(slug: str) -> EvidenceFinding:
    node_id = event_id(slug)
    evidence = Evidence(
        source="namespace",
        score=0.75,
        explanation=f"Event inferred from template prefix {slug!r}",
    )
    node = Node(
        id=node_id, kind=NodeKind.EVENT, label=slug.replace("_", " ").title(), evidence=(evidence,)
    )
    return EvidenceFinding(evidence=evidence, node=node)


def _field_link_finding(
    *,
    entity_slug: str,
    template_id: str,
    param_name: str,
) -> EvidenceFinding:
    field_node_id = field_id(template_id, param_name)
    entity_node_id = entity_id(entity_slug)
    evidence = Evidence(
        source="namespace",
        score=0.7,
        explanation=f"Field {param_name!r} linked to entity {entity_slug!r}",
    )
    field_node = Node(id=field_node_id, kind=NodeKind.FIELD, label=param_name, evidence=(evidence,))
    edge = Edge(
        source_id=entity_node_id, target_id=field_node_id, label="has_field", evidence=(evidence,)
    )
    return EvidenceFinding(evidence=evidence, node=field_node, edge=edge)
