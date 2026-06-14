from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "etl"))

from pipeline import RAW_PATH, read_csv, run_pipeline, validate_dataframe  # noqa: E402


OUTPUT = PROJECT_ROOT / "outputs" / "validation" / "test_report.json"


def safe_write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text, encoding="utf-8")
        return path
    except PermissionError:
        fallback = path.with_name(f"{path.stem}_generated{path.suffix}")
        fallback.write_text(text, encoding="utf-8")
        return fallback


def scenario_valid() -> dict:
    data, report, mart, metrics, alerts = run_pipeline(RAW_PATH, write_outputs=False)
    return {
        "scenario": "valid_default_bbri_csv",
        "status": report.status,
        "row_count": report.row_count,
        "column_count": report.column_count,
        "min_date": report.min_date,
        "max_date": report.max_date,
        "duplicate_dates": report.duplicate_dates,
        "open_zero_count": report.open_zero_count,
        "mart_tables": list(mart.keys()),
        "latest_close": metrics.get("latest_close"),
        "alert_count": len(alerts),
    }


def scenario_missing_column() -> dict:
    df = read_csv(RAW_PATH)
    df = df.drop(columns=["Close"])
    _, report = validate_dataframe(df)
    return {"scenario": "missing_required_column", "status": report.status, "errors": report.errors}


def scenario_wrong_ticker() -> dict:
    df = read_csv(RAW_PATH)
    df.loc[0, "Ticker"] = "BBCA"
    _, report = validate_dataframe(df)
    return {"scenario": "wrong_ticker", "status": report.status, "errors": report.errors}


def scenario_duplicate_date() -> dict:
    df = read_csv(RAW_PATH)
    df.loc[1, "Date"] = df.loc[0, "Date"]
    _, report = validate_dataframe(df)
    return {"scenario": "duplicate_date", "status": report.status, "errors": report.errors}


def main() -> None:
    results = [
        scenario_valid(),
        scenario_missing_column(),
        scenario_wrong_ticker(),
        scenario_duplicate_date(),
    ]
    safe_write_text(OUTPUT, json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
