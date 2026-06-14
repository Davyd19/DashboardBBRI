from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import IO, Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "BBRI.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
VALIDATION_DIR = ROOT / "outputs" / "validation"

REQUIRED_COLUMNS = [
    "Date",
    "Ticker",
    "Name",
    "Previous",
    "Open",
    "High",
    "Low",
    "Close",
    "Change",
    "Volume",
    "Value",
    "Frequency",
    "Offer",
    "OfferVolume",
    "Bid",
    "BidVolume",
    "ListedShares",
    "TradebleShares",
    "WeightForIndex",
    "ForeignSell",
    "ForeignBuy",
]

NUMERIC_COLUMNS = [
    "Previous",
    "Open",
    "High",
    "Low",
    "Close",
    "Change",
    "Volume",
    "Value",
    "Frequency",
    "IndexIndividual",
    "Offer",
    "OfferVolume",
    "Bid",
    "BidVolume",
    "ListedShares",
    "TradebleShares",
    "WeightForIndex",
    "ForeignSell",
    "ForeignBuy",
    "NonRegularVolume",
    "NonRegularValue",
    "NonRegularFrequency",
]


@dataclass
class ValidationReport:
    status: str
    errors: list[str]
    warnings: list[str]
    row_count: int
    column_count: int
    min_date: str | None
    max_date: str | None
    duplicate_dates: int
    open_zero_count: int
    missing_critical_count: int
    ticker_values: list[str]


def read_csv(source: str | Path | IO[bytes] | IO[str]) -> pd.DataFrame:
    return pd.read_csv(source, encoding="utf-8-sig")


def _empty_report(df: pd.DataFrame, errors: list[str], warnings: list[str]) -> ValidationReport:
    return ValidationReport(
        status="ERROR" if errors else "VALID",
        errors=errors,
        warnings=warnings,
        row_count=len(df),
        column_count=len(df.columns),
        min_date=None,
        max_date=None,
        duplicate_dates=0,
        open_zero_count=0,
        missing_critical_count=0,
        ticker_values=[],
    )


def validate_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, ValidationReport]:
    data = df.copy()
    errors: list[str] = []
    warnings: list[str] = []

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in data.columns]
    if missing_columns:
        errors.append(f"Kolom wajib tidak ditemukan: {', '.join(missing_columns)}")
        return data, _empty_report(data, errors, warnings)

    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    invalid_dates = int(data["Date"].isna().sum())
    if invalid_dates:
        errors.append(f"Terdapat {invalid_dates} baris dengan format Date tidak valid.")

    for col in NUMERIC_COLUMNS:
        if col in data.columns:
            before_na = data[col].isna().sum()
            data[col] = pd.to_numeric(data[col], errors="coerce")
            after_na = data[col].isna().sum()
            if after_na > before_na and col in REQUIRED_COLUMNS:
                errors.append(f"Kolom {col} memiliki nilai yang tidak dapat dikonversi ke angka.")

    ticker_values = sorted([str(x) for x in data["Ticker"].dropna().unique().tolist()])
    invalid_ticker = [x for x in ticker_values if x != "BBRI"]
    if invalid_ticker:
        errors.append(f"Ticker selain BBRI ditemukan: {', '.join(invalid_ticker)}")

    duplicate_dates = int(data["Date"].duplicated().sum()) if "Date" in data else 0
    if duplicate_dates:
        errors.append(f"Terdapat {duplicate_dates} duplicate date pada data harian.")

    critical_cols = ["Date", "Ticker", "Close", "High", "Low", "Volume", "Value", "ForeignBuy", "ForeignSell"]
    missing_critical_count = int(data[critical_cols].isna().sum().sum())
    if missing_critical_count:
        errors.append(f"Terdapat {missing_critical_count} missing value pada kolom kritis.")

    open_zero_count = int((data["Open"] == 0).sum())
    if open_zero_count:
        warnings.append(
            f"Terdapat {open_zero_count} baris Open = 0; nilai diproses dengan imputasi dari Previous atau Close hari sebelumnya."
        )

    non_positive_volume = int((data["Volume"] <= 0).sum())
    if non_positive_volume:
        errors.append(f"Terdapat {non_positive_volume} baris Volume <= 0.")

    invalid_ohlc = int(((data["High"] < data["Low"]) | (data["Close"] > data["High"]) | (data["Close"] < data["Low"])).sum())
    if invalid_ohlc:
        errors.append(f"Terdapat {invalid_ohlc} baris dengan konsistensi OHLC tidak valid.")

    if not data["Value"].dropna().empty:
        value_threshold = data["Value"].quantile(0.99) * 1.5
        value_outliers = int((data["Value"] > value_threshold).sum())
        if value_outliers:
            warnings.append(f"Terdapat {value_outliers} potensi outlier Value transaksi.")

    if not data["Volume"].dropna().empty:
        volume_threshold = data["Volume"].quantile(0.99) * 1.5
        volume_outliers = int((data["Volume"] > volume_threshold).sum())
        if volume_outliers:
            warnings.append(f"Terdapat {volume_outliers} potensi outlier Volume transaksi.")

    status = "ERROR" if errors else ("WARNING" if warnings else "VALID")
    report = ValidationReport(
        status=status,
        errors=errors,
        warnings=warnings,
        row_count=len(data),
        column_count=len(data.columns),
        min_date=data["Date"].min().strftime("%Y-%m-%d") if data["Date"].notna().any() else None,
        max_date=data["Date"].max().strftime("%Y-%m-%d") if data["Date"].notna().any() else None,
        duplicate_dates=duplicate_dates,
        open_zero_count=open_zero_count,
        missing_critical_count=missing_critical_count,
        ticker_values=ticker_values,
    )
    return data, report


def transform_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy().sort_values("Date").reset_index(drop=True)
    data["Open_Original"] = data["Open"]
    data["Open_Was_Imputed"] = data["Open"].eq(0)
    previous_clean = data["Previous"].where(data["Previous"] > 0)
    prior_close = data["Close"].shift(1).where(data["Close"].shift(1) > 0)
    data["Open_Clean"] = data["Open"].where(data["Open"] > 0, previous_clean)
    data["Open_Clean"] = data["Open_Clean"].fillna(prior_close)
    data["Daily_Return"] = data["Close"].pct_change()
    data["Intraday_Return"] = (data["Close"] - data["Open_Clean"]) / data["Open_Clean"]
    data["Net_Foreign_Flow"] = data["ForeignBuy"] - data["ForeignSell"]
    data["Trading_Value_Trillion"] = data["Value"] / 1_000_000_000_000
    data["Volume_Million"] = data["Volume"] / 1_000_000
    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA60"] = data["Close"].rolling(60).mean()
    data["Rolling_Volatility_20D"] = data["Daily_Return"].rolling(20).std() * np.sqrt(252)
    data["Rolling_Avg_Volume_20D"] = data["Volume"].rolling(20).mean()
    data["Rolling_Net_Foreign_20D"] = data["Net_Foreign_Flow"].rolling(20).sum()
    data["Volume_Ratio_20D"] = data["Volume"] / data["Rolling_Avg_Volume_20D"]
    data["Cumulative_Max_Close"] = data["Close"].cummax()
    data["Drawdown"] = (data["Close"] / data["Cumulative_Max_Close"]) - 1
    data["Drawdown_Zone"] = data["Drawdown"].apply(_drawdown_zone)
    data["Corporate_Action_Watch"] = data.apply(_corporate_action_watch, axis=1)
    data["Month"] = data["Date"].dt.to_period("M").astype(str)
    data["Year"] = data["Date"].dt.year
    data["Quarter"] = data["Date"].dt.to_period("Q").astype(str)
    data["Market_Status"] = data.apply(_classify_row, axis=1)
    return data


def _drawdown_zone(drawdown: float) -> str:
    if pd.notna(drawdown) and drawdown <= -0.20:
        return "Pressure Zone"
    if pd.notna(drawdown) and drawdown <= -0.10:
        return "Watch Zone"
    return "Normal Zone"


def _corporate_action_watch(row: pd.Series) -> str:
    drawdown = row.get("Drawdown", np.nan)
    rolling_foreign = row.get("Rolling_Net_Foreign_20D", np.nan)
    volume_ratio = row.get("Volume_Ratio_20D", np.nan)
    daily_return = row.get("Daily_Return", np.nan)
    volatility = row.get("Rolling_Volatility_20D", np.nan)

    if pd.notna(drawdown) and drawdown <= -0.20 and pd.notna(rolling_foreign) and rolling_foreign < 0 and pd.notna(volume_ratio) and volume_ratio >= 1:
        return "Buyback Watch"
    if pd.notna(rolling_foreign) and rolling_foreign < 0 and pd.notna(daily_return) and daily_return < 0:
        return "Market Communication Watch"
    if pd.notna(volatility) and volatility >= 0.45:
        return "Volatility Watch"
    return "Routine Monitoring"


def _classify_row(row: pd.Series) -> str:
    daily_return = row.get("Daily_Return", np.nan)
    drawdown = row.get("Drawdown", np.nan)
    volatility = row.get("Rolling_Volatility_20D", np.nan)
    rolling_foreign = row.get("Rolling_Net_Foreign_20D", np.nan)
    volume_ratio = row.get("Volume_Ratio_20D", np.nan)
    if pd.notna(drawdown) and drawdown <= -0.20 and pd.notna(rolling_foreign) and rolling_foreign < 0:
        return "Pressure"
    if pd.notna(daily_return) and daily_return <= -0.03:
        return "Watch"
    if pd.notna(volatility) and volatility >= 0.45:
        return "Watch"
    if pd.notna(volume_ratio) and volume_ratio >= 1.5 and pd.notna(daily_return) and daily_return < 0:
        return "Watch"
    return "Normal"


def build_data_mart(data: pd.DataFrame) -> dict[str, pd.DataFrame]:
    dim_date = data[["Date", "Year", "Quarter", "Month"]].drop_duplicates().copy()
    dim_date["Date_Key"] = dim_date["Date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["Tanggal"] = dim_date["Date"].dt.strftime("%Y-%m-%d")
    dim_date["Hari"] = dim_date["Date"].dt.day_name()
    dim_date["Bulan"] = dim_date["Date"].dt.month
    dim_date = dim_date[["Date_Key", "Tanggal", "Hari", "Bulan", "Quarter", "Year"]].rename(columns={"Year": "Tahun"})

    latest = data.sort_values("Date").iloc[-1]
    dim_stock = pd.DataFrame(
        [
            {
                "Stock_Key": 1,
                "Ticker": latest["Ticker"],
                "Nama_Emiten": latest["Name"],
                "ListedShares": latest.get("ListedShares"),
                "TradebleShares": latest.get("TradebleShares"),
                "WeightForIndex": latest.get("WeightForIndex"),
            }
        ]
    )

    fact = data.copy()
    fact["Date_Key"] = fact["Date"].dt.strftime("%Y%m%d").astype(int)
    fact["Stock_Key"] = 1
    fact_cols = [
        "Date_Key",
        "Stock_Key",
        "Previous",
        "Open",
        "Open_Original",
        "Open_Was_Imputed",
        "Open_Clean",
        "High",
        "Low",
        "Close",
        "Change",
        "Daily_Return",
        "Intraday_Return",
        "Volume",
        "Value",
        "Frequency",
        "Offer",
        "OfferVolume",
        "Bid",
        "BidVolume",
        "ForeignBuy",
        "ForeignSell",
        "Net_Foreign_Flow",
        "MA20",
        "MA60",
        "Rolling_Volatility_20D",
        "Rolling_Avg_Volume_20D",
        "Rolling_Net_Foreign_20D",
        "Volume_Ratio_20D",
        "Drawdown",
        "Drawdown_Zone",
        "Corporate_Action_Watch",
        "Market_Status",
    ]
    fact = fact[[col for col in fact_cols if col in fact.columns]]
    return {
        "Fact_DailyMarketTrading": fact,
        "Dim_Date": dim_date,
        "Dim_Stock": dim_stock,
    }


def generate_alerts(data: pd.DataFrame) -> list[dict[str, str]]:
    latest = data.sort_values("Date").iloc[-1]
    recent = data.sort_values("Date").tail(20)
    alerts: list[dict[str, str]] = []

    period_return = (latest["Close"] / recent.iloc[0]["Close"]) - 1 if len(recent) > 1 else 0
    net_foreign_20d = latest.get("Rolling_Net_Foreign_20D", recent["Net_Foreign_Flow"].sum())
    if pd.isna(net_foreign_20d):
        net_foreign_20d = recent["Net_Foreign_Flow"].sum()
    avg_volume_20d = recent["Volume"].mean()
    latest_volume = latest["Volume"]
    volume_ratio_20d = latest.get("Volume_Ratio_20D", latest_volume / avg_volume_20d if avg_volume_20d else np.nan)

    if period_return <= -0.05 and latest["Drawdown"] <= -0.15:
        alerts.append(
            {
                "level": "High",
                "condition": "Tekanan harga meningkat",
                "insight": "Return 20 hari negatif dan drawdown berada pada area tekanan.",
                "recommendation": "Lakukan monitoring ketat dan siapkan kajian komunikasi pasar.",
            }
        )
    if net_foreign_20d < 0:
        alerts.append(
            {
                "level": "Medium",
                "condition": "Foreign sell pressure",
                "insight": "Akumulasi net foreign flow 20 hari terakhir berada di zona negatif.",
                "recommendation": "Investor Relations perlu memantau narasi pasar dan minat investor asing.",
            }
        )
    if pd.notna(volume_ratio_20d) and volume_ratio_20d >= 1.5 and latest["Daily_Return"] < 0:
        alerts.append(
            {
                "level": "Medium",
                "condition": "Volume tinggi saat harga turun",
                "insight": "Transaksi meningkat saat return harian negatif, mengindikasikan tekanan distribusi.",
                "recommendation": "Evaluasi risiko likuiditas dan pantau transaksi beberapa hari berikutnya.",
            }
        )
    if pd.notna(latest["Rolling_Volatility_20D"]) and latest["Rolling_Volatility_20D"] >= 0.45:
        alerts.append(
            {
                "level": "Medium",
                "condition": "Volatilitas meningkat",
                "insight": "Volatilitas 20 hari berada di atas batas watch dashboard.",
                "recommendation": "Hindari keputusan aksi agresif tanpa validasi fundamental dan regulasi.",
            }
        )
    if latest["Drawdown"] <= -0.20 and pd.notna(volume_ratio_20d) and volume_ratio_20d >= 1:
        alerts.append(
            {
                "level": "Watch",
                "condition": "Buyback Watch",
                "insight": "Harga berada dalam drawdown tinggi namun likuiditas transaksi masih memadai.",
                "recommendation": "Pertimbangkan kajian awal buyback sebagai opsi, bukan keputusan final.",
            }
        )
    if not alerts:
        alerts.append(
            {
                "level": "Normal",
                "condition": "Kondisi pasar stabil",
                "insight": "Tidak ada indikator tekanan utama berdasarkan rule dashboard.",
                "recommendation": "Lanjutkan monitoring rutin melalui dashboard.",
            }
        )
    return alerts


def summarize_metrics(data: pd.DataFrame) -> dict[str, Any]:
    ordered = data.sort_values("Date")
    latest = ordered.iloc[-1]
    first = ordered.iloc[0]
    recent = ordered.tail(20)
    return {
        "latest_date": latest["Date"].strftime("%Y-%m-%d"),
        "first_date": first["Date"].strftime("%Y-%m-%d"),
        "latest_close": float(latest["Close"]),
        "period_return": float(latest["Close"] / first["Close"] - 1),
        "return_20d": float(latest["Close"] / recent.iloc[0]["Close"] - 1) if len(recent) > 1 else 0.0,
        "total_volume": float(ordered["Volume"].sum()),
        "total_value": float(ordered["Value"].sum()),
        "net_foreign_flow": float(ordered["Net_Foreign_Flow"].sum()),
        "net_foreign_flow_20d": float(recent["Net_Foreign_Flow"].sum()),
        "rolling_net_foreign_20d": float(latest["Rolling_Net_Foreign_20D"]) if pd.notna(latest["Rolling_Net_Foreign_20D"]) else None,
        "volume_ratio_20d": float(latest["Volume_Ratio_20D"]) if pd.notna(latest["Volume_Ratio_20D"]) else None,
        "ma20": float(latest["MA20"]) if pd.notna(latest["MA20"]) else None,
        "ma60": float(latest["MA60"]) if pd.notna(latest["MA60"]) else None,
        "max_drawdown": float(ordered["Drawdown"].min()),
        "latest_drawdown": float(latest["Drawdown"]),
        "drawdown_zone": str(latest["Drawdown_Zone"]),
        "corporate_action_watch": str(latest["Corporate_Action_Watch"]),
        "latest_volatility": float(latest["Rolling_Volatility_20D"]) if pd.notna(latest["Rolling_Volatility_20D"]) else None,
        "latest_status": str(latest["Market_Status"]),
    }


def run_pipeline(
    source: str | Path | IO[bytes] | IO[str] = RAW_PATH,
    write_outputs: bool = True,
) -> tuple[pd.DataFrame, ValidationReport, dict[str, pd.DataFrame], dict[str, Any], list[dict[str, str]]]:
    raw = read_csv(source)
    validated, report = validate_dataframe(raw)
    if report.status == "ERROR":
        return validated, report, {}, {}, []
    transformed = transform_dataframe(validated)
    mart = build_data_mart(transformed)
    metrics = summarize_metrics(transformed)
    alerts = generate_alerts(transformed)

    if write_outputs:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
        _safe_to_csv(transformed, PROCESSED_DIR / "bbri_daily_market_processed.csv")
        for name, frame in mart.items():
            _safe_to_csv(frame, PROCESSED_DIR / f"{name}.csv")
        _safe_write_text(VALIDATION_DIR / "validation_report.json", json.dumps(asdict(report), indent=2))
        _safe_write_text(VALIDATION_DIR / "metrics_summary.json", json.dumps(metrics, indent=2))
        _safe_write_text(VALIDATION_DIR / "alerts.json", json.dumps(alerts, indent=2))
    return transformed, report, mart, metrics, alerts


def _safe_to_csv(frame: pd.DataFrame, path: Path) -> None:
    csv_text = frame.to_csv(index=False)
    _safe_write_text(path, csv_text)


def _safe_write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text, encoding="utf-8")
        return path
    except PermissionError:
        fallback = path.with_name(f"{path.stem}_generated{path.suffix}")
        fallback.write_text(text, encoding="utf-8")
        return fallback


if __name__ == "__main__":
    transformed_df, validation_report, mart_tables, summary, alert_rows = run_pipeline()
    print(json.dumps(asdict(validation_report), indent=2))
    print(json.dumps(summary, indent=2))
    print(f"Generated processed rows: {len(transformed_df)}")
    print(f"Generated mart tables: {', '.join(mart_tables.keys())}")
