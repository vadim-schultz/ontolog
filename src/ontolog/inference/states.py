"""State machine inference from lifecycle signals."""

from __future__ import annotations

from collections import Counter
from itertools import pairwise

from ontolog.config import ConfidenceThresholds
from ontolog.evidence.graph import EvidenceGraph
from ontolog.inference.scoring import combine_scores
from ontolog.inference.status_values import status_label_from_template
from ontolog.models.candidate import InferenceResult, StateMachineCandidate, StateTransition
from ontolog.models.evidence import Evidence
from ontolog.models.finding import ProviderInput
from ontolog.models.template import Template, TemplateOccurrence

_DEFAULT_MIN_SUPPORT = 2
_STATUS_PARAM = "status"
_ORDER_LIFECYCLE_NAME = "OrderLifecycle"


class StateInferencePass:
    """Infer lifecycle state machines from status parameters and sequences."""

    @property
    def name(self) -> str:
        """Return the inference pass identifier."""
        return "states"

    def infer(
        self,
        graph: EvidenceGraph,
        data: ProviderInput,
        *,
        thresholds: ConfidenceThresholds,
    ) -> InferenceResult:
        """Return state machine candidates."""
        machine = _lifecycle_state_machine(graph, data, thresholds.entity)
        if machine is None:
            return InferenceResult()
        return InferenceResult(state_machines=(machine,))


def _lifecycle_state_machine(
    graph: EvidenceGraph,
    data: ProviderInput,
    min_confidence: float,
) -> StateMachineCandidate | None:
    """Return an order lifecycle machine when transition evidence is sufficient."""
    transition_counts = _merged_transition_counts(graph, data)
    if not transition_counts:
        return None
    transitions = _build_transitions(transition_counts)
    confidence = combine_scores([transition.confidence for transition in transitions])
    if confidence < min_confidence:
        return None
    return _build_state_machine(transitions, confidence)


def _merged_transition_counts(
    graph: EvidenceGraph,
    data: ProviderInput,
) -> Counter[tuple[str, str]]:
    """Merge status-parameter and temporal transition counts."""
    status_counts = _transition_counts_from_status_param(data.occurrences, data.templates)
    follows_counts = _transition_counts_from_follows(graph, data.templates)
    return _merge_transition_counts(status_counts, follows_counts)


def _build_state_machine(
    transitions: tuple[StateTransition, ...],
    confidence: float,
) -> StateMachineCandidate:
    """Build a lifecycle state machine from observed transitions."""
    return StateMachineCandidate(
        name=_ORDER_LIFECYCLE_NAME,
        states=_ordered_states(transitions),
        transitions=transitions,
        confidence=confidence,
        evidence=_state_machine_evidence(confidence),
    )


def _state_machine_evidence(confidence: float) -> tuple[Evidence, ...]:
    """Return provenance for a mined lifecycle state machine."""
    return (
        Evidence(
            source="states",
            score=confidence,
            explanation="Lifecycle transitions mined from status parameters and temporal edges",
        ),
    )


def _transition_counts_from_status_param(
    occurrences: tuple[TemplateOccurrence, ...],
    templates: tuple[Template, ...],
) -> Counter[tuple[str, str]]:
    """Count adjacent status values from ordered occurrences."""
    templates_by_id = _templates_by_id(templates)
    status_values = _ordered_status_values(occurrences, templates_by_id)
    return _pairwise_transition_counts(status_values)


def _templates_by_id(templates: tuple[Template, ...]) -> dict[str, Template]:
    """Index templates by identifier."""
    return {template.id: template for template in templates}


def _ordered_status_values(
    occurrences: tuple[TemplateOccurrence, ...],
    templates_by_id: dict[str, Template],
) -> list[str]:
    """Return status values from occurrences sorted by timestamp."""
    ordered = sorted(
        occurrences,
        key=lambda item: (item.timestamp is None, item.timestamp or ""),
    )
    values: list[str] = []
    for occurrence in ordered:
        value = _status_value(occurrence, templates_by_id)
        if value is not None:
            values.append(value)
    return values


def _pairwise_transition_counts(values: list[str]) -> Counter[tuple[str, str]]:
    """Count adjacent value pairs as state transitions."""
    counts: Counter[tuple[str, str]] = Counter()
    for left, right in pairwise(values):
        counts[(left, right)] += 1
    return counts


def _status_value(
    occurrence: TemplateOccurrence,
    templates_by_id: dict[str, Template],
) -> str | None:
    """Resolve the status label for one occurrence."""
    for param in occurrence.parameters:
        if param.name == _STATUS_PARAM:
            return param.value
    template = templates_by_id.get(occurrence.template_id)
    if template is None:
        return None
    return status_label_from_template(template.template)


def _transition_counts_from_follows(
    graph: EvidenceGraph,
    templates: tuple[Template, ...],
) -> Counter[tuple[str, str]]:
    """Count transitions implied by temporal ``follows`` edges."""
    template_labels = {
        template.id: status_label_from_template(template.template) for template in templates
    }
    counts: Counter[tuple[str, str]] = Counter()
    for edge in graph.edges():
        if edge.label != "follows":
            continue
        transition = _follows_transition(edge.source_id, edge.target_id, template_labels)
        if transition is not None:
            counts[transition] += 1
    return counts


def _follows_transition(
    source_id: str,
    target_id: str,
    template_labels: dict[str, str | None],
) -> tuple[str, str] | None:
    """Return a state transition pair from one ``follows`` edge."""
    left = template_labels.get(source_id.removeprefix("template:"))
    right = template_labels.get(target_id.removeprefix("template:"))
    if left is None or right is None:
        return None
    return left, right


def _merge_transition_counts(
    left: Counter[tuple[str, str]],
    right: Counter[tuple[str, str]],
) -> Counter[tuple[str, str]]:
    """Merge two transition count maps."""
    merged: Counter[tuple[str, str]] = Counter(left)
    merged.update(right)
    return merged


def _build_transitions(counts: Counter[tuple[str, str]]) -> tuple[StateTransition, ...]:
    """Build supported state transitions from counted pairs."""
    transitions: list[StateTransition] = []
    for (from_state, to_state), count in sorted(counts.items()):
        if count < _DEFAULT_MIN_SUPPORT:
            continue
        transitions.append(_state_transition(from_state, to_state, count))
    return tuple(transitions)


def _state_transition(from_state: str, to_state: str, count: int) -> StateTransition:
    """Build one transition with confidence derived from support count."""
    confidence = min(1.0, 0.55 + 0.05 * count)
    return StateTransition(
        from_state=from_state,
        to_state=to_state,
        count=count,
        confidence=confidence,
    )


def _ordered_states(transitions: tuple[StateTransition, ...]) -> tuple[str, ...]:
    """Return states in first-seen order across transitions."""
    states: list[str] = []
    for transition in transitions:
        for value in (transition.from_state, transition.to_state):
            if value not in states:
                states.append(value)
    return tuple(states)
