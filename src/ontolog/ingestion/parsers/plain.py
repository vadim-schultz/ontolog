"""Plain-text log line parser."""

from __future__ import annotations

from ontolog.ingestion.parsers.base import build_log_record
from ontolog.models import LogRecord

__all__ = ["PlainParser"]


class PlainParser:
    """Parse unstructured lines where the entire line is the message body."""

    @property
    def name(self) -> str:
        """Return the parser identifier."""
        return "plain"

    def parse_line(self, line: str, *, line_number: int) -> LogRecord:
        """Treat the stripped line as the message body."""
        return build_log_record(
            line=line,
            line_number=line_number,
            message=line.strip(),
        )
