"""Tests for ontolog.models.log_record."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ontolog.models import LogRecord


def test_construct_minimal() -> None:
    record = LogRecord(message="hello")
    assert record.message == "hello"
    assert record.timestamp is None
    assert record.hostname is None
    assert record.process is None
    assert record.pid is None
    assert record.level is None
    assert record.logger is None


def test_construct_full() -> None:
    timestamp = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
    record = LogRecord(
        timestamp=timestamp,
        hostname="host1",
        process="sshd",
        pid=1234,
        level="info",
        logger="auth",
        message="Accepted publickey",
    )
    assert record.timestamp == timestamp
    assert record.hostname == "host1"
    assert record.process == "sshd"
    assert record.pid == 1234
    assert record.level == "INFO"
    assert record.logger == "auth"
    assert record.message == "Accepted publickey"


def test_pid_validation() -> None:
    with pytest.raises(ValidationError):
        LogRecord(message="hello", pid=0)


def test_frozen() -> None:
    record = LogRecord(message="hello")
    with pytest.raises(ValidationError):
        record.message = "changed"  # type: ignore[misc]


def test_json_round_trip() -> None:
    timestamp = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
    original = LogRecord(
        timestamp=timestamp,
        hostname="host1",
        process="sshd",
        pid=1234,
        level="INFO",
        logger="auth",
        message="Accepted publickey",
    )
    restored = LogRecord.model_validate_json(original.model_dump_json())
    assert restored == original


def test_extra_forbidden() -> None:
    with pytest.raises(ValidationError):
        LogRecord(message="hello", unknown="field")  # type: ignore[call-arg]


def test_empty_strings_coerced_to_none() -> None:
    record = LogRecord(message="hello", hostname="  ", level="")
    assert record.hostname is None
    assert record.level is None
