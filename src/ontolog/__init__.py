"""Ontolog — probabilistic domain-model inference from application logs."""

from ontolog.config import OntologConfig, default_config
from ontolog.errors import ConfigError, OntologError, ParseError, TemplateError
from ontolog.models import LogRecord

__version__ = "0.0.1"

__all__ = [
    "ConfigError",
    "LogRecord",
    "OntologConfig",
    "OntologError",
    "ParseError",
    "TemplateError",
    "__version__",
    "default_config",
]
