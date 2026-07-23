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

The public CLI exposes a single command: `ontolog infer PATH --format EXPORT`. The library entry
point is `ontolog.infer()`, which runs ingestion, template extraction, inference, and export in one
ephemeral pass. See {doc}`export` and {doc}`architecture`.

## Verify installation

```python
import ontolog

print(ontolog.__version__)
```
