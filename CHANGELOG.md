# Changelog

## Unreleased

### Added

* Template extraction via Drain3 (`TemplateExtractor`, `extract_templates`)
* Configurable masking (IP, UUID, MAC, hex, email, numbers, timestamps)
* `Template` model and SQLite persistence (`templates`, `template_occurrences`)
* `ontolog templates` CLI with Rich summary table
* Log ingestion: syslog, JSONL, and plain parsers
* Preprocessor registry and streaming reader (file, directory, stdin)
* `ontolog ingest` CLI command (JSONL output)
* Fixtures: `controlboard.log`, LogHub `apache_2k` / `openssh_2k` slices
* `LogRecord` model, `OntologConfig`, typed exceptions
* `ontolog` CLI with `--version` and `--help`
* Project scaffold (Chapter 0): `src/ontolog` package, pytest harness, Sphinx docs stub, GitHub
  Actions CI (ruff, mypy, pytest, docs build, wheel smoke test), Read the Docs config,
  pre-commit hooks, and unified implementation plan.

## 0.0.1 — 2026-07-14

### Added

* Initial package skeleton and engineering baseline.
