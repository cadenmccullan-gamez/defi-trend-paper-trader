"""Reserve-based, Uniswap-v2-style paper execution simulator.

This module contains no RPC, wallet, signing, or transaction-broadcast functionality.
"""

from __future__ import annotations

from .types import Snapshot, SwapQuote

_GWEI_TO_ETH = 1e-9


def effective_gas_cost_quote(snapshot: Snapshot) -> float:
    """Estimate EIP-1559-style paid gas from recorded fee inputs and gas used."""

    effective_gas_price_gwei = snapshot.base_fee_gwei + snapshot.priority_fee_gwei
    return snapshot.gas_used * effective_gas_price_gwei * _GWEI_TO_ETH * snapshot.eth_usd


def _validate_trade_size(amount: float, maximum_fraction: float) -> None:
    if amount <= 0:
        raise ValueError("trade amount must be positive")
    if maximum_fraction <= 0 or maximum_fraction > 0.1:
        raise ValueError("maximum_fraction must be in (0, 0.1]")


def quote_buy_base(
    snapshot: Snapshot,
    input_quote: float,
    pool_fee_fraction: float,
    mev_haircut_bps: float,
    maximum_fraction_of_reserve: float,
) -> SwapQuote:
    """Simulate an exact-input quote-to-base swap against a v2-style pool."""

    _validate_trade_size(input_quote, maximum_fraction_of_reserve)
    if input_quote > snapshot.reserve_quote * maximum_fraction_of_reserve:
        raise ValueError("buy input exceeds configured pool-liquidity cap")
    if not 0 <= pool_fee_fraction < 1:
        raise ValueError("pool_fee_fraction must be in [0, 1)")

    fee_adjusted_input = input_quote * (1 - pool_fee_fraction)
    output_base = (
        snapshot.reserve_base
        * fee_adjusted_input
        / (snapshot.reserve_quote + fee_adjusted_input)
    )
    spot_price = snapshot.reserve_quote / snapshot.reserve_base
    execution_price = input_quote / output_base
    price_impact_bps = (execution_price / spot_price - 1.0) * 10_000
    pool_fee_quote = input_quote * pool_fee_fraction
    gas_cost = effective_gas_cost_quote(snapshot)
    mev_cost = input_quote * mev_haircut_bps / 10_000

    return SwapQuote(
        direction="BUY_BASE",
        trade_quote_signed=-input_quote,
        trade_base_signed=output_base,
        pool_fee_quote=pool_fee_quote,
        spot_price_quote_per_base=spot_price,
        execution_price_quote_per_base=execution_price,
        price_impact_bps=price_impact_bps,
        gas_cost_quote=gas_cost,
        mev_cost_quote=mev_cost,
        total_cost_quote=pool_fee_quote + gas_cost + mev_cost,
    )


def quote_sell_base(
    snapshot: Snapshot,
    input_base: float,
    pool_fee_fraction: float,
    mev_haircut_bps: float,
    maximum_fraction_of_reserve: float,
) -> SwapQuote:
    """Simulate an exact-input base-to-quote swap against a v2-style pool."""

    _validate_trade_size(input_base, maximum_fraction_of_reserve)
    if input_base > snapshot.reserve_base * maximum_fraction_of_reserve:
        raise ValueError("sell input exceeds configured pool-liquidity cap")
    if not 0 <= pool_fee_fraction < 1:
        raise ValueError("pool_fee_fraction must be in [0, 1)")

    fee_adjusted_input = input_base * (1 - pool_fee_fraction)
    output_quote_before_mev = (
        snapshot.reserve_quote
        * fee_adjusted_input
        / (snapshot.reserve_base + fee_adjusted_input)
    )
    spot_price = snapshot.reserve_quote / snapshot.reserve_base
    execution_price = output_quote_before_mev / input_base
    price_impact_bps = (1.0 - execution_price / spot_price) * 10_000
    pool_fee_quote = input_base * spot_price * pool_fee_fraction
    gas_cost = effective_gas_cost_quote(snapshot)
    mev_cost = output_quote_before_mev * mev_haircut_bps / 10_000

    return SwapQuote(
        direction="SELL_BASE",
        trade_quote_signed=output_quote_before_mev - mev_cost,
        trade_base_signed=-input_base,
        pool_fee_quote=pool_fee_quote,
        spot_price_quote_per_base=spot_price,
        execution_price_quote_per_base=execution_price,
        price_impact_bps=price_impact_bps,
        gas_cost_quote=gas_cost,
        mev_cost_quote=mev_cost,
        total_cost_quote=pool_fee_quote + gas_cost + mev_cost,
    )
