"""
handles updating the database

- makes the database

- put daily values inside the daily table
- update the last value inside intraday table

- retrieve the last available IV value of a stock for the purpose of checking max/min
    - try finding from database of the current day
    - if that's impossible (top row of daily is null) pull from no more than a week ago
    - if that doesn't exist, return null value (we don't have a good latest value)
"""

import sqlite3
from datetime import datetime


class databaseUpdater:
    def __init__(self):
        self.connection = sqlite3.connect("stocks.db")
        self.connection.execute('PRAGMA foreign_keys = ON;')

    def makeDatabase(self):
        """
        make the Stocks database

        stocks: just stock symbols for foreign key references
        intraday: one IV a day for each stock (will update every poll, but will take the last poll, usually right before market closes)
        daily: all polls of a day is kept here
        TODO: make a separate script that deletes old daily
        """
        cursor = self.connection.execute("""
                                         CREATE TABLE stocks
                                         (
                                             stock_symbol TEXT PRIMARY KEY NOT NULL
                                         ) STRICT;
                                         """)

        cursor.execute("""
                       CREATE TABLE intraday
                       (
                           stock_symbol  TEXT,
                           date          TEXT,
                           compositeIV30 TEXT,
                           PRIMARY KEY (stock_symbol, date, time),
                           FOREIGN KEY (stock_symbol) REFERENCES stocks (stock_symbol)

                       ) STRICT;
                       """)

        cursor.execute("""
                       CREATE TABLE daily
                       (
                           stock_symbol  TEXT,
                           date          TEXT,
                           time          TEXT,
                           compositeIV30 TEXT,
                           PRIMARY KEY (stock_symbol, date),
                           FOREIGN KEY (stock_symbol) REFERENCES stocks (stock_symbol)
                       ) STRICT;
                       """)

        cursor.close()

    def insertDaily(self, stock_symbol: str, date_and_time: datetime, compositeIV30: int):
        date = str(date_and_time.date())
        time = date_and_time.strftime('%H:%M')

        cursor = self.connection.execute("""
                                         INSERT INTO daily (stock_symbol, date, time, compositeIV30)
                                         VALUES (:stock_symbol, :date, :time, :compositeIV30);
                                         """,
                                         {'stock_symbol': stock_symbol, 'date': date, 'time': time,
                                          'compositeIV30': compositeIV30})
        cursor.close()

    def insertIntraday(self, stock_symbol : str, date_and_time : datetime, compositeIV30 : int):
        date = str(date_and_time.date())
        cursor = self.connection.execute("""
            INSERT INTO intraday (stock_symbol, date, compositeIV30)""")



x = databaseUpdater()
