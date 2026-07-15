"""Tests for ontolog.errors."""

from __future__ import annotations

import ontolog
from ontolog.errors import OntologError, ParseError


def test_hierarchy() -> None:
    assert issubclass(ParseError, OntologError)
    assert issubclass(OntologError, Exception)
    assert issubclass(ontolog.ParseError, ontolog.OntologError)


def test_parse_error_attrs() -> None:
    error = ParseError("bad line", line="foo", line_number=42)
    assert str(error) == "bad line"
    assert error.line == "foo"
    assert error.line_number == 42
