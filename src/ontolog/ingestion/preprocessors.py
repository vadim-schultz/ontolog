"""Preprocessor registry for org-specific log pipelines."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from ontolog.errors import ConfigError
from ontolog.types import Preprocessor

__all__ = ["PreprocessorRegistry", "default_preprocessor_registry"]

_WHITESPACE_RUN = re.compile(r"[ \t]+")


@dataclass(frozen=True, slots=True)
class _StripPreprocessor:
    @property
    def name(self) -> str:
        return "strip"

    def process(self, line: str, *, line_number: int) -> str:
        return line.strip()


@dataclass(frozen=True, slots=True)
class _DropUtf8BomPreprocessor:
    @property
    def name(self) -> str:
        return "drop_utf8_bom"

    def process(self, line: str, *, line_number: int) -> str:
        if line.startswith("\ufeff"):
            return line[1:]
        return line


@dataclass(frozen=True, slots=True)
class _SquashWhitespacePreprocessor:
    @property
    def name(self) -> str:
        return "squash_whitespace"

    def process(self, line: str, *, line_number: int) -> str:
        return _WHITESPACE_RUN.sub(" ", line)


class PreprocessorRegistry:
    """Named preprocessors and ordered application chains."""

    def __init__(
        self,
        *,
        default_chain: Sequence[str] = ("strip",),
        **preprocessors: Preprocessor,
    ) -> None:
        """Register preprocessors and the default application order."""
        self._preprocessors: dict[str, Preprocessor] = dict(preprocessors)
        self._default_chain = tuple(default_chain)

    def register(self, preprocessor: Preprocessor) -> None:
        """Register or replace a preprocessor by name."""
        self._preprocessors[preprocessor.name] = preprocessor

    def get(self, name: str) -> Preprocessor:
        """Return the preprocessor for ``name``."""
        try:
            return self._preprocessors[name]
        except KeyError as exc:
            msg = f"unknown preprocessor: {name}"
            raise ConfigError(msg) from exc

    def apply(
        self,
        line: str,
        *,
        line_number: int,
        chain: Sequence[str] | None = None,
    ) -> str:
        """Apply the preprocessor chain to ``line``."""
        selected = self._default_chain if chain is None else ("strip", *chain)
        result = line
        seen: set[str] = set()
        for name in selected:
            if name in seen:
                continue
            seen.add(name)
            result = self.get(name).process(result, line_number=line_number)
        return result


def default_preprocessor_registry() -> PreprocessorRegistry:
    """Return a registry with built-in preprocessors."""
    return PreprocessorRegistry(
        strip=_StripPreprocessor(),
        drop_utf8_bom=_DropUtf8BomPreprocessor(),
        squash_whitespace=_SquashWhitespacePreprocessor(),
    )
