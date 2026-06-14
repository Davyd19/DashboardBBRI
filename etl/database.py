from __future__ import annotations

import os
from typing import Any

import pandas as pd


TABLE_MAP = {
    "Dim_Date": "dim_date",
    "Dim_Stock": "dim_stock",
    "Fact_DailyMarketTrading": "fact_daily_market_trading",
}


def db_config() -> dict[str, Any]:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "dashboard_bbri"),
        "charset": "utf8mb4",
        "autocommit": False,
    }


def get_connection():
    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError("Dependency pymysql belum terinstall. Jalankan pip install -r requirements.txt.") from exc
    return pymysql.connect(**db_config())


def create_tables(connection=None) -> None:
    own_connection = connection is None
    conn = connection or get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS dim_date (
                    Date_Key INT PRIMARY KEY,
                    Tanggal DATE NOT NULL,
                    Hari VARCHAR(20),
                    Bulan INT,
                    Quarter VARCHAR(10),
                    Tahun INT
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS dim_stock (
                    Stock_Key INT PRIMARY KEY,
                    Ticker VARCHAR(10) NOT NULL,
                    Nama_Emiten VARCHAR(255),
                    ListedShares DOUBLE,
                    TradebleShares DOUBLE,
                    WeightForIndex DOUBLE
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS fact_daily_market_trading (
                    Date_Key INT NOT NULL,
                    Stock_Key INT NOT NULL,
                    Previous DOUBLE,
                    `Open` DOUBLE,
                    Open_Original DOUBLE,
                    Open_Was_Imputed BOOLEAN,
                    Open_Clean DOUBLE,
                    High DOUBLE,
                    Low DOUBLE,
                    `Close` DOUBLE,
                    `Change` DOUBLE,
                    Daily_Return DOUBLE,
                    Intraday_Return DOUBLE,
                    Volume DOUBLE,
                    `Value` DOUBLE,
                    Frequency DOUBLE,
                    Offer DOUBLE,
                    OfferVolume DOUBLE,
                    Bid DOUBLE,
                    BidVolume DOUBLE,
                    ForeignBuy DOUBLE,
                    ForeignSell DOUBLE,
                    Net_Foreign_Flow DOUBLE,
                    MA20 DOUBLE,
                    MA60 DOUBLE,
                    Rolling_Volatility_20D DOUBLE,
                    Rolling_Avg_Volume_20D DOUBLE,
                    Rolling_Net_Foreign_20D DOUBLE,
                    Volume_Ratio_20D DOUBLE,
                    Drawdown DOUBLE,
                    Drawdown_Zone VARCHAR(30),
                    Corporate_Action_Watch VARCHAR(50),
                    Market_Status VARCHAR(20),
                    PRIMARY KEY (Date_Key, Stock_Key),
                    CONSTRAINT fk_fact_date FOREIGN KEY (Date_Key) REFERENCES dim_date(Date_Key),
                    CONSTRAINT fk_fact_stock FOREIGN KEY (Stock_Key) REFERENCES dim_stock(Stock_Key)
                )
                """
            )
        conn.commit()
    finally:
        if own_connection:
            conn.close()


def _clean_records(frame: pd.DataFrame) -> list[tuple[Any, ...]]:
    data = frame.copy()
    for column in data.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns:
        data[column] = data[column].dt.strftime("%Y-%m-%d")
    data = data.astype(object).where(pd.notna(data), None)
    return [tuple(row) for row in data.itertuples(index=False, name=None)]


def _insert_frame(cursor, table_name: str, frame: pd.DataFrame) -> None:
    columns = list(frame.columns)
    column_sql = ", ".join(f"`{column}`" for column in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"INSERT INTO `{table_name}` ({column_sql}) VALUES ({placeholders})"
    records = _clean_records(frame)
    if records:
        cursor.executemany(sql, records)


def load_data_mart(mart: dict[str, pd.DataFrame]) -> None:
    conn = get_connection()
    try:
        create_tables(conn)
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM fact_daily_market_trading")
            cursor.execute("DELETE FROM dim_stock")
            cursor.execute("DELETE FROM dim_date")
            _insert_frame(cursor, TABLE_MAP["Dim_Date"], mart["Dim_Date"])
            _insert_frame(cursor, TABLE_MAP["Dim_Stock"], mart["Dim_Stock"])
            _insert_frame(cursor, TABLE_MAP["Fact_DailyMarketTrading"], mart["Fact_DailyMarketTrading"])
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def read_fact_data() -> pd.DataFrame:
    conn = get_connection()
    try:
        query = """
            SELECT
                d.Tanggal AS Date,
                s.Ticker,
                s.Nama_Emiten AS Name,
                f.Previous,
                f.`Open`,
                f.Open_Original,
                f.Open_Was_Imputed,
                f.Open_Clean,
                f.High,
                f.Low,
                f.`Close`,
                f.`Change`,
                f.Daily_Return,
                f.Intraday_Return,
                f.Volume,
                f.`Value`,
                f.Frequency,
                f.Offer,
                f.OfferVolume,
                f.Bid,
                f.BidVolume,
                f.ForeignBuy,
                f.ForeignSell,
                f.Net_Foreign_Flow,
                f.MA20,
                f.MA60,
                f.Rolling_Volatility_20D,
                f.Rolling_Avg_Volume_20D,
                f.Rolling_Net_Foreign_20D,
                f.Volume_Ratio_20D,
                f.Drawdown,
                f.Drawdown_Zone,
                f.Corporate_Action_Watch,
                f.Market_Status
            FROM fact_daily_market_trading f
            JOIN dim_date d ON d.Date_Key = f.Date_Key
            JOIN dim_stock s ON s.Stock_Key = f.Stock_Key
            ORDER BY d.Tanggal
        """
        data = pd.read_sql(query, conn)
    finally:
        conn.close()
    if data.empty:
        raise RuntimeError("Tabel database masih kosong. Jalankan etl/run_etl.py terlebih dahulu.")
    data["Date"] = pd.to_datetime(data["Date"])
    data["Open_Was_Imputed"] = data["Open_Was_Imputed"].astype(bool)
    data["Year"] = data["Date"].dt.year
    data["Quarter"] = data["Date"].dt.to_period("Q").astype(str)
    data["Month"] = data["Date"].dt.to_period("M").astype(str)
    return data
