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
from datetime import datetime, timedelta
from pathlib import Path

from services.compositeIVFinder import CompositeIVResult

DATABASE_NAME = "stocks.db"

class DatabaseUpdater:
    def __init__(self):
        self.connection = sqlite3.connect(Path(DATABASE_NAME))
        self.connection.execute('PRAGMA foreign_keys = ON;')

    def __delete__(self, instance):
        self.connection.commit()
        self.connection.close()

    def makeDatabase(self):
        """
        make the Stocks database

        stocks: just stock symbols for foreign key references
        intraday: one IV a day for each stock (will update every poll, but will take the last poll, usually right before market closes)
        daily: all polls of a day is kept here
        TODO: make a separate script that deletes old daily
        """
        with open("schema.sql") as f:
            self.connection.executescript(f.read()) #executescript does NOT return a cursor, self.connection.close() ≠ cursor.close()...
        self.connection.commit()

    def insertStock(self, composite_iv_result: CompositeIVResult):
        """
        insert stock symbol into stock table for the first time
        """
        stock_symbol = composite_iv_result.symbol
        cursor = self.connection.execute("""
        INSERT INTO stocks (stock_symbol)
            VALUES (:stock_symbol)
            ON CONFLICT (stock_symbol) DO NOTHING
        """, {'stock_symbol' : stock_symbol})

        self.connection.commit()
        cursor.close()

    def insertDaily(self, composite_iv_result: CompositeIVResult):
        """
        inserts data from the composite_iv_result onto the daily table
        """
        stock_symbol = composite_iv_result.symbol
        compositeIV30 = composite_iv_result.iv
        date = str(composite_iv_result.datetime.date())
        time = composite_iv_result.datetime.strftime('%H:%M')

        cursor = self.connection.execute("""
                                         INSERT INTO daily (stock_symbol, iv_date, iv_time, compositeIV30)
                                         VALUES (:stock_symbol, :date, :time, :compositeIV30)
                                            ON CONFLICT(stock_symbol, iv_date, iv_time)
                                         DO UPDATE SET compositeIV30 = excluded.compositeIV30;
                                         """,
                                         {'stock_symbol': stock_symbol, 'date': date, 'time': time,
                                          'compositeIV30': compositeIV30})

        self.connection.commit()
        cursor.close()

    def insertIntraday(self, composite_iv_result: CompositeIVResult):
        """
        inserts data from composite_iv_result onto the intraday table

        """
        stock_symbol = composite_iv_result.symbol
        compositeIV30 = composite_iv_result.iv
        date = str(composite_iv_result.datetime.date())

        cursor = self.connection.execute("""
                                         INSERT INTO intraday (stock_symbol, iv_date, compositeIV30)
                                         VALUES (:stock_symbol, :date, :compositeIV30)
                                         ON CONFLICT(stock_symbol, iv_date)
                                         DO UPDATE SET compositeIV30 = excluded.compositeIV30;""",
                                         {'stock_symbol': stock_symbol, 'date': date,
                                          'compositeIV30': compositeIV30}
                                         )
        self.connection.commit()
        cursor.close()


    def getLatestIVFromStock(self, stock_symbol : str):
        """
        returns an iv of the stock that is no later than one week
        if it is/no iv exist, return None
        """
        cursor = self.connection.execute("""
            SELECT compositeIV30, iv_date
            FROM intraday
            WHERE stock_symbol = :stock_symbol
            ORDER BY iv_date DESC
            LIMIT 1;
        """, {'stock_symbol' : stock_symbol})

        potential_iv_time = cursor.fetchone()
        if not potential_iv_time or datetime.strptime(potential_iv_time[1], '%Y-%m-%d') < datetime.now() - timedelta(weeks = 1):
            return None

        return potential_iv_time[0]

    def update_stock(self, compositeIVResult : CompositeIVResult):
        """
        given compositeIVResult (including symbol, iv, and date),
        add stock to stock table,
        add to daily table,
        and replace the intraday value with latest IV
        """
        self.insertStock(compositeIVResult)
        self.insertDaily(compositeIVResult)
        self.insertIntraday(compositeIVResult)

