# DeFi Trend Paper Trader

> **Axiom Hive Technology**  
> **Technical attribution:** Alexis M. Adams & Nicholas Michael Grossi

A compact, **paper-trading-only** Python research framework for a single Uniswap-v2-style constant-product pool. It validates local historical pool snapshots, creates a deterministic trend score, applies rule-based risk controls, simulates AMM execution and costs, and writes an auditable CSV ledger.

> **Research boundary:** This project does not provide investment advice, forecast returns, access a wallet, store a private key, sign a transaction, call a live RPC endpoint, or broadcast a transaction. It is intended for local research and simulated paper operation only.

## What is implemented

| Capability | Status |
|---|---|
| Strict input-schema and point-in-time validation | Implemented |
| Deterministic trend baseline | Implemented |
| Rule-based risk controls and kill switch | Implemented |
| Uniswap-v2-style reserve-based exact-input swap simulation | Implemented |
| Gas, pool fee, execution delay, and stress haircut model | Implemented |
| Audit-ready CSV paper ledger | Implemented |
| Unit tests and GitHub CI workflow template | Implemented |
| Live wallet/RPC/signing/broadcast path | Deliberately absent |
| Uniswap v3 concentrated-liquidity simulation | Deliberately absent |

## Quick start

The project uses the Python standard library and has no runtime third-party dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .

# Generate deterministic sample data.
defi-trend generate-sample --output data/sample/pool_snapshots.csv

# Validate the sample input and show its digest.
defi-trend validate --input data/sample/pool_snapshots.csv

# Run the isolated paper simulation.
defi-trend backtest \
  --input data/sample/pool_snapshots.csv \
  --config configs/research.example.json \
  --output reports/paper_ledger.csv
```

Run the test suite with:

```bash
python -m pytest -q
```

## Input data contract

The current engine accepts **finalized, historical snapshots only**. Its required CSV columns are:

```text
block_number,block_timestamp,available_at_utc,price_usd,reserve_base,reserve_quote,
base_fee_gwei,priority_fee_gwei,gas_used,eth_usd
```

The validator requires increasing unique block numbers, positive price/reserves, non-negative fees, and `available_at_utc` no later than the decision time. This contract is intentionally narrow: a production-quality ingest pipeline must independently preserve block hashes, finality/reorganization state, event provenance, and protocol metadata before generating this input.

## Model and execution limits

The baseline score is derived from a fast/slow moving-average gap and trailing return. It maps to a bounded **target base-asset weight**, not to an order. The independent risk engine can reject a target for stale data, disabled operation, excessive turnover, liquidity limits, exposure caps, or an activated kill switch.

The AMM simulator assumes a v2-style constant-product pool and exact-input swap. It is not suitable for Uniswap v3, v4, multi-hop routes, concentrated-liquidity pools, leveraged products, or live execution. The simulator records all rejected decisions as well as accepted paper trades.

## Repository layout

```text
configs/                 Versioned example configuration
src/defi_trend/          Research, validation, risk, AMM, and CLI modules
tests/                   Unit and integration tests
data/sample/             Deterministic local demonstration data
docs/                    Architecture and operational boundaries
docs/github-actions-test.yml.example  CI workflow template; no schedules or network integrations
```

## Security controls

The codebase deliberately contains no wallet package, signer abstraction, RPC URL configuration, transaction serialization, API key support, or live network client. The test workflow is supplied as a template in `docs/` because the publishing credential cannot create workflow files. Copy it into `.github/workflows/` only with a credential authorized to manage workflows. Do not add a live-execution capability without separate protocol-specific, operational, legal, sanctions, tax, and security reviews.

## License

This repository is released under the [MIT License](LICENSE).
