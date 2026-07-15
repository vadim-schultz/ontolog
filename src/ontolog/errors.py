"""Exceptions raised by ontolog."""


class OntologError(Exception):
    """Base class for ontolog errors."""


class ParseError(OntologError):
    """Raised when a raw log line cannot be parsed."""

    def __init__(
        self,
        message: str,
        *,
        line: str | None = None,
        line_number: int | None = None,
    ) -> None:
        super().__init__(message)
        self.line = line
        self.line_number = line_number


class TemplateError(OntologError):
    """Raised when template extraction or storage fails."""


class ConfigError(OntologError):
    """Raised when configuration is invalid."""


class StorageError(OntologError):
    """Raised when persistence operations fail."""


class InferenceError(OntologError):
    """Raised when the inference pipeline fails."""


class ExportError(OntologError):
    """Raised when model export fails."""
