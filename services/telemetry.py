"""Lightweight metrics — Prometheus text format + request timing."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class MetricCounter:
    value: float = 0.0
    labels: dict[str, str] = field(default_factory=dict)


class MetricsRegistry:
    """In-memory metrics registry (Prometheus exposition format)."""

    def __init__(self) -> None:
        self._counters: dict[str, float] = defaultdict(float)
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def inc(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        key = self._label_key(name, labels)
        with self._lock:
            self._counters[key] += value

    def observe(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._label_key(name, labels)
        with self._lock:
            bucket = self._histograms[key]
            bucket.append(value)
            if len(bucket) > 1000:
                self._histograms[key] = bucket[-500:]

    def _label_key(self, name: str, labels: dict[str, str] | None) -> str:
        if not labels:
            return name
        parts = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{parts}}}"

    def render_prometheus(self) -> str:
        lines: list[str] = []
        with self._lock:
            for key, val in sorted(self._counters.items()):
                metric_name = key.split("{")[0]
                lines.append(f"# TYPE {metric_name} counter")
                lines.append(f"{key} {val}")
            for key, vals in sorted(self._histograms.items()):
                if not vals:
                    continue
                metric_name = key.split("{")[0]
                lines.append(f"# TYPE {metric_name}_sum gauge")
                lines.append(f"{key}_sum {sum(vals)}")
                lines.append(f"# TYPE {metric_name}_count gauge")
                lines.append(f"{key}_count {len(vals)}")
                sorted_vals = sorted(vals)
                p95_idx = int(len(sorted_vals) * 0.95)
                lines.append(f"# TYPE {metric_name}_p95 gauge")
                lines.append(f"{key}_p95 {sorted_vals[min(p95_idx, len(sorted_vals) - 1)]}")
        return "\n".join(lines) + "\n"

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "histogram_counts": {k: len(v) for k, v in self._histograms.items()},
            }


metrics = MetricsRegistry()


class RequestTimer:
    """Context manager for timing API/agent calls."""

    def __init__(self, metric_name: str, labels: dict[str, str] | None = None) -> None:
        self._metric = metric_name
        self._labels = labels
        self._start = 0.0

    def __enter__(self) -> "RequestTimer":
        self._start = time.monotonic()
        return self

    def __exit__(self, *args: object) -> None:
        elapsed_ms = (time.monotonic() - self._start) * 1000
        metrics.observe(self._metric, elapsed_ms, self._labels)
