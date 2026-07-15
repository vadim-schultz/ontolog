"""JSON Lines log parser."""

from __future__ import annotations

import json
from typing import Any

from ontolog.errors import ParseError
from ontolog.ingestion.parsers.base import build_log_record, parse_datetime_value
from ontolog.models import LogRecord

__all__ = ["JsonParser", "is_json_log_line"]

_TIMESTAMP_KEYS = ("@timestamp", "timestamp", "time", "ts")
_HOSTNAME_KEYS = ("hostname", "host", "_HOSTNAME")
_PROCESS_KEYS = ("process", "syslog.ident", "ident", "app")
_PID_KEYS = ("pid", "process_id")
_LEVEL_KEYS = ("level", "log_level", "severity", "PRIORITY", "syslog.priority")
_LOGGER_KEYS = ("logger", "logger_name", "name", "syslog.tag")
_MESSAGE_KEYS = ("event", "message", "MESSAGE", "msg", "@message")
_SYSLOG_PRIORITY_LEVELS: dict[int, str] = {
    0: "EMERG",
    1: "ALERT",
    2: "CRIT",
    3: "ERROR",
    4: "WARNING",
    5: "NOTICE",
    6: "INFO",
    7: "DEBUG",
}


def is_json_log_line(line: str) -> bool:
    """Return True when ``line`` is a JSON object."""
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return False
    return isinstance(data, dict)


def _first_value(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


def _stringify_message(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def _parse_level(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, int):
        return _SYSLOG_PRIORITY_LEVELS.get(value, str(value))
    if isinstance(value, str) and value.isdigit():
        priority = int(value)
        return _SYSLOG_PRIORITY_LEVELS.get(priority, value)
    return str(value)


def _parse_pid(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


class JsonParser:
    """Parse JSONL lines including generic, journald, and structlog dialects."""

    @property
    def name(self) -> str:
        """Return the parser identifier."""
        return "json"

    def parse_line(self, line: str, *, line_number: int) -> LogRecord:
        """Parse a JSON object line into a :class:`~ontolog.models.LogRecord`."""
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            msg = "invalid JSON line"
            raise ParseError(msg, line=line, line_number=line_number) from exc

        if not isinstance(data, dict):
            msg = "JSON line must be an object"
            raise ParseError(msg, line=line, line_number=line_number)

        raw_message = _first_value(data, _MESSAGE_KEYS)
        if raw_message is None:
            msg = "JSON line missing message field"
            raise ParseError(msg, line=line, line_number=line_number)

        timestamp = parse_datetime_value(_first_value(data, _TIMESTAMP_KEYS))
        hostname = _first_value(data, _HOSTNAME_KEYS)
        process = _first_value(data, _PROCESS_KEYS)
        pid = _parse_pid(_first_value(data, _PID_KEYS))
        level = _parse_level(_first_value(data, _LEVEL_KEYS))
        logger = _first_value(data, _LOGGER_KEYS)

        return build_log_record(
            line=line,
            line_number=line_number,
            timestamp=timestamp,
            hostname=str(hostname) if hostname is not None else None,
            process=str(process) if process is not None else None,
            pid=pid,
            level=level,
            logger=str(logger) if logger is not None else None,
            message=_stringify_message(raw_message),
        )
