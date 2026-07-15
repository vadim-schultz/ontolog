"""Tests for preprocessor registry."""

from __future__ import annotations

import pytest

from ontolog.errors import ConfigError
from ontolog.ingestion.preprocessors import PreprocessorRegistry, default_preprocessor_registry


class _PrefixStripper:
    @property
    def name(self) -> str:
        return "strip_prefix"

    def process(self, line: str, *, line_number: int) -> str:
        return line.removeprefix("k8s|")


def test_default_chain_strips_whitespace() -> None:
    registry = default_preprocessor_registry()
    assert registry.apply("  hello  ", line_number=1) == "hello"


def test_custom_chain_order() -> None:
    registry = default_preprocessor_registry()
    registry.register(_PrefixStripper())

    result = registry.apply(
        "  k8s|payload  ",
        line_number=1,
        chain=("strip_prefix", "squash_whitespace"),
    )
    assert result == "payload"


def test_unknown_preprocessor_raises() -> None:
    registry = PreprocessorRegistry()
    with pytest.raises(ConfigError, match="unknown preprocessor"):
        registry.get("missing")


def test_drop_utf8_bom() -> None:
    registry = default_preprocessor_registry()
    result = registry.apply("\ufeffhello", line_number=1, chain=("drop_utf8_bom",))
    assert result == "hello"


def test_register_custom_preprocessor() -> None:
    registry = default_preprocessor_registry()
    registry.register(_PrefixStripper())
    preprocessor = registry.get("strip_prefix")
    assert preprocessor.process("k8s|x", line_number=1) == "x"
