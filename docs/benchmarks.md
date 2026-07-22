# Benchmarks

Ontolog benchmarks use committed LogHub 2k fixtures for fast, reproducible runs. Larger
corpora can be downloaded with `scripts/fetch_corpora.py` for integration and nightly jobs.

## Citation

LogHub datasets are from [LogHub](https://github.com/logpai/loghub) (Zenodo
[8196385](https://zenodo.org/records/8196385)). Template labels come from
[LogHub-2.0](https://github.com/logpai/loghub-2.0) (Zenodo
[8275861](https://zenodo.org/record/8275861)).

## Template Accuracy

Measured against LogHub-2.0 2k datasets (pairwise clustering F1):

| Dataset | Precision | Recall | F1 |
|---------|-----------|--------|-----|
| Apache | 1.000 | 1.000 | 1.000 |
| OpenSSH | 0.995 | 1.000 | 0.998 |

## Template Throughput

Measured on committed fixtures (Python 3.11, single-threaded, batched SQLite writes):

| Fixture | Lines/sec | Templates | Time |
|---------|-----------|-----------|------|
| controlboard.log | 511 | 3 | 0.12s |
| apache_2k.log | 932 | 6 | 2.15s |

## Inference Latency

Measured on committed fixtures (Python 3.11):

| Fixture | Total | Entities | Events |
|---------|-------|----------|--------|
| controlboard.log | 117ms | 0 | 3 |
| order_lifecycle.log | 35ms | 0 | 4 |

Entity counts reflect export eligibility thresholds in the default configuration.
