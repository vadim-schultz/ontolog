"""Shared helpers for log line parsers."""

from __future__ import annotations

from datetime import datetime

from pydantic import ValidationError

from ontolog.errors import ParseError
from ontolog.ingestion.datetime_parsers import parse_datetime_value
from ontolog.models import LogRecord

__all__ = [
    "build_log_record",
    "is_blank_line",
    "parse_datetime_value",
    "strip_message",
]


def is_blank_line(line: str) -> bool:
    """Return True when the line is empty or whitespace-only."""
    return not line.strip()


def strip_message(message: str) -> str:
    """Strip trailing whitespace while preserving internal spacing."""
    return message.rstrip()


def build_log_record(
    *,
    line: str,
    line_number: int,
    timestamp: datetime | None = None,
    hostname: str | None = None,
    process: str | None = None,
    pid: int | None = None,
    level: str | None = None,
    logger: str | None = None,
    message: str,
) -> LogRecord:
    """Construct a :class:`LogRecord`, wrapping validation errors as :class:`ParseError`."""
    try:
        return LogRecord(
            timestamp=timestamp,
            hostname=hostname,
            process=process,
            pid=pid,
            level=level,
            logger=logger,
            message=strip_message(message),
        )
    except ValidationError as exc:
        msg = "invalid log record"
        raise ParseError(msg, line=line, line_number=line_number) from exc
