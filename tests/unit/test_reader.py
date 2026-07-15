"""Tests for streaming reader."""

from __future__ import annotations

import io
import sys

import pytest

from ontolog.errors import ParseError
from ontolog.ingestion import IngestOptions, LogFormat, ingest_path, iter_records


def test_stdin_ingest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("plain stdin line\n"))
    records = list(
        iter_records("-", IngestOptions(format=LogFormat.PLAIN)),
    )
    assert len(records) == 1
    assert records[0].message == "plain stdin line"


def test_directory_ingest(tmp_path) -> None:
    (tmp_path / "a.log").write_text("alpha\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("beta\n", encoding="utf-8")
    (tmp_path / "c.jsonl").write_text('{"message": "gamma"}\n', encoding="utf-8")
    (tmp_path / "ignore.md").write_text("ignored\n", encoding="utf-8")

    records = list(
        iter_records(tmp_path, IngestOptions(format=LogFormat.PLAIN)),
    )
    assert [record.message for record in records] == ["alpha", "beta", '{"message": "gamma"}']


def test_limit_stops_after_n_records(tmp_path) -> None:
    log_file = tmp_path / "many.log"
    log_file.write_text("one\n two\n three\n", encoding="utf-8")

    records = list(
        iter_records(
            log_file,
            IngestOptions(format=LogFormat.PLAIN, limit=2),
        )
    )
    assert len(records) == 2


def test_skip_errors_continues(tmp_path) -> None:
    log_file = tmp_path / "mixed.log"
    log_file.write_text(
        "Dec 10 06:55:46 LabSZ sshd[1]: ok\nbad syslog\nDec 10 06:55:47 LabSZ sshd[2]: also ok\n",
        encoding="utf-8",
    )

    records = list(
        iter_records(
            log_file,
            IngestOptions(format=LogFormat.SYSLOG, skip_errors=True),
        )
    )
    assert len(records) == 2
    assert records[0].pid == 1
    assert records[1].pid == 2


def test_parse_error_aborts_by_default(tmp_path) -> None:
    log_file = tmp_path / "bad.log"
    log_file.write_text("not syslog\n", encoding="utf-8")

    with pytest.raises(ParseError):
        list(iter_records(log_file, IngestOptions(format=LogFormat.SYSLOG)))


def test_per_file_line_numbers(tmp_path) -> None:
    first = tmp_path / "first.log"
    second = tmp_path / "second.log"
    first.write_text("bad\n", encoding="utf-8")
    second.write_text("also bad\n", encoding="utf-8")

    with pytest.raises(ParseError) as exc_info:
        list(iter_records(tmp_path, IngestOptions(format=LogFormat.SYSLOG)))

    assert exc_info.value.line_number == 1


def test_ingest_path_public_api(tmp_path) -> None:
    log_file = tmp_path / "one.log"
    log_file.write_text("hello\n", encoding="utf-8")

    records = list(ingest_path(log_file, IngestOptions(format=LogFormat.PLAIN)))
    assert records[0].message == "hello"
