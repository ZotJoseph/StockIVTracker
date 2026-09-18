from click import DateTime
from fastapi import FastAPI

import common.database


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/stocks")
def read_stock_symbol(symbol: str) -> float:
    database = common.database.DatabaseConnection()
    return database.getLatestIVFromStock(symbol)

