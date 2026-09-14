CREATE TABLE IF NOT EXISTS intraday (
    stock_symbol TEXT,
    iv_date TEXT,
    compositeIV30 REAL,
    PRIMARY KEY (stock_symbol, iv_date)
) STRICT;
