"""Map inferred type slugs to Python and JSON Schema representations."""

from __future__ import annotations

from dataclasses import dataclass

_JSON_SCHEMA_STRING: dict[str, object] = {"type": "string"}

_TYPE_JSON_SCHEMA: dict[str, dict[str, object]] = {
    "int": {"type": "integer"},
    "float": {"type": "number"},
    "bool": {"type": "boolean"},
    "ipv4": {"type": "string", "format": "ipv4"},
    "hex": {"type": "string", "pattern": "^[0-9a-fA-F]+$"},
    "uuid": {"type": "string", "format": "uuid"},
    "mac": {"type": "string", "format": "mac"},
    "email": {"type": "string", "format": "email"},
    "url": {"type": "string", "format": "uri"},
    "path": {"type": "string", "format": "path"},
}

_DEFAULT_PYTHON = "str"


@dataclass(frozen=True)
class PythonFieldType:
    """Python annotation and imports for a generated Pydantic field."""

    annotation: str
    stdlib_imports: tuple[str, ...] = ()
    pydantic_names: tuple[str, ...] = ()
    field_pattern: str | None = None


_TYPE_PYTHON: dict[str, PythonFieldType] = {
    "int": PythonFieldType("int"),
    "float": PythonFieldType("float"),
    "bool": PythonFieldType("bool"),
    "ipv4": PythonFieldType(
        "IPv4Address",
        stdlib_imports=("from ipaddress import IPv4Address",),
    ),
    "hex": PythonFieldType(
        "str",
        field_pattern=r"^[0-9a-fA-F]+$",
    ),
    "uuid": PythonFieldType(
        "UUID",
        stdlib_imports=("from uuid import UUID",),
    ),
    "mac": PythonFieldType(
        "str",
        field_pattern=r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$",
    ),
    "email": PythonFieldType(
        "EmailStr",
        pydantic_names=("EmailStr",),
    ),
    "url": PythonFieldType(
        "AnyUrl",
        pydantic_names=("AnyUrl",),
    ),
    "path": PythonFieldType(
        "Path",
        stdlib_imports=("from pathlib import Path",),
    ),
}

_TYPE_DESCRIPTIONS: dict[str, str] = {
    "int": "integer",
    "float": "floating-point number",
    "bool": "boolean",
    "ipv4": "IPv4 address",
    "hex": "hexadecimal string",
    "uuid": "UUID",
    "mac": "MAC address",
    "email": "email address",
    "url": "URL",
    "path": "filesystem path",
}


def python_field_type(type_slug: str) -> PythonFieldType:
    """Return the generated-field mapping for ``type_slug``."""
    return _TYPE_PYTHON.get(type_slug, PythonFieldType(_DEFAULT_PYTHON))


def python_type_for(type_slug: str) -> str:
    """Return a Python annotation string for ``type_slug``."""
    return python_field_type(type_slug).annotation


def python_imports_for(type_slugs: set[str]) -> tuple[str, ...]:
    """Return sorted stdlib import lines required for ``type_slugs``."""
    imports: set[str] = set()
    for slug in type_slugs:
        imports.update(python_field_type(slug).stdlib_imports)
    return tuple(sorted(imports))


def pydantic_names_for(type_slugs: set[str]) -> tuple[str, ...]:
    """Return sorted extra Pydantic types to import for ``type_slugs``."""
    names: set[str] = set()
    for slug in type_slugs:
        names.update(python_field_type(slug).pydantic_names)
    return tuple(sorted(names))


def type_description_for(type_slug: str) -> str:
    """Return a human-readable description for ``type_slug``."""
    if type_slug.startswith("enum:"):
        return "lifecycle status"
    return _TYPE_DESCRIPTIONS.get(type_slug, type_slug)


def json_schema_for(type_slug: str) -> dict[str, object]:
    """Return a JSON Schema fragment for ``type_slug``."""
    return dict(_TYPE_JSON_SCHEMA.get(type_slug, _JSON_SCHEMA_STRING))
