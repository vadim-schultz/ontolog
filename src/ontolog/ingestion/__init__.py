"""Log ingestion: parsers, preprocessors, and streaming reader."""

from ontolog.ingestion.formats import LogFormat, detect_format
from ontolog.ingestion.parsers import JsonParser, PlainParser, SyslogParser
from ontolog.ingestion.preprocessors import PreprocessorRegistry, default_preprocessor_registry
from ontolog.ingestion.reader import IngestOptions, ingest_path, iter_lines, iter_records
from ontolog.ingestion.registry import PARSER_REGISTRY, get_parser

__all__ = [
    "PARSER_REGISTRY",
    "IngestOptions",
    "JsonParser",
    "LogFormat",
    "PlainParser",
    "PreprocessorRegistry",
    "SyslogParser",
    "default_preprocessor_registry",
    "detect_format",
    "get_parser",
    "ingest_path",
    "iter_lines",
    "iter_records",
]
