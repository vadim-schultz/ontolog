"""Tests for syslog parser."""

from __future__ import annotations

import pytest

from ontolog.errors import ParseError
from ontolog.ingestion.parsers.syslog import SyslogParser

OPENSSH_LINE = (
    "Dec 10 06:55:46 LabSZ sshd[24200]: reverse mapping checking getaddrinfo "
    "for ns.example.com [173.234.31.186] failed - POSSIBLE BREAK-IN ATTEMPT!"
)
CONTROLBOARD_LINE = (
    "2024-01-15T12:00:01.123Z cb-host controlboard[1001]: INFO "
    "PacketSent interface=eth0 destination=192.168.1.10 payload=0xdeadbeef"
)
APACHE_LINE = (
    "[Sun Dec 04 04:47:44 2005] [notice] workerEnv.init() ok /etc/httpd/conf/workers2.properties"
)


def test_parse_rfc3164_openssh() -> None:
    parser = SyslogParser()
    record = parser.parse_line(OPENSSH_LINE, line_number=1)

    assert record.hostname == "LabSZ"
    assert record.process == "sshd"
    assert record.pid == 24200
    assert record.level is None
    assert "reverse mapping" in record.message
    assert "LabSZ" not in record.message
    assert "24200" not in record.message


def test_parse_iso8601_controlboard() -> None:
    parser = SyslogParser()
    record = parser.parse_line(CONTROLBOARD_LINE, line_number=1)

    assert record.hostname == "cb-host"
    assert record.process == "controlboard"
    assert record.pid == 1001
    assert record.level == "INFO"
    assert record.message.startswith("PacketSent")
    assert "cb-host" not in record.message


def test_parse_apache_bracket() -> None:
    parser = SyslogParser()
    record = parser.parse_line(APACHE_LINE, line_number=1)

    assert record.process == "apache"
    assert record.level == "NOTICE"
    assert record.message.startswith("workerEnv.init()")
    assert not record.message.startswith("[")


def test_malformed_line_raises() -> None:
    parser = SyslogParser()
    with pytest.raises(ParseError, match="unrecognized syslog line"):
        parser.parse_line("not a syslog line", line_number=7)
