import sqlite3
import unittest
from datetime import datetime
from pathlib import Path

import Backend.databaseUpdater
from API.compositeIVFinder import CompositeIVResult
from Backend.databaseUpdater import DatabaseUpdater, DATABASE_NAME


Backend.databaseUpdater.DATABASE_NAME = "test_stocks.db"



def make_fresh_db() -> DatabaseUpdater:
    database = DatabaseUpdater()
    database.makeDatabase()
    return database

def wipe_db(database : DatabaseUpdater):
    cursor = database.connection.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';""")
    for row in cursor:
        cursor.execute("""DROP TABLE IF EXISTS {:table_name};""", {'table_name' : row[0]})


class TestDatabase(unittest.TestCase):

    def test_add_to_database(self):
        database = make_fresh_db()

        fictitious_stock = CompositeIVResult(symbol = "john_stocks", iv = .8, datetime = datetime.now())

        database.insertStock(fictitious_stock)
        database.update_stock(fictitious_stock)

if __name__ == '__main__':
    unittest.main()
