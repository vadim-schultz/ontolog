"""Tests for export type mapping."""

from __future__ import annotations

from ontolog.export.type_map import (
    json_schema_for,
    pydantic_names_for,
    python_field_type,
    python_imports_for,
    python_type_for,
)


def test_python_type_for_ipv4() -> None:
    assert python_type_for("ipv4") == "IPv4Address"


def test_python_type_for_email_and_url() -> None:
    assert python_type_for("email") == "EmailStr"
    assert python_type_for("url") == "AnyUrl"


def test_python_field_type_hex_uses_pattern() -> None:
    mapping = python_field_type("hex")
    assert mapping.annotation == "str"
    assert mapping.field_pattern is not None


def test_python_imports_for_ipv4_and_uuid() -> None:
    imports = python_imports_for({"ipv4", "uuid"})
    assert "from ipaddress import IPv4Address" in imports
    assert "from uuid import UUID" in imports


def test_pydantic_names_for_email_and_url() -> None:
    names = pydantic_names_for({"email", "url"})
    assert names == ("AnyUrl", "EmailStr")


def test_json_schema_for_hex_includes_pattern() -> None:
    schema = json_schema_for("hex")
    assert schema["type"] == "string"
    assert "pattern" in schema


def test_unknown_slug_falls_back_to_string() -> None:
    assert python_type_for("custom_type") == "str"
    assert json_schema_for("custom_type") == {"type": "string"}
