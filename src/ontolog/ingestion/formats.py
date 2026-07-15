"""Log format enumeration and auto-detection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ontolog.ingestion.parsers.json import is_json_log_line
from ontolog.ingestion.parsers.syslog import matches_syslog_line

__all__ = [
    "DEFAULT_FORMAT_DETECTION",
    "FormatDetectionSettings",
    "LogFormat",
    "detect_format",
]


@dataclass(frozen=True, slots=True)
class FormatDetectionSettings:
    """Tunables for auto-detecting log format from a line sample."""

    sample_size: int = 20
    match_threshold: float = 0.8


DEFAULT_FORMAT_DETECTION = FormatDetectionSettings()


class LogFormat(StrEnum):
    """Supported log file formats."""

    SYSLOG = "syslog"
    JSON = "json"
    PLAIN = "plain"
    AUTO = "auto"


def detect_format(
    lines: list[str],
    *,
    settings: FormatDetectionSettings = DEFAULT_FORMAT_DETECTION,
) -> LogFormat:
    """Detect the log format from a sample of preprocessed lines."""
    non_empty = [line for line in lines if line.strip()]
    if not non_empty:
        return LogFormat.PLAIN

    sample = non_empty[: settings.sample_size]
    json_count = sum(1 for line in sample if is_json_log_line(line))
    syslog_count = sum(1 for line in sample if matches_syslog_line(line))

    if json_count / len(sample) >= settings.match_threshold:
        return LogFormat.JSON
    if syslog_count / len(sample) >= settings.match_threshold:
        return LogFormat.SYSLOG
    if syslog_count > 0:
        return LogFormat.SYSLOG
    return LogFormat.PLAIN
