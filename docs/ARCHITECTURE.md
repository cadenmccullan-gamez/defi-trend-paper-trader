# Repository Architecture

> **Axiom Hive Technology**  
> **Technical attribution:** Alexis M. Adams & Nicholas Michael Grossi

## Purpose

This repository implements a **local, paper-trading-only** research framework for one synthetic Uniswap-v2-style constant-product pool. It is designed to validate data quality, calculate a deterministic trend signal, apply independent risk controls, simulate v2 AMM execution, and write an audit ledger. It does not use a wallet, private key, signer, live RPC connection, transaction broadcaster, or third-party funds.

## Scope decision

The implementation intentionally supports **v2-style pools only**. The cost engine uses a reserve-based constant-product formula, which must not be applied to a Uniswap v3 concentrated-liquidity pool. A v3 implementation requires a separate state reconstruction engine for ticks and active liquidity.

## Components

| Component | Module | Responsibility | Safety boundary |
|---|---|---|---|
| Configuration | `config.py` | Loads and validates a JSON configuration with explicit risk and cost limits. | Rejects unknown or unsafe configuration values. |
| Data validation | `validation.py` | Validates block order, unique block numbers, positive reserves, and point-in-time availability. | Rejects invalid records before features or execution. |
| Features | `features.py` | Builds trailing-return, moving-average-gap, volatility, and liquidity features. | Uses only observations available at the stated decision time. |
| Signal | `signal.py` | Produces a bounded deterministic trend score and target position. | Produces no order and accesses no execution interface. |
| Risk | `risk.py` | Applies freshness, exposure, turnover, volatility, and liquidity controls. | Can reject any model target independently. |
| Execution simulator | `amm_v2.py` | Simulates v2-style exact-input swap output, price impact, gas, and stress haircut. | No signing or broadcasting capabilities exist. |
| Backtest | `backtest.py` | Runs chronological paper simulation and produces an audit ledger. | Writes only local CSV output. |
| CLI | `cli.py` | Offers `validate`, `backtest`, and `generate-sample` commands. | Requires explicit local file paths. |

## Data contract

The initial input is a CSV file. Each row represents an already-finalized historical pool snapshot. Required fields are:

```text
block_number,block_timestamp,available_at_utc,price_usd,reserve_base,reserve_quote,
base_fee_gwei,priority_fee_gwei,gas_used,eth_usd
```

The backtest evaluates a decision only when `available_at_utc <= decision_time`. Input records must have strictly increasing `block_number`, unique block numbers, positive prices and reserves, and non-negative fee/gas fields.

## Operational model

The repository is intentionally a local research package. A GitHub Actions test-workflow template is supplied in `docs/github-actions-test.yml.example`; it does not execute a recurring strategy, call a market-data provider, or interact with any blockchain. It can be copied into `.github/workflows/` after using a credential authorized to manage workflow files.

## Acceptance criteria

A valid build must pass all unit tests, generate the deterministic sample data, validate that data, and create a repeatable paper-trading ledger. The output must contain a decision record for every evaluated timestamp, including rejections and their reason codes.
