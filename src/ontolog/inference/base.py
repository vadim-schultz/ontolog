"""Inference pass registry and shared constants."""

from __future__ import annotations

from ontolog.config import InferenceConfig, InferenceKind
from ontolog.inference.entities import EntityInferencePass
from ontolog.inference.events import EventInferencePass
from ontolog.inference.fields import FieldInferencePass
from ontolog.inference.relationships import RelationshipInferencePass
from ontolog.inference.states import StateInferencePass
from ontolog.types import InferencePass

DEFAULT_INFERENCE_ORDER: tuple[InferenceKind, ...] = (
    InferenceKind.ENTITIES,
    InferenceKind.EVENTS,
    InferenceKind.FIELDS,
    InferenceKind.RELATIONSHIPS,
    InferenceKind.STATES,
)

_PASS_FACTORIES: dict[InferenceKind, type[InferencePass]] = {
    InferenceKind.ENTITIES: EntityInferencePass,
    InferenceKind.EVENTS: EventInferencePass,
    InferenceKind.FIELDS: FieldInferencePass,
    InferenceKind.RELATIONSHIPS: RelationshipInferencePass,
    InferenceKind.STATES: StateInferencePass,
}


def inference_registry(config: InferenceConfig) -> tuple[InferencePass, ...]:
    """Return enabled inference passes in default execution order."""
    passes: list[InferencePass] = []
    for kind in DEFAULT_INFERENCE_ORDER:
        if kind not in config.enabled:
            continue
        passes.append(_PASS_FACTORIES[kind]())
    return tuple(passes)
