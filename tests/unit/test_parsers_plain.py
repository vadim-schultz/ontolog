"""Tests for plain-text parser."""

from __future__ import annotations

from ontolog.ingestion.formats import LogFormat
from ontolog.ingestion.parsers.plain import PlainParser
from ontolog.ingestion.reader import IngestOptions, iter_records


def test_whole_line_becomes_message() -> None:
    line = "  unstructured application log line  "
    record = PlainParser().parse_line(line, line_number=1)

    assert record.message == "unstructured application log line"
    assert record.hostname is None
    assert record.timestamp is None


def test_blank_lines_skipped_by_reader(tmp_path) -> None:
    log_file = tmp_path / "plain.log"
    log_file.write_text("first line\n\n   \nsecond line\n", encoding="utf-8")

    records = list(
        iter_records(
            log_file,
            IngestOptions(format=LogFormat.PLAIN),
        )
    )

    assert [record.message for record in records] == ["first line", "second line"]
