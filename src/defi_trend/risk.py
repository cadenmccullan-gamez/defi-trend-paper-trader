"""Deterministic controls independent of the trend signal."""

from __future__ import annotations

from .config import ResearchConfig
from .types import RiskDecision, Snapshot


def evaluate_risk(
    snapshot: Snapshot,
    requested_target_weight: float,
    current_weight: float,
    portfolio_value_quote: float,
    turnover_used_quote: float,
    config: ResearchConfig,
) -> RiskDecision:
    """Approve or reject a bounded target without modifying model output logic."""

    if config.kill_switch:
        return RiskDecision(False, "KILL_SWITCH_ACTIVE", current_weight)
    data_age_seconds = (snapshot.available_at_utc - snapshot.block_timestamp).total_seconds()
    if data_age_seconds > config.max_data_age_seconds:
        return RiskDecision(False, "STALE_DATA", current_weight)
    if not 0.0 <= requested_target_weight <= config.max_target_weight:
        return RiskDecision(False, "TARGET_CAP_BREACH", current_weight)
    if portfolio_value_quote <= 0:
        return RiskDecision(False, "NON_POSITIVE_PORTFOLIO_VALUE", current_weight)

    proposed_turnover = abs(requested_target_weight - current_weight) * portfolio_value_quote
    remaining_turnover = max(0.0, config.max_turnover_quote - turnover_used_quote)
    if proposed_turnover > remaining_turnover:
        return RiskDecision(False, "TURNOVER_CAP", current_weight)

    liquidity_cap_quote = snapshot.reserve_quote * config.max_trade_fraction_of_reserve
    if proposed_turnover > liquidity_cap_quote:
        return RiskDecision(False, "LIQUIDITY_CAP", current_weight)

    return RiskDecision(True, "APPROVED", requested_target_weight)
