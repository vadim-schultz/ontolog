"""Tests for export field identifier helpers."""

from __future__ import annotations

from ontolog.identifiers import is_valid_field_name, to_python_identifier


def test_is_valid_field_name_rejects_star() -> None:
    assert not is_valid_field_name("*")


def test_sanitize_field_name_star() -> None:
    assert to_python_identifier("*") is None


def test_is_valid_field_name_accepts_rhost() -> None:
    assert is_valid_field_name("rhost")
    assert to_python_identifier("rhost") == "rhost"


def test_to_python_identifier_reserved_word() -> None:
    assert to_python_identifier("class") == "class_"
