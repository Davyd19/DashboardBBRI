-- Data mart schema for BI Market Intelligence & Corporate Action Support BBRI.
-- This SQL is provided as a physical design reference; the implemented project
-- exports the same structures as CSV files under data/processed/.

CREATE TABLE Dim_Date (
    Date_Key INT PRIMARY KEY,
    Tanggal DATE NOT NULL,
    Hari VARCHAR(20),
    Bulan INT,
    Quarter VARCHAR(10),
    Tahun INT
);

CREATE TABLE Dim_Stock (
    Stock_Key INT PRIMARY KEY,
    Ticker VARCHAR(10) NOT NULL,
    Nama_Emiten VARCHAR(255),
    ListedShares NUMERIC,
    TradebleShares NUMERIC,
    WeightForIndex NUMERIC
);

CREATE TABLE Fact_DailyMarketTrading (
    Date_Key INT REFERENCES Dim_Date(Date_Key),
    Stock_Key INT REFERENCES Dim_Stock(Stock_Key),
    Previous NUMERIC,
    Open NUMERIC,
    Open_Clean NUMERIC,
    High NUMERIC,
    Low NUMERIC,
    Close NUMERIC,
    Change NUMERIC,
    Daily_Return NUMERIC,
    Intraday_Return NUMERIC,
    Volume NUMERIC,
    Value NUMERIC,
    Frequency NUMERIC,
    Offer NUMERIC,
    OfferVolume NUMERIC,
    Bid NUMERIC,
    BidVolume NUMERIC,
    ForeignBuy NUMERIC,
    ForeignSell NUMERIC,
    Net_Foreign_Flow NUMERIC,
    Rolling_Volatility_20D NUMERIC,
    Drawdown NUMERIC,
    Market_Status VARCHAR(20),
    PRIMARY KEY (Date_Key, Stock_Key)
);
