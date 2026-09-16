from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Callable


class ProductionHarnessAdapter:
    """Adapter for the existing AIAS `harness_gate_executor.py`.

    Supported legacy contracts:
      1. enforce_gates(model_output: dict) -> dict
      2. enforce(model_output: dict, context: dict) -> dict

    This module deliberately does not reimplement G0-G13; it delegates to the
    controlled AIAS harness supplied at deployment time.
    """

    def __init__(self, harness_path: str) -> None:
        path = Path(harness_path)
        if not path.exists():
            raise FileNotFoundError(path)
        spec = importlib.util.spec_from_file_location("aias_legacy_harness", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load harness: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self._enforce_gates: Callable | None = getattr(module, "enforce_gates", None)
        self._enforce: Callable | None = getattr(module, "enforce", None)
        if self._enforce_gates is None and self._enforce is None:
            raise AttributeError("legacy harness must expose enforce_gates() or enforce()")

    def enforce(self, candidate: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        if self._enforce is not None:
            return self._enforce(candidate, context)
        assert self._enforce_gates is not None
        result = self._enforce_gates(candidate)
        if isinstance(result, dict):
            result.setdefault("world_context", context)
        return result
