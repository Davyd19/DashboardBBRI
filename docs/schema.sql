-- MySQL/MariaDB schema for database dashboard_bbri.
-- The ETL script creates these tables automatically if they do not exist.

CREATE TABLE IF NOT EXISTS dim_date (
    Date_Key INT PRIMARY KEY,
    Tanggal DATE NOT NULL,
    Hari VARCHAR(20),
    Bulan INT,
    Quarter VARCHAR(10),
    Tahun INT
);

CREATE TABLE IF NOT EXISTS dim_stock (
    Stock_Key INT PRIMARY KEY,
    Ticker VARCHAR(10) NOT NULL,
    Nama_Emiten VARCHAR(255),
    ListedShares DOUBLE,
    TradebleShares DOUBLE,
    WeightForIndex DOUBLE
);

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
);
