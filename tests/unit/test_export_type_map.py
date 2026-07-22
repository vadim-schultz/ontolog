"""Tests for export type mapping."""

from __future__ import annotations

from ontolog.export.type_map import (
    json_schema_for,
    pydantic_names_for,
    python_field_type,
    python_imports_for,
    python_type_for,
    type_description_for,
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


def test_python_field_type_int() -> None:
    assert python_type_for("int") == "int"
    assert type_description_for("int") == "integer"


def test_python_field_type_float() -> None:
    assert python_type_for("float") == "float"
    assert type_description_for("float") == "floating-point number"


def test_python_field_type_bool() -> None:
    assert python_type_for("bool") == "bool"
    assert type_description_for("bool") == "boolean"


def test_json_schema_for_int() -> None:
    assert json_schema_for("int") == {"type": "integer"}
