"""Parser registry and factory."""

from __future__ import annotations

from ontolog.ingestion.formats import LogFormat
from ontolog.ingestion.parsers.json import JsonParser
from ontolog.ingestion.parsers.plain import PlainParser
from ontolog.ingestion.parsers.syslog import SyslogParser
from ontolog.types import LogParser

__all__ = ["PARSER_REGISTRY", "get_parser"]

PARSER_REGISTRY: dict[str, LogParser] = {
    LogFormat.SYSLOG: SyslogParser(),
    LogFormat.JSON: JsonParser(),
    LogFormat.PLAIN: PlainParser(),
}


def get_parser(log_format: LogFormat) -> LogParser:
    """Return the parser for ``log_format``."""
    if log_format == LogFormat.AUTO:
        msg = "cannot get parser for AUTO format; detect format first"
        raise ValueError(msg)
    parser = PARSER_REGISTRY.get(log_format)
    if parser is None:
        msg = f"unsupported log format: {log_format}"
        raise ValueError(msg)
    return parser
