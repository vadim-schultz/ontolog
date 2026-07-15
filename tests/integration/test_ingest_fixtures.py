"""Integration tests for fixture ingestion."""

from __future__ import annotations

from pathlib import Path

from ontolog.ingestion import IngestOptions, LogFormat, ingest_path

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _count_lines(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def test_controlboard_fixture() -> None:
    records = list(ingest_path(FIXTURES / "controlboard.log"))

    assert len(records) >= 50
    assert all(record.message for record in records)
    assert all(record.process == "controlboard" for record in records)
    assert all("cb-host" not in record.message for record in records)


def test_openssh_loghub_slice() -> None:
    path = FIXTURES / "loghub" / "openssh_2k.log"
    records = list(ingest_path(path, IngestOptions(format=LogFormat.SYSLOG)))

    assert len(records) == _count_lines(path)
    assert all(record.process == "sshd" for record in records)
    assert all(record.pid is not None and record.pid >= 1 for record in records)


def test_apache_loghub_slice() -> None:
    path = FIXTURES / "loghub" / "apache_2k.log"
    records = list(ingest_path(path, IngestOptions(format=LogFormat.SYSLOG)))
    allowed_levels = {"NOTICE", "ERROR", "WARN", "WARNING", "INFO", "DEBUG", "CRIT", "ALERT"}

    assert len(records) == _count_lines(path)
    assert all(record.process == "apache" for record in records)
    assert all(record.level in allowed_levels for record in records)
    assert all(record.timestamp is not None for record in records)


def test_sample_jsonl_fixture() -> None:
    records = list(
        ingest_path(
            FIXTURES / "sample.jsonl",
            IngestOptions(format=LogFormat.JSON),
        )
    )

    assert len(records) == 6
    assert records[0].message == "service started"
    assert records[0].hostname == "app-01"
    assert records[1].hostname == "edge-01"
    assert records[2].message == "PacketSent"
    assert records[3].level == "WARNING"
