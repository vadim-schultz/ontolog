# Benchmarks

Performance and accuracy measurements. See [`docs/benchmarks.md`](../docs/benchmarks.md) for baseline results.

- [`template_accuracy.py`](template_accuracy.py) — F1 vs LogHub-2.0 labels
- [`template_throughput.py`](template_throughput.py) — Lines/sec and templates/sec
- [`inference_latency.py`](inference_latency.py) — End-to-end timing

Run from the repository root:

```bash
python benchmarks/template_throughput.py
python benchmarks/inference_latency.py
python benchmarks/template_accuracy.py
```
