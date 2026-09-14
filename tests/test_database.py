import unittest
from datetime import datetime, timedelta

import common.database
from controller.composite_iv_finder import CompositeIVResult
from common.database import DatabaseUpdater


common.database.DATABASE_NAME = "test_stocks.db"


def make_fresh_db() -> DatabaseUpdater:
    database = DatabaseUpdater()
    wipe_db(database)
    database.makeDatabase()
    return database


def wipe_db(database: DatabaseUpdater):
    cursor = database.connection.execute("""
                                         SELECT name
                                         FROM sqlite_master
                                         WHERE type = 'table'
                                           AND name NOT LIKE 'sqlite_%';
                                         """)

    tables = [row[0] for row in cursor]
    tables.reverse()

    for table in tables:
        database.connection.execute(f'DROP TABLE IF EXISTS "{table}"')

    database.connection.commit()





def test_wipe_db():
    """
    test for wipe_db,
    the function facilitating clean tests
    :return:
    """
    database = make_fresh_db()
    wipe_db(database)

def test_add_to_database():
    """
    nominal case of putting something in the database and then retrieving the latest stock
    :return:
    """
    database = make_fresh_db()

    fictitious_stock = CompositeIVResult(symbol = "john_stocks", iv = .8,
                                         datetime = datetime.now())

    database.update_stock(fictitious_stock)

    test_iv = database.getLatestIVFromStock("john_stocks")
    assert test_iv == fictitious_stock.iv

    #print("value stored successfully and same value is retrieved")

def test_retrieve_bad_stock():
    """
    test when 1: stock doesn't exist
    2: stock is way too old to have an accurate IV value
    """

    print()

    database = make_fresh_db()

    #never existed
    test_iv = database.getLatestIVFromStock("john_stocks")
    assert test_iv is None
    #print("retrieving stock with no value yields null — passed")

    #too old
    fictitious_stock = CompositeIVResult(symbol = "john_stocks", iv = .8,
                                         datetime = datetime.now()-timedelta(weeks = 1))
    database.update_stock(fictitious_stock)
    test_iv = database.getLatestIVFromStock("john_stocks")
    assert test_iv is None
    #print("retrieving stock that's too old — passed")

    #good enough
    fictitious_stock = CompositeIVResult(symbol = "john_stocks", iv = .2,
                                         datetime = datetime.now()-timedelta(days = 5))
    database.update_stock(fictitious_stock)
    test_iv = database.getLatestIVFromStock("john_stocks")
    assert test_iv == .2
    #print("good value is retrieved — passed")

def test_retrieve_latest_stock():
    """
    when a newer value is added, retrieve it
    """

    print()

    database = make_fresh_db()

    #old iv
    fictitious_stock = CompositeIVResult(symbol = "john_stocks", iv = .2,
                                         datetime = datetime.now()-timedelta(days = 3))
    database.update_stock(fictitious_stock)
    test_iv = database.getLatestIVFromStock("john_stocks")
    assert test_iv == .2

    #new iv
    fictitious_stock = CompositeIVResult(symbol = "john_stocks", iv = .9,
                                         datetime = datetime.now()-timedelta(days = 1))
    database.update_stock(fictitious_stock)
    test_iv = database.getLatestIVFromStock("john_stocks")
    assert test_iv == .9

    #new iv
    fictitious_stock = CompositeIVResult(symbol = "john_stocks", iv = .4,
                                         datetime = datetime.now()-timedelta(minutes = 5))
    database.update_stock(fictitious_stock)
    test_iv = database.getLatestIVFromStock("john_stocks")
    assert test_iv == .4

if __name__ == '__main__':
    unittest.main()
