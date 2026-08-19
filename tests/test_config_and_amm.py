from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from defi_trend.amm_v2 import quote_buy_base, quote_sell_base
from defi_trend.config import load_config
from defi_trend.types import Snapshot


def snapshot() -> Snapshot:
    return Snapshot(
        block_number=1,
        block_timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        available_at_utc=datetime(2025, 1, 1, 0, 2, tzinfo=timezone.utc),
        price_usd=2000.0,
        reserve_base=1000.0,
        reserve_quote=2_000_000.0,
        base_fee_gwei=20.0,
        priority_fee_gwei=2.0,
        gas_used=100_000,
        eth_usd=2000.0,
    )


def test_v2_buy_quote_has_positive_output_and_costs() -> None:
    quote = quote_buy_base(snapshot(), 1000.0, 0.003, 10.0, 0.01)
    assert quote.direction == "BUY_BASE"
    assert quote.trade_quote_signed == -1000.0
    assert quote.trade_base_signed > 0
    assert quote.execution_price_quote_per_base > quote.spot_price_quote_per_base
    assert quote.pool_fee_quote == pytest.approx(3.0)
    assert quote.gas_cost_quote > 0
    assert quote.mev_cost_quote == pytest.approx(1.0)


def test_v2_sell_quote_reduces_base_and_receives_quote() -> None:
    quote = quote_sell_base(snapshot(), 0.25, 0.003, 10.0, 0.01)
    assert quote.direction == "SELL_BASE"
    assert quote.trade_base_signed == -0.25
    assert quote.trade_quote_signed > 0
    assert quote.execution_price_quote_per_base < quote.spot_price_quote_per_base
    assert quote.price_impact_bps > 0


def test_liquidity_cap_rejects_large_trade() -> None:
    with pytest.raises(ValueError, match="liquidity cap"):
        quote_buy_base(snapshot(), 25_000.0, 0.003, 0.0, 0.01)


def test_config_rejects_live_execution_fields(tmp_path: Path) -> None:
    config = {
        "run_name": "test",
        "paper_mode": True,
        "kill_switch": False,
        "fast_window": 2,
        "slow_window": 4,
        "lookback_return_window": 2,
        "volatility_window": 2,
        "decision_interval": 1,
        "initial_quote_balance": 1000.0,
        "initial_base_balance": 0.0,
        "max_target_weight": 0.3,
        "max_turnover_quote": 1000.0,
        "max_trade_fraction_of_reserve": 0.01,
        "max_data_age_seconds": 600,
        "pool_fee_fraction": 0.003,
        "execution_delay_blocks": 1,
        "mev_haircut_bps": 0.0,
        "minimum_trade_quote": 1.0,
        "model_version": "test",
        "risk_config_version": "test",
        "cost_model_version": "test",
        "private_key": "not-allowed"
    }
    path = tmp_path / "unsafe.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(path)
