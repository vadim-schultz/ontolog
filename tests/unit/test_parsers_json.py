"""Tests for JSON Lines parser."""

from __future__ import annotations

import pytest

from ontolog.errors import ParseError
from ontolog.ingestion.parsers.json import JsonParser


def test_parse_generic_jsonl() -> None:
    line = (
        '{"message": "service started", "timestamp": "2024-01-15T10:00:00Z", '
        '"level": "info", "hostname": "app-01", "process": "api", "pid": 4242}'
    )
    record = JsonParser().parse_line(line, line_number=1)

    assert record.message == "service started"
    assert record.hostname == "app-01"
    assert record.process == "api"
    assert record.pid == 4242
    assert record.level == "INFO"


def test_parse_journald_fields() -> None:
    line = '{"_HOSTNAME": "edge-01", "MESSAGE": "connection accepted", "PRIORITY": "6"}'
    record = JsonParser().parse_line(line, line_number=1)

    assert record.hostname == "edge-01"
    assert record.message == "connection accepted"
    assert record.level == "INFO"


def test_parse_structlog_event_and_log_level() -> None:
    line = (
        '{"event": "PacketSent", "log_level": "warning", '
        '"timestamp": "2024-01-15T12:00:01.123456Z"}'
    )
    record = JsonParser().parse_line(line, line_number=1)

    assert record.message == "PacketSent"
    assert record.level == "WARNING"
    assert record.timestamp is not None


def test_missing_message_raises() -> None:
    with pytest.raises(ParseError, match="missing message field"):
        JsonParser().parse_line('{"timestamp": "2024-01-15T10:00:00Z"}', line_number=1)


def test_nested_message_stringified() -> None:
    line = '{"message": {"detail": "nested"}, "timestamp": "2024-01-15T12:02:00Z"}'
    record = JsonParser().parse_line(line, line_number=1)

    assert record.message == '{"detail":"nested"}'


def test_scalar_context_fields_appended_to_message() -> None:
    line = (
        '{"event": "PacketSent", "level": "info", "timestamp": "2024-01-15T12:00:01.123456Z", '
        '"interface": "eth0", "destination": "192.168.1.10"}'
    )
    record = JsonParser().parse_line(line, line_number=1)

    assert record.message == "PacketSent destination=192.168.1.10 interface=eth0"
