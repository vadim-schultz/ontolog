"""Parser classes for log ingestion."""

from ontolog.ingestion.parsers.json import JsonParser
from ontolog.ingestion.parsers.plain import PlainParser
from ontolog.ingestion.parsers.syslog import SyslogParser

__all__ = ["JsonParser", "PlainParser", "SyslogParser"]
