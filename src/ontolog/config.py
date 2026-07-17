"""Configuration models and defaults."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class MaskKind(StrEnum):
    """Token classes masked before template extraction."""

    IP = "ip"
    UUID = "uuid"
    MAC = "mac"
    HEX = "hex"
    EMAIL = "email"
    NUMBER = "number"
    TIMESTAMP = "timestamp"


class MaskConfig(BaseModel):
    """Masking rules applied during template extraction."""

    model_config = ConfigDict(frozen=True)

    enabled: frozenset[MaskKind] = Field(default_factory=lambda: frozenset(MaskKind))


class ProviderKind(StrEnum):
    """Deterministic evidence provider identifiers."""

    REGEX = "regex"
    STATISTICS = "statistics"
    CO_OCCURRENCE = "co_occurrence"
    NAMESPACE = "namespace"
    TEMPORAL = "temporal"
    PROCESS = "process"


class ProviderConfig(BaseModel):
    """Enable/disable deterministic evidence providers."""

    model_config = ConfigDict(frozen=True)

    enabled: frozenset[ProviderKind] = Field(default_factory=lambda: frozenset(ProviderKind))


class InferenceKind(StrEnum):
    """Inference pass identifiers."""

    ENTITIES = "entities"
    EVENTS = "events"
    FIELDS = "fields"
    RELATIONSHIPS = "relationships"
    STATES = "states"


class InferenceConfig(BaseModel):
    """Enable/disable inference passes."""

    model_config = ConfigDict(frozen=True)

    enabled: frozenset[InferenceKind] = Field(default_factory=lambda: frozenset(InferenceKind))


class ConfidenceThresholds(BaseModel):
    """Minimum confidence scores for inference and export eligibility."""

    model_config = ConfigDict(frozen=True)

    export: float = Field(default=0.7, ge=0.0, le=1.0)
    field: float = Field(default=0.5, ge=0.0, le=1.0)
    entity: float = Field(default=0.6, ge=0.0, le=1.0)
    relationship: float = Field(default=0.6, ge=0.0, le=1.0)
    event: float = Field(default=0.5, ge=0.0, le=1.0)


class EvidenceSourceTier(StrEnum):
    """Evidence provenance tier for aggregation priority."""

    HUMAN = "human"
    DETERMINISTIC = "deterministic"
    LLM = "llm"


class EvidenceSourceWeights(BaseModel):
    """Per-tier multipliers applied during confidence aggregation."""

    model_config = ConfigDict(frozen=True)

    human: float = Field(default=1.0, ge=0.0, le=1.0)
    deterministic: float = Field(default=0.85, ge=0.0, le=1.0)
    llm: float = Field(default=0.5, ge=0.0, le=1.0)


class OntologConfig(BaseModel):
    """Top-level ontolog configuration."""

    model_config = ConfigDict(frozen=True)

    masks: MaskConfig = Field(default_factory=MaskConfig)
    providers: ProviderConfig = Field(default_factory=ProviderConfig)
    inference: InferenceConfig = Field(default_factory=InferenceConfig)
    confidence: ConfidenceThresholds = Field(default_factory=ConfidenceThresholds)
    source_weights: EvidenceSourceWeights = Field(default_factory=EvidenceSourceWeights)
    storage_path: Path = Path("ontolog.db")


def default_config() -> OntologConfig:
    """Return the default configuration."""
    return OntologConfig()
