"""Configuration validation for paper-only trend research."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ResearchConfig:
    run_name: str
    paper_mode: bool
    kill_switch: bool
    fast_window: int
    slow_window: int
    lookback_return_window: int
    volatility_window: int
    decision_interval: int
    initial_quote_balance: float
    initial_base_balance: float
    max_target_weight: float
    max_turnover_quote: float
    max_trade_fraction_of_reserve: float
    max_data_age_seconds: int
    pool_fee_fraction: float
    execution_delay_blocks: int
    mev_haircut_bps: float
    minimum_trade_quote: float
    model_version: str
    risk_config_version: str
    cost_model_version: str


_REQUIRED_FIELDS = set(ResearchConfig.__annotations__)
_FORBIDDEN_FIELDS = {
    "private_key",
    "wallet_address",
    "rpc_url",
    "signer",
    "broadcast_url",
    "api_key",
    "seed_phrase",
}


def _positive_int(value: object, field: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _non_negative_float(value: object, field: str) -> float:
    if not isinstance(value, (int, float)) or float(value) < 0:
        raise ValueError(f"{field} must be a non-negative number")
    return float(value)


def load_config(path: str | Path) -> ResearchConfig:
    """Load a local JSON configuration and reject any live-execution fields."""

    source = Path(path)
    raw = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("configuration root must be a JSON object")

    unknown = set(raw) - _REQUIRED_FIELDS
    missing = _REQUIRED_FIELDS - set(raw)
    forbidden = _FORBIDDEN_FIELDS & set(raw)
    if missing:
        raise ValueError(f"configuration is missing fields: {sorted(missing)}")
    if unknown:
        raise ValueError(f"configuration contains unsupported fields: {sorted(unknown)}")
    if forbidden:
        raise ValueError(f"configuration contains forbidden live-execution fields: {sorted(forbidden)}")
    if raw["paper_mode"] is not True:
        raise ValueError("paper_mode must be true; live mode is not implemented")

    fast_window = _positive_int(raw["fast_window"], "fast_window")
    slow_window = _positive_int(raw["slow_window"], "slow_window")
    if fast_window >= slow_window:
        raise ValueError("fast_window must be smaller than slow_window")

    max_target_weight = _non_negative_float(raw["max_target_weight"], "max_target_weight")
    if max_target_weight > 1.0:
        raise ValueError("max_target_weight must not exceed 1.0 in this long-only paper framework")

    pool_fee_fraction = _non_negative_float(raw["pool_fee_fraction"], "pool_fee_fraction")
    if pool_fee_fraction >= 1.0:
        raise ValueError("pool_fee_fraction must be less than 1.0")

    reserve_fraction = _non_negative_float(
        raw["max_trade_fraction_of_reserve"], "max_trade_fraction_of_reserve"
    )
    if reserve_fraction > 0.1:
        raise ValueError("max_trade_fraction_of_reserve must not exceed 10 percent")

    for field in ("run_name", "model_version", "risk_config_version", "cost_model_version"):
        if not isinstance(raw[field], str) or not raw[field].strip():
            raise ValueError(f"{field} must be a non-empty string")

    return ResearchConfig(
        run_name=raw["run_name"],
        paper_mode=True,
        kill_switch=bool(raw["kill_switch"]),
        fast_window=fast_window,
        slow_window=slow_window,
        lookback_return_window=_positive_int(raw["lookback_return_window"], "lookback_return_window"),
        volatility_window=_positive_int(raw["volatility_window"], "volatility_window"),
        decision_interval=_positive_int(raw["decision_interval"], "decision_interval"),
        initial_quote_balance=_non_negative_float(raw["initial_quote_balance"], "initial_quote_balance"),
        initial_base_balance=_non_negative_float(raw["initial_base_balance"], "initial_base_balance"),
        max_target_weight=max_target_weight,
        max_turnover_quote=_non_negative_float(raw["max_turnover_quote"], "max_turnover_quote"),
        max_trade_fraction_of_reserve=reserve_fraction,
        max_data_age_seconds=_positive_int(raw["max_data_age_seconds"], "max_data_age_seconds"),
        pool_fee_fraction=pool_fee_fraction,
        execution_delay_blocks=_positive_int(raw["execution_delay_blocks"], "execution_delay_blocks"),
        mev_haircut_bps=_non_negative_float(raw["mev_haircut_bps"], "mev_haircut_bps"),
        minimum_trade_quote=_non_negative_float(raw["minimum_trade_quote"], "minimum_trade_quote"),
        model_version=raw["model_version"],
        risk_config_version=raw["risk_config_version"],
        cost_model_version=raw["cost_model_version"],
    )
