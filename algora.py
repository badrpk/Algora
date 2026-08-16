from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from json import dumps
from math import isfinite
from typing import Callable, Dict, Iterable, List, Mapping, Sequence


@dataclass(frozen=True)
class Benchmark:
    latency_ms: float
    memory_mb: float
    accuracy: float = 1.0
    cost: float = 0.0

    def __post_init__(self) -> None:
        if self.latency_ms < 0 or self.memory_mb < 0 or self.cost < 0:
            raise ValueError("benchmark metrics must be non-negative")
        if not 0 <= self.accuracy <= 1:
            raise ValueError("accuracy must be between 0 and 1")
        for value in (self.latency_ms, self.memory_mb, self.accuracy, self.cost):
            if not isfinite(value):
                raise ValueError("benchmark metrics must be finite")


@dataclass(frozen=True)
class Constraints:
    max_latency_ms: float | None = None
    max_memory_mb: float | None = None
    min_accuracy: float | None = None
    max_cost: float | None = None


@dataclass(frozen=True)
class Weights:
    latency: float = 1.0
    memory: float = 1.0
    accuracy: float = 1.0
    cost: float = 1.0

    def __post_init__(self) -> None:
        if any(v < 0 for v in (self.latency, self.memory, self.accuracy, self.cost)):
            raise ValueError("weights must be non-negative")
        if self.latency + self.memory + self.accuracy + self.cost == 0:
            raise ValueError("at least one weight must be positive")


@dataclass
class Candidate:
    name: str
    implementation: Callable[..., object]
    benchmark: Benchmark
    tags: frozenset[str] = field(default_factory=frozenset)


class Algora:
    """Deterministic algorithm registry, selector and evidence store."""

    def __init__(self) -> None:
        self._candidates: Dict[str, Candidate] = {}

    def register(
        self,
        name: str,
        implementation: Callable[..., object],
        benchmark: Benchmark,
        *,
        tags: Iterable[str] = (),
    ) -> None:
        clean = name.strip()
        if not clean:
            raise ValueError("algorithm name is required")
        if not callable(implementation):
            raise TypeError("implementation must be callable")
        self._candidates[clean] = Candidate(
            name=clean,
            implementation=implementation,
            benchmark=benchmark,
            tags=frozenset(str(tag).strip() for tag in tags if str(tag).strip()),
        )

    def names(self) -> List[str]:
        return sorted(self._candidates)

    def eligible(
        self,
        constraints: Constraints = Constraints(),
        *,
        required_tags: Iterable[str] = (),
    ) -> List[Candidate]:
        tags = frozenset(required_tags)
        result: List[Candidate] = []
        for candidate in self._candidates.values():
            b = candidate.benchmark
            if constraints.max_latency_ms is not None and b.latency_ms > constraints.max_latency_ms:
                continue
            if constraints.max_memory_mb is not None and b.memory_mb > constraints.max_memory_mb:
                continue
            if constraints.min_accuracy is not None and b.accuracy < constraints.min_accuracy:
                continue
            if constraints.max_cost is not None and b.cost > constraints.max_cost:
                continue
            if not tags.issubset(candidate.tags):
                continue
            result.append(candidate)
        return sorted(result, key=lambda c: c.name)

    @staticmethod
    def _normalise(values: Mapping[str, float], *, invert: bool = False) -> Dict[str, float]:
        if not values:
            return {}
        lo = min(values.values())
        hi = max(values.values())
        if hi == lo:
            base = {name: 1.0 for name in values}
        else:
            base = {name: (value - lo) / (hi - lo) for name, value in values.items()}
        return {name: (1.0 - value if invert else value) for name, value in base.items()}

    def rank(
        self,
        constraints: Constraints = Constraints(),
        *,
        weights: Weights = Weights(),
        required_tags: Iterable[str] = (),
    ) -> List[dict]:
        candidates = self.eligible(constraints, required_tags=required_tags)
        if not candidates:
            return []

        latency = self._normalise({c.name: c.benchmark.latency_ms for c in candidates}, invert=True)
        memory = self._normalise({c.name: c.benchmark.memory_mb for c in candidates}, invert=True)
        accuracy = self._normalise({c.name: c.benchmark.accuracy for c in candidates})
        cost = self._normalise({c.name: c.benchmark.cost for c in candidates}, invert=True)

        total_weight = weights.latency + weights.memory + weights.accuracy + weights.cost
        ranked = []
        for c in candidates:
            score = (
                latency[c.name] * weights.latency
                + memory[c.name] * weights.memory
                + accuracy[c.name] * weights.accuracy
                + cost[c.name] * weights.cost
            ) / total_weight
            ranked.append({
                "name": c.name,
                "score": round(score, 9),
                "benchmark": c.benchmark,
                "tags": sorted(c.tags),
            })

        return sorted(ranked, key=lambda x: (-x["score"], x["name"]))

    def select(self, *args, **kwargs) -> Candidate:
        ranked = self.rank(*args, **kwargs)
        if not ranked:
            raise LookupError("no algorithm satisfies the requested constraints")
        return self._candidates[ranked[0]["name"]]

    def execute(self, *args, constraints: Constraints = Constraints(), weights: Weights = Weights(), required_tags: Iterable[str] = (), **kwargs):
        candidate = self.select(constraints, weights=weights, required_tags=required_tags)
        return {
            "algorithm": candidate.name,
            "result": candidate.implementation(*args, **kwargs),
            "benchmark": candidate.benchmark,
        }

    def evidence_hash(self) -> str:
        payload = [
            {
                "name": c.name,
                "benchmark": {
                    "latency_ms": c.benchmark.latency_ms,
                    "memory_mb": c.benchmark.memory_mb,
                    "accuracy": c.benchmark.accuracy,
                    "cost": c.benchmark.cost,
                },
                "tags": sorted(c.tags),
            }
            for c in sorted(self._candidates.values(), key=lambda c: c.name)
        ]
        encoded = dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return sha256(encoded).hexdigest()
