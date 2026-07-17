"""Evidence provider registry and shared constants."""

from __future__ import annotations

from ontolog.config import ProviderConfig, ProviderKind
from ontolog.providers.co_occurrence import CoOccurrenceProvider
from ontolog.providers.namespace import NamespaceProvider
from ontolog.providers.process import ProcessProvider
from ontolog.providers.regex import RegexProvider
from ontolog.providers.statistics import StatisticsProvider
from ontolog.providers.temporal import TemporalProvider
from ontolog.types import EvidenceProvider

DEFAULT_PROVIDER_ORDER: tuple[ProviderKind, ...] = (
    ProviderKind.NAMESPACE,
    ProviderKind.REGEX,
    ProviderKind.STATISTICS,
    ProviderKind.CO_OCCURRENCE,
    ProviderKind.TEMPORAL,
    ProviderKind.PROCESS,
)

_PROVIDER_FACTORIES: dict[ProviderKind, type[EvidenceProvider]] = {
    ProviderKind.REGEX: RegexProvider,
    ProviderKind.STATISTICS: StatisticsProvider,
    ProviderKind.CO_OCCURRENCE: CoOccurrenceProvider,
    ProviderKind.NAMESPACE: NamespaceProvider,
    ProviderKind.TEMPORAL: TemporalProvider,
    ProviderKind.PROCESS: ProcessProvider,
}


def provider_registry(config: ProviderConfig) -> tuple[EvidenceProvider, ...]:
    """Return enabled providers in default execution order."""
    providers: list[EvidenceProvider] = []
    for kind in DEFAULT_PROVIDER_ORDER:
        if kind not in config.enabled:
            continue
        providers.append(_PROVIDER_FACTORIES[kind]())
    return tuple(providers)
