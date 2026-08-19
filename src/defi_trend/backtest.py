"""Chronological, local, paper-only backtesting and audit-ledger generation."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from .amm_v2 import quote_buy_base, quote_sell_base
from .config import ResearchConfig
from .risk import evaluate_risk
from .signal import build_signal
from .types import LedgerRow, Snapshot


def _row(
    snapshot: Snapshot,
    *,
    status: str,
    reason: str,
    portfolio_value_quote: float,
    base_balance: float,
    quote_balance: float,
    score: float | None = None,
    requested_target_weight: float | None = None,
    approved_target_weight: float | None = None,
    trade_quote: float = 0.0,
    trade_base: float = 0.0,
    execution_price_quote_per_base: float | None = None,
    price_impact_bps: float | None = None,
    pool_fee_quote: float | None = None,
    gas_cost_quote: float | None = None,
    mev_cost_quote: float | None = None,
    total_cost_quote: float | None = None,
) -> LedgerRow:
    return LedgerRow(
        block_number=snapshot.block_number,
        decision_time=snapshot.available_at_utc,
        status=status,
        reason=reason,
        score=score,
        requested_target_weight=requested_target_weight,
        approved_target_weight=approved_target_weight,
        portfolio_value_quote=portfolio_value_quote,
        base_balance=base_balance,
        quote_balance=quote_balance,
        trade_quote=trade_quote,
        trade_base=trade_base,
        execution_price_quote_per_base=execution_price_quote_per_base,
        price_impact_bps=price_impact_bps,
        pool_fee_quote=pool_fee_quote,
        gas_cost_quote=gas_cost_quote,
        mev_cost_quote=mev_cost_quote,
        total_cost_quote=total_cost_quote,
    )


def run_backtest(snapshots: list[Snapshot], config: ResearchConfig) -> list[LedgerRow]:
    """Run chronological v2-style paper simulation against validated local snapshots."""

    required_history = max(
        config.slow_window,
        config.lookback_return_window + 1,
        config.volatility_window + 1,
    )
    base_balance = config.initial_base_balance
    quote_balance = config.initial_quote_balance
    turnover_by_day: dict[str, float] = defaultdict(float)
    ledger: list[LedgerRow] = []

    for index, snapshot in enumerate(snapshots):
        portfolio_value = quote_balance + base_balance * snapshot.price_usd
        if index + 1 < required_history:
            ledger.append(
                _row(
                    snapshot,
                    status="WARMUP",
                    reason="INSUFFICIENT_HISTORY",
                    portfolio_value_quote=portfolio_value,
                    base_balance=base_balance,
                    quote_balance=quote_balance,
                )
            )
            continue
        if index % config.decision_interval != 0:
            ledger.append(
                _row(
                    snapshot,
                    status="SKIPPED",
                    reason="DECISION_INTERVAL",
                    portfolio_value_quote=portfolio_value,
                    base_balance=base_balance,
                    quote_balance=quote_balance,
                )
            )
            continue

        signal = build_signal(snapshots[: index + 1], config)
        current_weight = (base_balance * snapshot.price_usd) / portfolio_value if portfolio_value else 0.0
        day_key = snapshot.available_at_utc.date().isoformat()
        risk = evaluate_risk(
            snapshot=snapshot,
            requested_target_weight=signal.target_weight,
            current_weight=current_weight,
            portfolio_value_quote=portfolio_value,
            turnover_used_quote=turnover_by_day[day_key],
            config=config,
        )
        if not risk.approved:
            ledger.append(
                _row(
                    snapshot,
                    status="REJECTED",
                    reason=risk.reason,
                    score=signal.score,
                    requested_target_weight=signal.target_weight,
                    approved_target_weight=risk.approved_target_weight,
                    portfolio_value_quote=portfolio_value,
                    base_balance=base_balance,
                    quote_balance=quote_balance,
                )
            )
            continue

        execution_index = index + config.execution_delay_blocks
        if execution_index >= len(snapshots):
            ledger.append(
                _row(
                    snapshot,
                    status="REJECTED",
                    reason="NO_FUTURE_EXECUTION_SNAPSHOT",
                    score=signal.score,
                    requested_target_weight=signal.target_weight,
                    approved_target_weight=risk.approved_target_weight,
                    portfolio_value_quote=portfolio_value,
                    base_balance=base_balance,
                    quote_balance=quote_balance,
                )
            )
            continue

        target_base_value = risk.approved_target_weight * portfolio_value
        current_base_value = base_balance * snapshot.price_usd
        delta_quote_at_decision = target_base_value - current_base_value
        if abs(delta_quote_at_decision) < config.minimum_trade_quote:
            ledger.append(
                _row(
                    snapshot,
                    status="NO_TRADE",
                    reason="BELOW_MINIMUM_TRADE",
                    score=signal.score,
                    requested_target_weight=signal.target_weight,
                    approved_target_weight=risk.approved_target_weight,
                    portfolio_value_quote=portfolio_value,
                    base_balance=base_balance,
                    quote_balance=quote_balance,
                )
            )
            continue

        execution_snapshot = snapshots[execution_index]
        try:
            if delta_quote_at_decision > 0:
                quote = quote_buy_base(
                    execution_snapshot,
                    input_quote=delta_quote_at_decision,
                    pool_fee_fraction=config.pool_fee_fraction,
                    mev_haircut_bps=config.mev_haircut_bps,
                    maximum_fraction_of_reserve=config.max_trade_fraction_of_reserve,
                )
                required_quote = -quote.trade_quote_signed + quote.gas_cost_quote + quote.mev_cost_quote
                if required_quote > quote_balance:
                    raise ValueError("INSUFFICIENT_QUOTE_BALANCE")
                base_balance += quote.trade_base_signed
                quote_balance += quote.trade_quote_signed - quote.gas_cost_quote - quote.mev_cost_quote
            else:
                desired_base = min(
                    base_balance,
                    abs(delta_quote_at_decision) / execution_snapshot.price_usd,
                )
                quote = quote_sell_base(
                    execution_snapshot,
                    input_base=desired_base,
                    pool_fee_fraction=config.pool_fee_fraction,
                    mev_haircut_bps=config.mev_haircut_bps,
                    maximum_fraction_of_reserve=config.max_trade_fraction_of_reserve,
                )
                base_balance += quote.trade_base_signed
                quote_balance += quote.trade_quote_signed - quote.gas_cost_quote

            turnover_by_day[day_key] += abs(delta_quote_at_decision)
            updated_value = quote_balance + base_balance * execution_snapshot.price_usd
            ledger.append(
                _row(
                    snapshot,
                    status="PAPER_FILLED",
                    reason=f"{quote.direction}_AT_DELAY_{config.execution_delay_blocks}",
                    score=signal.score,
                    requested_target_weight=signal.target_weight,
                    approved_target_weight=risk.approved_target_weight,
                    portfolio_value_quote=updated_value,
                    base_balance=base_balance,
                    quote_balance=quote_balance,
                    trade_quote=quote.trade_quote_signed - quote.gas_cost_quote,
                    trade_base=quote.trade_base_signed,
                    execution_price_quote_per_base=quote.execution_price_quote_per_base,
                    price_impact_bps=quote.price_impact_bps,
                    pool_fee_quote=quote.pool_fee_quote,
                    gas_cost_quote=quote.gas_cost_quote,
                    mev_cost_quote=quote.mev_cost_quote,
                    total_cost_quote=quote.total_cost_quote,
                )
            )
        except ValueError as error:
            ledger.append(
                _row(
                    snapshot,
                    status="REJECTED",
                    reason=str(error),
                    score=signal.score,
                    requested_target_weight=signal.target_weight,
                    approved_target_weight=risk.approved_target_weight,
                    portfolio_value_quote=portfolio_value,
                    base_balance=base_balance,
                    quote_balance=quote_balance,
                )
            )

    return ledger


def write_ledger(rows: list[LedgerRow], path: str | Path) -> None:
    """Write an audit-ready CSV ledger and create parent directories when needed."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(LedgerRow.__annotations__))
        writer.writeheader()
        for row in rows:
            record = asdict(row)
            record["decision_time"] = row.decision_time.isoformat()
            writer.writerow(record)
