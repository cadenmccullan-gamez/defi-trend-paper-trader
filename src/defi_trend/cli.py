"""Command-line interface for local validation and paper simulation only."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .backtest import run_backtest, write_ledger
from .config import load_config
from .validation import load_snapshots, sha256_digest


def generate_sample(path: str | Path, rows: int = 48) -> None:
    """Create deterministic, explicitly synthetic data for tests and local demonstrations."""

    if rows < 24:
        raise ValueError("sample generation requires at least 24 rows")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    fields = [
        "block_number",
        "block_timestamp",
        "available_at_utc",
        "price_usd",
        "reserve_base",
        "reserve_quote",
        "base_fee_gwei",
        "priority_fee_gwei",
        "gas_used",
        "eth_usd",
    ]
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index in range(rows):
            timestamp = start + timedelta(hours=4 * index)
            price = 2000.0 * (1.0 + 0.0025 * index + 0.01 * ((index % 6) - 3) / 6)
            reserve_base = 1500.0 + 2.0 * index
            reserve_quote = reserve_base * price
            writer.writerow(
                {
                    "block_number": 19_000_000 + index,
                    "block_timestamp": timestamp.isoformat(),
                    "available_at_utc": (timestamp + timedelta(minutes=2)).isoformat(),
                    "price_usd": f"{price:.8f}",
                    "reserve_base": f"{reserve_base:.8f}",
                    "reserve_quote": f"{reserve_quote:.8f}",
                    "base_fee_gwei": f"{18.0 + (index % 5):.2f}",
                    "priority_fee_gwei": "1.50",
                    "gas_used": 140000,
                    "eth_usd": f"{price:.8f}",
                }
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="defi-trend",
        description="Local, paper-only Uniswap-v2-style trend research simulator.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sample = subparsers.add_parser("generate-sample", help="write deterministic synthetic demonstration data")
    sample.add_argument("--output", required=True)
    sample.add_argument("--rows", type=int, default=48)

    validate = subparsers.add_parser("validate", help="validate a local historical snapshot CSV")
    validate.add_argument("--input", required=True)

    backtest = subparsers.add_parser("backtest", help="run a local paper simulation and write an audit ledger")
    backtest.add_argument("--input", required=True)
    backtest.add_argument("--config", required=True)
    backtest.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "generate-sample":
        generate_sample(args.output, args.rows)
        print(f"Wrote deterministic synthetic sample data to {args.output}")
        return 0
    if args.command == "validate":
        snapshots = load_snapshots(args.input)
        print(
            f"VALID: {len(snapshots)} snapshots; "
            f"SHA256={sha256_digest(args.input)}"
        )
        return 0
    if args.command == "backtest":
        config = load_config(args.config)
        snapshots = load_snapshots(args.input)
        ledger = run_backtest(snapshots, config)
        write_ledger(ledger, args.output)
        fills = sum(row.status == "PAPER_FILLED" for row in ledger)
        rejections = sum(row.status == "REJECTED" for row in ledger)
        print(
            f"PAPER_ONLY: {len(ledger)} decisions; {fills} simulated fills; "
            f"{rejections} rejections; ledger={args.output}"
        )
        return 0
    raise RuntimeError("unknown command")


if __name__ == "__main__":
    raise SystemExit(main())
