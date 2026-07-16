# Template extraction

Chapter 3 compresses normalized log messages into stable, parameterized templates using
[Drain3](https://github.com/logpai/Drain3). Templates are the semantic boundary between raw logs
and downstream evidence/inference (Chapter 4+).

## Pipeline position

```text
ingest_path() → LogRecord.message → TemplateExtractor (Drain3) → Template → SQLite store
```

## Mask kinds

Masking is configured via `OntologConfig.masks` (`MaskConfig.enabled`). Each enabled `MaskKind`
becomes a Drain3 masking instruction:

| Kind | Placeholder | Example |
|------|-------------|---------|
| `ip` | `<IP>` | `192.168.1.10` |
| `uuid` | `<UUID>` | RFC 4122 UUIDs |
| `mac` | `<MAC>` | `aa:bb:cc:dd:ee:ff` |
| `hex` | `<HEX>` | `0xdeadbeef` |
| `email` | `<EMAIL>` | `user@example.com` |
| `number` | `<NUMBER>` | standalone integers/floats |
| `timestamp` | `<TIMESTAMP>` | ISO-8601 timestamps |

All mask kinds are enabled by default. Disable kinds by passing a subset to `MaskConfig`.

## Python API

```python
from pathlib import Path

from ontolog.storage import SqliteTemplateStore
from ontolog.templates import ExtractOptions, extract_templates

templates = extract_templates(
    Path("tests/fixtures/controlboard.log"),
    ExtractOptions(),
)
for template in templates:
    print(template.id, template.occurrence_count, template.template)
```

Persist templates across runs:

```python
store = SqliteTemplateStore(Path("ontolog.db"))
templates = extract_templates(
    Path("tests/fixtures/controlboard.log"),
    ExtractOptions(),
    store=store,
)
store.close()
```

## CLI

```bash
# Summary table on stdout; status on stderr
ontolog templates tests/fixtures/controlboard.log

# Persist to SQLite (default: ontolog.db)
ontolog templates tests/fixtures/controlboard.log --store my.db

# In-memory only
ontolog templates tests/fixtures/controlboard.log --no-store
```

Ingest options (`--format`, `--skip-errors`, `--limit`, `--preprocessor`) are also supported.

## SQLite schema

| Table | Purpose |
|-------|---------|
| `templates` | Template catalog (`id`, `template`, `occurrence_count`, timestamps, `examples` JSON) |
| `template_occurrences` | Per-message rows with extracted parameters JSON |

Schema version is tracked via `PRAGMA user_version = 1`.
