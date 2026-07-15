"""Syslog-style log line parser."""

from __future__ import annotations

from ontolog.ingestion.parsers.syslog_adapters import (
    SyslogParserChain,
    default_syslog_parser_chain,
)
from ontolog.models import LogRecord

__all__ = ["SyslogParser", "matches_syslog_line"]

_DEFAULT_CHAIN = default_syslog_parser_chain()


def matches_syslog_line(line: str) -> bool:
    """Return True if ``line`` matches any supported syslog pattern."""
    return _DEFAULT_CHAIN.matches(line)


class SyslogParser:
    """Parse RFC3164, ISO8601 syslog, and Apache error bracket lines."""

    def __init__(self, chain: SyslogParserChain | None = None) -> None:
        """Use ``chain`` or the default syslog adapter chain."""
        self._chain = chain or _DEFAULT_CHAIN

    @property
    def name(self) -> str:
        """Return the parser identifier."""
        return "syslog"

    def parse_line(self, line: str, *, line_number: int) -> LogRecord:
        """Delegate parsing to the configured adapter chain."""
        return self._chain.parse(line, line_number=line_number)
