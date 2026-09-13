CREATE TABLE IF NOT EXISTS stocks (
    stock_symbol TEXT PRIMARY KEY NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS intraday (
    stock_symbol TEXT,
    iv_date TEXT,
    compositeIV30 REAL,
    PRIMARY KEY (stock_symbol, iv_date),
    FOREIGN KEY (stock_symbol) REFERENCES stocks(stock_symbol)
) STRICT;

CREATE TABLE IF NOT EXISTS daily (
    stock_symbol TEXT,
    iv_date TEXT,
    iv_time TEXT,
    compositeIV30 REAL,
    PRIMARY KEY (stock_symbol, iv_date, iv_time),
    FOREIGN KEY (stock_symbol) REFERENCES stocks(stock_symbol)
) STRICT;