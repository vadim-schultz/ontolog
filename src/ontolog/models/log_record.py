"""Normalized log event model."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

OptionalStr = Annotated[str | None, Field(default=None)]


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class LogRecord(BaseModel):
    """Normalized representation of one log event."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    timestamp: datetime | None = None
    hostname: OptionalStr = None
    process: OptionalStr = None
    pid: Annotated[int | None, Field(default=None, ge=1)] = None
    level: OptionalStr = None
    logger: OptionalStr = None
    message: str

    @field_validator("hostname", "process", "logger", mode="before")
    @classmethod
    def _strip_optional_str(cls, value: object) -> object:
        if isinstance(value, str):
            return _strip_or_none(value)
        return value

    @field_validator("level", mode="before")
    @classmethod
    def _normalize_level(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = _strip_or_none(value)
            if stripped is None:
                return None
            return stripped.upper()
        return value
