from __future__ import annotations

from pathlib import Path

import pytest

from defi_trend.backtest import run_backtest, write_ledger
from defi_trend.cli import generate_sample
from defi_trend.config import load_config
from defi_trend.validation import load_snapshots


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_generated_sample_validates(tmp_path: Path) -> None:
    sample = tmp_path / "sample.csv"
    generate_sample(sample, rows=36)
    snapshots = load_snapshots(sample)
    assert len(snapshots) == 36
    assert snapshots[0].block_number < snapshots[-1].block_number


def test_duplicate_block_is_rejected(tmp_path: Path) -> None:
    sample = tmp_path / "sample.csv"
    generate_sample(sample, rows=24)
    lines = sample.read_text(encoding="utf-8").splitlines()
    first_data = lines[1].split(",")
    second_data = lines[2].split(",")
    second_data[0] = first_data[0]
    lines[2] = ",".join(second_data)
    sample.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate block_number"):
        load_snapshots(sample)


def test_paper_backtest_writes_audit_ledger(tmp_path: Path) -> None:
    sample = tmp_path / "sample.csv"
    output = tmp_path / "ledger.csv"
    generate_sample(sample, rows=48)
    snapshots = load_snapshots(sample)
    config = load_config(PROJECT_ROOT / "configs" / "research.example.json")
    ledger = run_backtest(snapshots, config)
    write_ledger(ledger, output)
    assert output.exists()
    assert len(ledger) == len(snapshots)
    assert any(row.status == "WARMUP" for row in ledger)
    assert any(row.status in {"PAPER_FILLED", "NO_TRADE", "REJECTED"} for row in ledger)
    assert "decision_time" in output.read_text(encoding="utf-8").splitlines()[0]
