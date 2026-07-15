"""Syslog line format adapters."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol

from ontolog.errors import ParseError
from ontolog.ingestion.parsers.base import build_log_record, strip_message

if TYPE_CHECKING:
    from ontolog.models import LogRecord

__all__ = [
    "ApacheBracketSyslogAdapter",
    "Iso8601SyslogAdapter",
    "RegexSyslogAdapter",
    "Rfc3164SyslogAdapter",
    "SyslogLineParser",
    "SyslogParserChain",
    "UnrecognizedSyslogAdapter",
    "default_syslog_parser_chain",
]


SyslogGroups = dict[str, str | None]


def _parse_iso8601_timestamp(text: str) -> datetime:
    normalized = text.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _parse_rfc3164_timestamp(text: str, *, reference: datetime | None = None) -> datetime:
    now = reference or datetime.now(tz=UTC)
    parsed = datetime.strptime(f"{text} {now.year}", "%b %d %H:%M:%S %Y").replace(tzinfo=UTC)
    if parsed > now and now.month == 1 and parsed.month == 12:
        parsed = parsed.replace(year=now.year - 1)
    return parsed


def _parse_apache_timestamp(text: str) -> datetime:
    parsed = datetime.strptime(text.strip(), "%a %b %d %H:%M:%S %Y")
    return parsed.replace(tzinfo=UTC)


class SyslogLineParser(Protocol):
    """Adapter that recognizes and parses one syslog line format."""

    def matches(self, line: str) -> bool:
        """Return True when this adapter handles ``line``."""

    def parse(self, line: str, *, line_number: int) -> LogRecord:
        """Parse ``line`` into a :class:`LogRecord`."""


class SyslogParserChain:
    """Try registered adapters in order, then fall back to the null object."""

    def __init__(
        self,
        parsers: tuple[SyslogLineParser, ...] | list[SyslogLineParser],
        *,
        fallback: SyslogLineParser,
    ) -> None:
        """Register adapters to try in order plus a fallback."""
        self._parsers = parsers
        self._fallback = fallback

    def matches(self, line: str) -> bool:
        """Return True when any adapter recognizes ``line``."""
        return any(parser.matches(line) for parser in self._parsers)

    def parse(self, line: str, *, line_number: int) -> LogRecord:
        """Parse ``line`` with the first matching adapter."""
        for parser in self._parsers:
            if parser.matches(line):
                return parser.parse(line, line_number=line_number)
        return self._fallback.parse(line, line_number=line_number)


class RegexSyslogAdapter:
    """Base adapter that matches a line with a compiled regular expression."""

    pattern: re.Pattern[str]

    def matches(self, line: str) -> bool:
        """Return True when ``line`` matches :attr:`pattern`."""
        return self.pattern.match(line) is not None

    def parse(self, line: str, *, line_number: int) -> LogRecord:
        """Match ``line`` and build a record from named groups."""
        match = self.pattern.match(line)
        if match is None:
            msg = "line does not match adapter pattern"
            raise ParseError(msg, line=line, line_number=line_number)
        return self.build_record(line, line_number=line_number, groups=match.groupdict())

    def build_record(
        self,
        line: str,
        *,
        line_number: int,
        groups: SyslogGroups,
    ) -> LogRecord:
        """Build a :class:`LogRecord` from regex ``groups``."""
        raise NotImplementedError


class Iso8601SyslogAdapter(RegexSyslogAdapter):
    """Parse ISO-8601 syslog lines with hostname, process, and optional level."""

    pattern = re.compile(
        r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2}))"
        r"\s+(?P<hostname>\S+)"
        r"\s+(?P<process>\S+?)(?:\[(?P<pid>\d+)\])?:"
        r"(?:\s+(?P<level>DEBUG|INFO|WARN(?:ING)?|ERROR|CRITICAL|TRACE|FATAL|NOTICE))?"
        r"\s+(?P<message>.+)$",
        re.IGNORECASE,
    )

    def build_record(
        self,
        line: str,
        *,
        line_number: int,
        groups: SyslogGroups,
    ) -> LogRecord:
        """Map ISO-8601 syslog capture groups to a :class:`LogRecord`."""
        level = groups.get("level")
        pid_text = groups.get("pid")
        return build_log_record(
            line=line,
            line_number=line_number,
            timestamp=_parse_iso8601_timestamp(groups["timestamp"]),  # type: ignore[arg-type]
            hostname=groups["hostname"],
            process=groups["process"],
            pid=int(pid_text) if pid_text else None,
            level=level.upper() if level else None,
            message=groups["message"],  # type: ignore[arg-type]
        )


class Rfc3164SyslogAdapter(RegexSyslogAdapter):
    """Parse traditional BSD syslog (RFC 3164) lines."""

    pattern = re.compile(
        r"^(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
        r"\s+(?P<hostname>\S+)"
        r"\s+(?P<process>\S+?)\[(?P<pid>\d+)\]:"
        r"\s+(?P<message>.+)$",
    )

    def build_record(
        self,
        line: str,
        *,
        line_number: int,
        groups: SyslogGroups,
    ) -> LogRecord:
        """Map RFC 3164 capture groups to a :class:`LogRecord`."""
        return build_log_record(
            line=line,
            line_number=line_number,
            timestamp=_parse_rfc3164_timestamp(groups["timestamp"]),  # type: ignore[arg-type]
            hostname=groups["hostname"],
            process=groups["process"],
            pid=int(groups["pid"]),  # type: ignore[arg-type]
            message=groups["message"],  # type: ignore[arg-type]
        )


class ApacheBracketSyslogAdapter(RegexSyslogAdapter):
    """Parse Apache error-log lines with bracketed timestamp and level."""

    pattern = re.compile(
        r"^\[(?P<timestamp>[^\]]+)\]\s+\[(?P<level>[^\]]+)\]\s+(?P<message>.+)$",
    )

    def build_record(
        self,
        line: str,
        *,
        line_number: int,
        groups: SyslogGroups,
    ) -> LogRecord:
        """Map Apache bracket capture groups to a :class:`LogRecord`."""
        level = groups["level"]
        return build_log_record(
            line=line,
            line_number=line_number,
            timestamp=_parse_apache_timestamp(groups["timestamp"]),  # type: ignore[arg-type]
            process="apache",
            level=level.upper() if level else None,
            message=strip_message(groups["message"]),  # type: ignore[arg-type]
        )


class UnrecognizedSyslogAdapter:
    """Null object adapter for lines that match no known syslog format."""

    def matches(self, line: str) -> bool:
        """Return True for every line so the chain can raise a parse error."""
        return True

    def parse(self, line: str, *, line_number: int) -> LogRecord:
        """Raise :exc:`~ontolog.errors.ParseError` for unrecognized syslog lines."""
        msg = "unrecognized syslog line"
        raise ParseError(msg, line=line, line_number=line_number)


def default_syslog_parser_chain() -> SyslogParserChain:
    """Build the default chain of syslog line adapters."""
    return SyslogParserChain(
        [
            Iso8601SyslogAdapter(),
            Rfc3164SyslogAdapter(),
            ApacheBracketSyslogAdapter(),
        ],
        fallback=UnrecognizedSyslogAdapter(),
    )
