# Log ingestion

Ontolog normalizes raw logs into :class:`~ontolog.models.LogRecord` streams before
template extraction and inference.

## Supported formats

| CLI `--format` | Description | Examples |
|----------------|-------------|----------|
| `syslog` | RFC3164, ISO8601 syslog, Apache error brackets | OpenSSH, controlboard fixture |
| `json` | JSON Lines (one object per line) | Generic JSONL, journald, structlog `JSONRenderer` |
| `plain` | Entire line becomes `message` | Unstructured text, structlog console/logfmt output |
| `auto` | Sample first 20 lines and detect (default) | Mixed directories |

### JSONL dialects (`--format json`)

| Dialect | Message field | Notes |
|---------|---------------|-------|
| Generic | `message`, `msg`, `@message` | Common app logging |
| journald | `MESSAGE`, `_HOSTNAME`, `PRIORITY` | `journalctl -o json` export |
| [structlog](https://www.structlog.org/en/stable/index.html) | `event` | `JSONRenderer` output; not a runtime dependency |

structlog **ConsoleRenderer** and **LogfmtRenderer** are plain text — use `--format plain`.

## CLI

```bash
ontolog ingest PATH [--format syslog|json|plain|auto] [--preprocessor NAME]... [--skip-errors] [--limit N]
```

`PATH` may be a file, a directory of log files (`.log`, `.txt`, `.jsonl`, `.ndjson`,
`.json`, `.out`), or `-` for stdin. Output is JSON
Lines on stdout (one `LogRecord` per line).

## Python API

```python
from ontolog.ingestion import IngestOptions, LogFormat, ingest_path

for record in ingest_path("app.log", IngestOptions(format=LogFormat.AUTO)):
    print(record.message)
```

## Custom preprocessors

Register org-specific line transforms without forking parsers:

```python
from ontolog.ingestion import default_preprocessor_registry
from ontolog.ingestion.reader import ingest_path


class StripK8sPrefix:
    @property
    def name(self) -> str:
        return "strip_k8s"

    def process(self, line: str, *, line_number: int) -> str:
        return line.split("|", 1)[-1]


registry = default_preprocessor_registry()
registry.register(StripK8sPrefix())

for record in ingest_path("pod.log", registry=registry):
    ...
```

CLI: append preprocessors after the built-in `strip` step:

```bash
ontolog ingest app.log --preprocessor strip_k8s
```

## Fixtures

Committed corpora live under `tests/fixtures/`. LogHub slice provenance and citation
requirements are documented in `tests/fixtures/loghub/README.md`.
