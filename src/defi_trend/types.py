"""Typed records for the isolated paper-trading research framework."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Snapshot:
    """A finalized historical v2-style pool snapshot available at a stated time."""

    block_number: int
    block_timestamp: datetime
    available_at_utc: datetime
    price_usd: float
    reserve_base: float
    reserve_quote: float
    base_fee_gwei: float
    priority_fee_gwei: float
    gas_used: int
    eth_usd: float


@dataclass(frozen=True)
class Signal:
    """A bounded deterministic score and its requested target base-asset weight."""

    score: float
    target_weight: float
    fast_average: float
    slow_average: float
    trailing_return: float
    realized_volatility: float


@dataclass(frozen=True)
class RiskDecision:
    """Independent deterministic approval or rejection of a target position."""

    approved: bool
    reason: str
    approved_target_weight: float


@dataclass(frozen=True)
class SwapQuote:
    """A simulated v2 exact-input swap with all explicitly modelled costs."""

    direction: str
    trade_quote_signed: float
    trade_base_signed: float
    pool_fee_quote: float
    spot_price_quote_per_base: float
    execution_price_quote_per_base: float
    price_impact_bps: float
    gas_cost_quote: float
    mev_cost_quote: float
    total_cost_quote: float


@dataclass(frozen=True)
class LedgerRow:
    """One immutable paper-decision record for audit and reconciliation."""

    block_number: int
    decision_time: datetime
    status: str
    reason: str
    score: float | None
    requested_target_weight: float | None
    approved_target_weight: float | None
    portfolio_value_quote: float
    base_balance: float
    quote_balance: float
    trade_quote: float
    trade_base: float
    execution_price_quote_per_base: float | None
    price_impact_bps: float | None
    pool_fee_quote: float | None
    gas_cost_quote: float | None
    mev_cost_quote: float | None
    total_cost_quote: float | None
