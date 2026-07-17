"""Aggregate state machine candidates into domain state machines."""

from __future__ import annotations

from ontolog.config import ConfidenceThresholds, EvidenceSourceWeights
from ontolog.inference.aggregate._grouping import aggregate_ranked_groups
from ontolog.models.candidate import StateMachineCandidate
from ontolog.models.domain import Alternative, StateMachine, StateTransition


def _state_machine_from_primary(
    name: str,
    primary: StateMachineCandidate,
    confidence: float,
    alternatives: tuple[Alternative, ...],
    export_eligible: bool,
) -> StateMachine:
    """Map the winning state machine candidate to a domain state machine."""
    transitions = tuple(
        StateTransition(
            from_state=transition.from_state,
            to_state=transition.to_state,
            count=transition.count,
            confidence=transition.confidence,
        )
        for transition in primary.transitions
    )
    return StateMachine(
        name=name,
        states=primary.states,
        transitions=transitions,
        confidence=confidence,
        evidence=primary.evidence,
        alternatives=alternatives,
        export_eligible=export_eligible,
    )


def aggregate_state_machines(
    candidates: tuple[StateMachineCandidate, ...],
    *,
    weights: EvidenceSourceWeights,
    thresholds: ConfidenceThresholds,
) -> tuple[StateMachine, ...]:
    """Merge state machine candidates grouped by name."""
    return aggregate_ranked_groups(
        candidates,
        key_fn=lambda candidate: candidate.name,
        alternative_value_fn=lambda candidate: candidate.name,
        tie_key_fn=lambda candidate: (candidate.name,),
        build=_state_machine_from_primary,
        weights=weights,
        export_threshold=thresholds.export,
    )
