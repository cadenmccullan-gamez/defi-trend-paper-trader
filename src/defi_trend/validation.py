"""Local CSV loading and point-in-time validation for finalized pool snapshots."""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from .types import Snapshot

_REQUIRED_COLUMNS = {
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
}


def _parse_time(raw: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{field} must be ISO-8601: {raw!r}") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def load_snapshots(path: str | Path) -> list[Snapshot]:
    """Load and validate finalized historical snapshots from a local CSV file."""

    source = Path(path)
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        actual = set(reader.fieldnames or [])
        missing = _REQUIRED_COLUMNS - actual
        if missing:
            raise ValueError(f"input is missing columns: {sorted(missing)}")

        snapshots: list[Snapshot] = []
        for line_number, row in enumerate(reader, start=2):
            try:
                snapshot = Snapshot(
                    block_number=int(row["block_number"]),
                    block_timestamp=_parse_time(row["block_timestamp"], "block_timestamp"),
                    available_at_utc=_parse_time(row["available_at_utc"], "available_at_utc"),
                    price_usd=float(row["price_usd"]),
                    reserve_base=float(row["reserve_base"]),
                    reserve_quote=float(row["reserve_quote"]),
                    base_fee_gwei=float(row["base_fee_gwei"]),
                    priority_fee_gwei=float(row["priority_fee_gwei"]),
                    gas_used=int(row["gas_used"]),
                    eth_usd=float(row["eth_usd"]),
                )
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"invalid row {line_number}: {error}") from error
            snapshots.append(snapshot)

    validate_snapshots(snapshots)
    return snapshots


def validate_snapshots(snapshots: list[Snapshot]) -> None:
    """Validate order, market-state integrity, and temporal availability invariants."""

    if not snapshots:
        raise ValueError("at least one snapshot is required")

    previous_block = -1
    previous_available: datetime | None = None
    seen_blocks: set[int] = set()
    for snapshot in snapshots:
        if snapshot.block_number in seen_blocks:
            raise ValueError(f"duplicate block_number: {snapshot.block_number}")
        seen_blocks.add(snapshot.block_number)
        if snapshot.block_number <= previous_block:
            raise ValueError("block_number values must be strictly increasing")
        if snapshot.available_at_utc < snapshot.block_timestamp:
            raise ValueError("available_at_utc cannot precede block_timestamp")
        if previous_available is not None and snapshot.available_at_utc < previous_available:
            raise ValueError("available_at_utc values must be non-decreasing")
        if snapshot.price_usd <= 0:
            raise ValueError("price_usd must be positive")
        if snapshot.reserve_base <= 0 or snapshot.reserve_quote <= 0:
            raise ValueError("reserves must be positive")
        if snapshot.base_fee_gwei < 0 or snapshot.priority_fee_gwei < 0:
            raise ValueError("fee fields must be non-negative")
        if snapshot.gas_used < 0 or snapshot.eth_usd <= 0:
            raise ValueError("gas_used must be non-negative and eth_usd must be positive")
        previous_block = snapshot.block_number
        previous_available = snapshot.available_at_utc


def sha256_digest(path: str | Path) -> str:
    """Return a content digest for reproducibility reporting."""

    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
