"""
handles updating the database

- makes the database

- put daily values inside the daily table
- update the last value inside intraday table

- retrieve the last available IV value of a stock for the purpose of checking max/min
    - pull the closest iv from no more than a week ago
    - if that doesn't exist, return null value (we don't have a good latest value)
"""

import sqlite3
from datetime import datetime

from API.compositeIVFinder import CompositeIVResult


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
                           iv_date  TEXT,
                           compositeIV30 TEXT,
                           PRIMARY KEY (stock_symbol, iv_date),
                           FOREIGN KEY (stock_symbol) REFERENCES stocks (stock_symbol)

                       ) STRICT;
                       """)

        cursor.execute("""
                       CREATE TABLE daily
                       (
                           stock_symbol  TEXT,
                           iv_date  TEXT,
                           iv_time          TEXT,
                           compositeIV30 TEXT,
                           PRIMARY KEY (stock_symbol, iv_date, iv_time),
                           FOREIGN KEY (stock_symbol) REFERENCES stocks (stock_symbol)
                       ) STRICT;
                       """)

        cursor.close()

    def insertDaily(self, composite_iv_result: CompositeIVResult):
        """
        inserts data from the composite_iv_result onto the daily database
        """
        stock_symbol = composite_iv_result.symbol
        compositeIV30 = composite_iv_result.iv
        date = str(composite_iv_result.datetime.date())
        time = composite_iv_result.datetime.strftime('%H:%M')

        cursor = self.connection.execute("""
                                         INSERT INTO daily (stock_symbol, iv_date, iv_time, compositeIV30)
                                         VALUES (:stock_symbol, :date, :time, :compositeIV30);
                                         """,
                                         {'stock_symbol': stock_symbol, 'date': date, 'time': time,
                                          'compositeIV30': compositeIV30})
        cursor.close()

    def insertIntraday(self, composite_iv_result: CompositeIVResult):
        """
        inserts data from composite_iv_result onto the intraday databasex

        """
        stock_symbol = composite_iv_result.symbol
        compositeIV30 = composite_iv_result.iv
        date = str(composite_iv_result.datetime.date())

        cursor = self.connection.execute("""
                                         INSERT INTO intraday (stock_symbol, iv_date, compositeIV30)
                                         VALUES (:stock_symbol, :date, :compositIV30)
                                         ON CONFLICT(stock_symbol, date)
                                         DO UPDATE SET compositeIV30 = excluded.compositeIV30;""",
                                         {'stock_symbol': stock_symbol, 'date': date,
                                          'compositeIV30': compositeIV30}
                                         )
        cursor.close()


    def getLatestIVFromStock(self, stock_symbol : str):
        cursor = self.connection.execute("""
            SELECT (compositeIV30, iv_date)
            FROM intraday
            WHERE stock_symbol = :stock_symbol
            ORDER BY date DESC;
        """, {'stock_symbol' : stock_symbol})



x = databaseUpdater()
