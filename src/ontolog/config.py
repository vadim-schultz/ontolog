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


class ConfidenceThresholds(BaseModel):
    """Minimum confidence scores for inference and export eligibility."""

    model_config = ConfigDict(frozen=True)

    export: float = Field(default=0.7, ge=0.0, le=1.0)
    field: float = Field(default=0.5, ge=0.0, le=1.0)
    entity: float = Field(default=0.6, ge=0.0, le=1.0)
    relationship: float = Field(default=0.6, ge=0.0, le=1.0)
    event: float = Field(default=0.5, ge=0.0, le=1.0)


class OntologConfig(BaseModel):
    """Top-level ontolog configuration."""

    model_config = ConfigDict(frozen=True)

    masks: MaskConfig = Field(default_factory=MaskConfig)
    confidence: ConfidenceThresholds = Field(default_factory=ConfidenceThresholds)
    storage_path: Path = Path("ontolog.db")


def default_config() -> OntologConfig:
    """Return the default configuration."""
    return OntologConfig()
