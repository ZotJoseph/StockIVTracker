import datetime
from fastapi import FastAPI

from common.database import DatabaseConnection, StockIV


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/stocks/{symbol}")
def read_stock(symbol: str, iv_date : datetime.date = datetime.date.today()) -> StockIV:
    """returns stock iv at date, date default to current day"""

    database = DatabaseConnection()
    return StockIV(symbol, database.getIVFromDate(symbol, iv_date), iv_date)


@app.put("/stocks/{symbol}")
def update_stock(symbol: str, iv : float, iv_date : datetime.date):
    """updates stock iv of symbol at date"""
    database = DatabaseConnection()
    database.updateDaily(symbol, iv, iv_date)
    return StockIV(symbol, iv, iv_date)


@app.get("/stocks/fetch30day/{symbol}")
def read_stock_30_days(symbol: str) -> list[StockIV]:
    """returns stock composite 30 day iv of past 30 days"""
    database = DatabaseConnection()
    return database.getIVOfPast30Days(symbol)


