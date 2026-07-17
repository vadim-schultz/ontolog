"""Domain inference from evidence graphs."""

from ontolog.inference.base import DEFAULT_INFERENCE_ORDER, inference_registry
from ontolog.inference.builder import build_inference_result
from ontolog.inference.runner import run_inference

__all__ = [
    "DEFAULT_INFERENCE_ORDER",
    "build_inference_result",
    "inference_registry",
    "run_inference",
]
