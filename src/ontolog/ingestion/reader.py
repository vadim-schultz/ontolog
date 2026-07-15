"""Streaming log file reader and ingest pipeline."""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from ontolog.errors import ParseError
from ontolog.ingestion.formats import DEFAULT_FORMAT_DETECTION, LogFormat, detect_format
from ontolog.ingestion.parsers.base import is_blank_line
from ontolog.ingestion.preprocessors import PreprocessorRegistry, default_preprocessor_registry
from ontolog.ingestion.registry import get_parser
from ontolog.ingestion.source_adapters import (
    LOG_FILE_EXTENSIONS,
    default_log_source_resolver,
)
from ontolog.models import LogRecord
from ontolog.types import LogParser

__all__ = ["LOG_FILE_EXTENSIONS", "IngestOptions", "ingest_path", "iter_lines", "iter_records"]

logger = logging.getLogger(__name__)

_DEFAULT_SOURCE_RESOLVER = default_log_source_resolver()


@dataclass(frozen=True)
class IngestOptions:
    """Options controlling log ingestion."""

    format: LogFormat = LogFormat.AUTO
    preprocessors: Sequence[str] = field(default_factory=tuple)
    skip_errors: bool = False
    limit: int | None = None


def _resolve_paths(source: Path | str) -> list[Path]:
    return _DEFAULT_SOURCE_RESOLVER.resolve(source)


def iter_lines(source: Path) -> Iterator[tuple[int, str]]:
    """Yield ``(line_number, text)`` from a file or stdin."""
    if str(source) == "-":
        for line_number, line in enumerate(sys.stdin, start=1):
            yield line_number, line.rstrip("\n")
        return

    with source.open(encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            yield line_number, line.rstrip("\n")


def _sample_lines(
    path: Path,
    *,
    registry: PreprocessorRegistry,
    extra_preprocessors: Sequence[str],
    sample_size: int = DEFAULT_FORMAT_DETECTION.sample_size,
) -> list[str]:
    samples: list[str] = []
    for line_number, line in iter_lines(path):
        processed = registry.apply(
            line,
            line_number=line_number,
            chain=extra_preprocessors,
        )
        if is_blank_line(processed):
            continue
        samples.append(processed)
        if len(samples) >= sample_size:
            break
    return samples


def _resolve_format(
    path: Path,
    options: IngestOptions,
    *,
    registry: PreprocessorRegistry,
) -> LogFormat:
    if options.format != LogFormat.AUTO:
        return options.format
    samples = _sample_lines(
        path,
        registry=registry,
        extra_preprocessors=options.preprocessors,
    )
    return detect_format(samples)


def _resolve_parser_format(
    paths: list[Path],
    options: IngestOptions,
    *,
    registry: PreprocessorRegistry,
) -> LogFormat:
    if options.format != LogFormat.AUTO or not paths:
        return options.format
    return _resolve_format(paths[0], options, registry=registry)


def _preprocess_line(
    line: str,
    *,
    line_number: int,
    registry: PreprocessorRegistry,
    preprocessors: Sequence[str],
) -> str:
    return registry.apply(
        line,
        line_number=line_number,
        chain=preprocessors,
    )


def _parse_line_to_record(
    parser: LogParser,
    processed: str,
    *,
    line_number: int,
    path: Path,
    skip_errors: bool,
) -> LogRecord | None:
    try:
        return parser.parse_line(processed, line_number=line_number)
    except ParseError:
        if skip_errors:
            logger.warning(
                "skipping unparseable line %s in %s",
                line_number,
                path,
            )
            return None
        raise


def _iter_path_records(
    path: Path,
    *,
    parser: LogParser,
    registry: PreprocessorRegistry,
    options: IngestOptions,
) -> Iterator[LogRecord]:
    for line_number, line in iter_lines(path):
        processed = _preprocess_line(
            line,
            line_number=line_number,
            registry=registry,
            preprocessors=options.preprocessors,
        )
        if is_blank_line(processed):
            continue
        record = _parse_line_to_record(
            parser,
            processed,
            line_number=line_number,
            path=path,
            skip_errors=options.skip_errors,
        )
        if record is not None:
            yield record


def iter_records(
    source: Path | str,
    options: IngestOptions,
    *,
    registry: PreprocessorRegistry | None = None,
) -> Iterator[LogRecord]:
    """Yield normalized records from ``source``."""
    preprocessor_registry = registry or default_preprocessor_registry()
    paths = _resolve_paths(source)
    parser = get_parser(
        _resolve_parser_format(paths, options, registry=preprocessor_registry),
    )
    emitted = 0

    for path in paths:
        for record in _iter_path_records(
            path,
            parser=parser,
            registry=preprocessor_registry,
            options=options,
        ):
            yield record
            emitted += 1
            if options.limit is not None and emitted >= options.limit:
                return


def ingest_path(
    source: Path | str,
    options: IngestOptions | None = None,
    *,
    registry: PreprocessorRegistry | None = None,
) -> Iterator[LogRecord]:
    """Public API entry point for log ingestion."""
    return iter_records(source, options or IngestOptions(), registry=registry)
