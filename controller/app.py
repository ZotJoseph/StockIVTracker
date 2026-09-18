import datetime

from click import DateTime
from fastapi import FastAPI

import common.database


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/stocks/{symbol}")
def read_stock(symbol: str, iv_date : datetime.date | None = None) -> float:
    """returns stock iv at date, if date is None, returns the latest stock from the last 5 days if available"""

    database = common.database.DatabaseConnection()
    if iv_date is None:
        return database.getLatestIVFromStock(symbol)
    return database.getIVFromDate(symbol, iv_date)


@app.put("/stocks/{symbol}")
def update_stock(symbol: str, iv : float, iv_date : datetime.date):

    database = common.database.DatabaseConnection()
    database.updateDaily(symbol, iv, iv_date)

    return {
        "symbol": symbol,
        "composite_30_iv" : iv,
        "date": iv_date
    }


#TODO: get stock at date


#TODO: get all of a stock within 30 days

