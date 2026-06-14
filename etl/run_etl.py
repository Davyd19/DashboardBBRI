from __future__ import annotations

import argparse
from pathlib import Path

from pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ETL for BBRI BI dashboard.")
    parser.add_argument("--input", default=str(Path(__file__).resolve().parents[1] / "data" / "raw" / "BBRI.csv"))
    args = parser.parse_args()
    data, report, mart, metrics = run_pipeline(args.input)
    print(f"Validation status: {report.status}")
    print(f"Rows: {report.row_count}, Columns: {report.column_count}")
    print(f"Date range: {report.min_date} to {report.max_date}")
    print(f"Duplicate dates: {report.duplicate_dates}")
    print(f"Open = 0 rows: {report.open_zero_count}")
    if report.errors:
        print("Errors:")
        for item in report.errors:
            print(f"- {item}")
    if report.warnings:
        print("Warnings:")
        for item in report.warnings:
            print(f"- {item}")
    if report.status != "ERROR":
        print(f"Processed rows: {len(data)}")
        print(f"Mart tables: {', '.join(mart.keys())}")
        print(f"Latest close: {metrics['latest_close']}")


if __name__ == "__main__":
    main()
