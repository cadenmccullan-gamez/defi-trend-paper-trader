"""Deterministic trend baseline; this module produces scores, never orders."""

from __future__ import annotations

import math
import statistics

from .config import ResearchConfig
from .types import Signal, Snapshot


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("at least one value is required")
    return sum(values) / len(values)


def build_signal(history: list[Snapshot], config: ResearchConfig) -> Signal:
    """Build a long-only bounded target from point-in-time local history."""

    required = max(
        config.slow_window,
        config.lookback_return_window + 1,
        config.volatility_window + 1,
    )
    if len(history) < required:
        raise ValueError(f"signal requires at least {required} snapshots")

    prices = [snapshot.price_usd for snapshot in history]
    fast_average = _mean(prices[-config.fast_window :])
    slow_average = _mean(prices[-config.slow_window :])
    trailing_return = prices[-1] / prices[-1 - config.lookback_return_window] - 1.0

    returns = [
        prices[index] / prices[index - 1] - 1.0
        for index in range(len(prices) - config.volatility_window, len(prices))
    ]
    realized_volatility = statistics.pstdev(returns) if len(returns) > 1 else 0.0
    moving_average_gap = fast_average / slow_average - 1.0
    raw_score = 100.0 * (0.7 * moving_average_gap + 0.3 * trailing_return)
    score = math.tanh(raw_score)

    volatility_scaler = 1.0 / (1.0 + 20.0 * realized_volatility)
    target_weight = max(0.0, min(config.max_target_weight, score * config.max_target_weight))
    target_weight *= volatility_scaler

    return Signal(
        score=score,
        target_weight=target_weight,
        fast_average=fast_average,
        slow_average=slow_average,
        trailing_return=trailing_return,
        realized_volatility=realized_volatility,
    )
