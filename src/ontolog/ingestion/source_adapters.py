"""Log source path resolution adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ontolog.errors import OntologError

__all__ = [
    "LOG_FILE_EXTENSIONS",
    "DirectorySourceAdapter",
    "FileSourceAdapter",
    "LogSourceResolver",
    "LogSourceResolverChain",
    "MissingSourceAdapter",
    "StdinSourceAdapter",
    "collect_directory_log_files",
    "default_log_source_resolver",
]

# Directory ingest: extensions aligned with syslog, plain, and JSON Lines parsers.
LOG_FILE_EXTENSIONS: tuple[str, ...] = (
    ".log",
    ".txt",
    ".jsonl",
    ".ndjson",
    ".json",
    ".out",
)


def collect_directory_log_files(
    directory: Path,
    *,
    extensions: tuple[str, ...] = LOG_FILE_EXTENSIONS,
) -> list[Path]:
    """Return sorted log files in ``directory`` matching ``extensions``."""
    files = [path for ext in extensions for path in directory.glob(f"*{ext}") if path.is_file()]
    return sorted(files, key=lambda path: path.name)


class LogSourceResolver(Protocol):
    """Adapter that resolves one kind of ingest source to readable paths."""

    def can_resolve(self, source: Path | str) -> bool:
        """Return True when this adapter handles ``source``."""

    def resolve(self, source: Path | str) -> list[Path]:
        """Resolve ``source`` to one or more readable log file paths."""


class LogSourceResolverChain:
    """Try registered adapters in order, then fall back to the null object."""

    def __init__(
        self,
        resolvers: tuple[LogSourceResolver, ...] | list[LogSourceResolver],
        *,
        fallback: LogSourceResolver,
    ) -> None:
        """Register resolvers to try in order plus a fallback."""
        self._resolvers = resolvers
        self._fallback = fallback

    def resolve(self, source: Path | str) -> list[Path]:
        """Resolve ``source`` with the first matching adapter."""
        for resolver in self._resolvers:
            if resolver.can_resolve(source):
                return resolver.resolve(source)
        return self._fallback.resolve(source)


class StdinSourceAdapter:
    """Resolve stdin sentinel ``"-"`` to a single pseudo-path."""

    def can_resolve(self, source: Path | str) -> bool:
        """Return True when ``source`` is the stdin sentinel ``"-"``."""
        return str(source) == "-"

    def resolve(self, source: Path | str) -> list[Path]:
        """Return a pseudo-path representing stdin."""
        return [Path("-")]


class DirectorySourceAdapter:
    """Resolve a directory to sorted log files with known extensions."""

    def __init__(self, *, extensions: tuple[str, ...] = LOG_FILE_EXTENSIONS) -> None:
        """Store filename extensions used when scanning directories."""
        self._extensions = extensions

    def can_resolve(self, source: Path | str) -> bool:
        """Return True when ``source`` is an existing directory."""
        if str(source) == "-":
            return False
        path = Path(source)
        return path.exists() and path.is_dir()

    def resolve(self, source: Path | str) -> list[Path]:
        """Return sorted log files under ``source``."""
        directory = Path(source)
        files = collect_directory_log_files(directory, extensions=self._extensions)
        if not files:
            extensions = ", ".join(self._extensions)
            msg = (
                f"no log files found in directory: {directory} (expected extensions: {extensions})"
            )
            raise OntologError(msg)
        return files


class FileSourceAdapter:
    """Resolve a single existing file path."""

    def can_resolve(self, source: Path | str) -> bool:
        """Return True when ``source`` is an existing file."""
        if str(source) == "-":
            return False
        path = Path(source)
        return path.exists() and path.is_file()

    def resolve(self, source: Path | str) -> list[Path]:
        """Return ``source`` as a single-element path list."""
        return [Path(source)]


class MissingSourceAdapter:
    """Null object adapter for sources that match no other resolver."""

    def can_resolve(self, source: Path | str) -> bool:
        """Return True for every source so the chain can raise :exc:`FileNotFoundError`."""
        return True

    def resolve(self, source: Path | str) -> list[Path]:
        """Raise :exc:`FileNotFoundError` when no resolver handles ``source``."""
        path = Path(source)
        msg = f"log source not found: {path}"
        raise FileNotFoundError(msg)


def default_log_source_resolver() -> LogSourceResolverChain:
    """Build the default chain of log source resolvers."""
    return LogSourceResolverChain(
        [
            StdinSourceAdapter(),
            DirectorySourceAdapter(),
            FileSourceAdapter(),
        ],
        fallback=MissingSourceAdapter(),
    )
