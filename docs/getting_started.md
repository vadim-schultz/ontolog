# Getting started

## Install

```bash
pip install ontolog
```

## Editable install (development)

```bash
git clone https://github.com/vadim-schultz/ontolog.git
cd ontolog
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Current status

Chapter 0 provides the package skeleton, test harness, and CI/CD baseline. The inference pipeline
(`ontolog ingest`, `ontolog infer`, exporters) arrives in Chapters 1–9 per
{doc}`architecture`.

## Verify installation

```python
import ontolog

print(ontolog.__version__)
```
