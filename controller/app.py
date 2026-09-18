import datetime

from click import DateTime
from fastapi import FastAPI

import common.database


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/stocks/{symbol}")
def read_stock_symbol(symbol: str) -> float:
    database = common.database.DatabaseConnection()
    return database.getLatestIVFromStock(symbol)


@app.put("/stocks/{symbol}")
def update_stock(symbol: str, iv : float, iv_date : datetime.date):

    database = common.database.DatabaseConnection()
    database.updateDaily(symbol, iv, iv_date)

    return {
        "symbol": symbol,
        "composite_30_iv" : iv,
        "date": datetime.date
    }
#TODO: get stock at date
#TODO: update stock at date

#TODO: get all of a stock within 30 days

