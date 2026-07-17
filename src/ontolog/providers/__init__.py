"""Deterministic evidence providers."""

from ontolog.providers.base import DEFAULT_PROVIDER_ORDER, provider_registry
from ontolog.providers.co_occurrence import CoOccurrenceProvider
from ontolog.providers.namespace import NamespaceProvider
from ontolog.providers.process import ProcessProvider
from ontolog.providers.regex import RegexProvider
from ontolog.providers.statistics import StatisticsProvider
from ontolog.providers.temporal import TemporalProvider

__all__ = [
    "DEFAULT_PROVIDER_ORDER",
    "CoOccurrenceProvider",
    "NamespaceProvider",
    "ProcessProvider",
    "RegexProvider",
    "StatisticsProvider",
    "TemporalProvider",
    "provider_registry",
]
