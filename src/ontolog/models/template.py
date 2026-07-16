"""Template models for mined log patterns."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TemplateParameter(BaseModel):
    """One extracted parameter from a log message."""

    model_config = ConfigDict(frozen=True)

    name: str
    value: str


class TemplateOccurrence(BaseModel):
    """A single observed instance of a template."""

    model_config = ConfigDict(frozen=True)

    template_id: str
    timestamp: datetime | None = None
    message: str
    parameters: tuple[TemplateParameter, ...] = ()


class Template(BaseModel):
    """Stable parameterized pattern mined from log messages."""

    model_config = ConfigDict(frozen=True)

    id: str
    template: str
    occurrence_count: int = Field(default=1, ge=1)
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    examples: tuple[str, ...] = ()
