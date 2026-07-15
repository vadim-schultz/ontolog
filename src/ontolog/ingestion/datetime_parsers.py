"""Datetime parsing adapters for log ingestion."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

__all__ = [
    "DatetimeInstanceParser",
    "DatetimeParser",
    "DatetimeParserChain",
    "IsoformatStringParser",
    "StrptimeFormatParser",
    "UnixTimestampParser",
    "default_datetime_parser",
    "parse_datetime_value",
    "to_utc",
]


def to_utc(value: datetime) -> datetime:
    """Normalize a parsed datetime to timezone-aware UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class DatetimeParser(Protocol):
    """Adapter that parses one kind of timestamp value."""

    def can_parse(self, value: object) -> bool:
        """Return True when this adapter should attempt parsing ``value``."""

    def parse(self, value: object) -> datetime:
        """Parse ``value`` into a datetime; raise :exc:`ValueError` on failure."""


class DatetimeParserChain:
    """Try registered parsers in order until one succeeds."""

    def __init__(self, parsers: tuple[DatetimeParser, ...] | list[DatetimeParser]) -> None:
        """Register parsers to try in order."""
        self._parsers = parsers

    def parse(self, value: object) -> datetime | None:
        """Return the first successful parse, or ``None`` when all adapters fail."""
        for parser in self._parsers:
            if not parser.can_parse(value):
                continue
            try:
                return parser.parse(value)
            except ValueError:
                continue
        return None


class DatetimeInstanceParser:
    """Parse values that are already :class:`datetime` instances."""

    def can_parse(self, value: object) -> bool:
        """Return True when ``value`` is a :class:`datetime`."""
        return isinstance(value, datetime)

    def parse(self, value: object) -> datetime:
        """Normalize ``value`` to timezone-aware UTC."""
        assert isinstance(value, datetime)
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


class UnixTimestampParser:
    """Parse Unix epoch timestamps supplied as integers or floats."""

    def can_parse(self, value: object) -> bool:
        """Return True when ``value`` is a numeric Unix timestamp."""
        return isinstance(value, (int, float))

    def parse(self, value: object) -> datetime:
        """Convert ``value`` from epoch seconds to UTC."""
        assert isinstance(value, (int, float))
        return datetime.fromtimestamp(value, tz=UTC)


class IsoformatStringParser:
    """Parse ISO-8601 strings, including trailing ``Z`` offsets."""

    def can_parse(self, value: object) -> bool:
        """Return True when ``value`` is a non-empty ISO-8601 string."""
        return isinstance(value, str) and bool(value.strip())

    def parse(self, value: object) -> datetime:
        """Parse ``value`` as ISO-8601, including trailing ``Z`` offsets."""
        assert isinstance(value, str)
        normalized = value.strip().replace("Z", "+00:00")
        return to_utc(datetime.fromisoformat(normalized))


class StrptimeFormatParser:
    """Parse strings with a single :meth:`datetime.strptime` format."""

    def __init__(self, fmt: str) -> None:
        """Store a :meth:`datetime.strptime` format string."""
        self._fmt = fmt

    def can_parse(self, value: object) -> bool:
        """Return True when ``value`` is a non-empty string."""
        return isinstance(value, str) and bool(value.strip())

    def parse(self, value: object) -> datetime:
        """Parse ``value`` with the configured strptime format."""
        assert isinstance(value, str)
        return to_utc(datetime.strptime(value.strip(), self._fmt))


def default_datetime_parser() -> DatetimeParserChain:
    """Build the default chain of log timestamp parsers."""
    return DatetimeParserChain(
        [
            DatetimeInstanceParser(),
            UnixTimestampParser(),
            IsoformatStringParser(),
            StrptimeFormatParser("%a %b %d %H:%M:%S %Y"),
            StrptimeFormatParser("%Y-%m-%d %H:%M:%S"),
            StrptimeFormatParser("%Y-%m-%dT%H:%M:%S"),
        ]
    )


_DEFAULT_PARSER = default_datetime_parser()


def parse_datetime_value(value: object) -> datetime | None:
    """Parse a timestamp from common log formats into timezone-aware UTC."""
    if value is None:
        return None
    return _DEFAULT_PARSER.parse(value)
