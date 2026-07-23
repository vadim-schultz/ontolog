"""Generate StrEnum source for enum-typed fields."""

from __future__ import annotations

from ontolog.enum_slug import enum_values_from_slug


def enum_class_name(entity_name: str) -> str:
    """Return the generated enum class name for ``entity_name``."""
    return f"{entity_name.replace(' ', '')}Status"


def enum_member_name(value: str) -> str:
    """Return a valid Python identifier for enum member ``value``."""
    return value.upper().replace("-", "_")


def enum_class_source(class_name: str, type_slug: str) -> str:
    """Return StrEnum class source for ``type_slug``."""
    members = enum_values_from_slug(type_slug)
    lines = [
        f"class {class_name}(StrEnum):",
        f'    """Lifecycle status values for {class_name.removesuffix("Status")}."""',
        "",
    ]
    for value in members:
        lines.append(f'    {enum_member_name(value)} = "{value}"')
    return "\n".join(lines)
