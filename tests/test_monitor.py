import unittest
from datetime import timedelta, datetime
from typing import Any, Generator

import Engine
from Engine.stock_monitor import StockMonitor
from API.compositeIVFinder import SchwabIV, CompositeIVResult
from tests.test_database import wipe_db, make_fresh_db

import Engine.stock_monitor


Engine.databaseUpdater.DATABASE_NAME = "test_stocks.db"
Engine.stock_monitor.OPTION_SYMBOLS_PATH = "tests/testSymbols.txt"


def patch_fetch_composite_iv(mocker, iv_list: list[float]):
    """
    patches API, mock a few returns
    PLEASE REMEMBER TO UPDATE TO composite_iv_result = "interpolated" ELSE THE MONITOR WILL THROW EXCEPTION

    *iv is the list of iv that will be returned in CompositeIVResult, the top of the list will be outputted first

    NOT DESIGNED TO GO BEYOND LIMIT of len(iv_list)
    """

    def composite_iv_result_generator() -> Generator[CompositeIVResult, Any, None]:
        minutes_before_present = 75
        for iv in iv_list:
            yield CompositeIVResult(symbol = "GOOGL",
                                    datetime = datetime.now() - timedelta(
                                        minutes = minutes_before_present), iv = iv, status = "interpolated")


    iv_results = composite_iv_result_generator()
    mocker.patch("API.compositeIVFinder.SchwabIV.fetch_composite_iv", side_effect = iv_results)


def test_iv_updates(mocker):
    """
    simulate when program updates IV, closes, and restarts, it should pull said latest IV
    :return:
    """
    # SchwabIV, the class used to access APi and find IV, is being mocked
    patch_fetch_composite_iv(mocker, [.1, .5])

    # wipe database
    monitor = StockMonitor()
    wipe_db(monitor.database)

    # first start
    monitor = StockMonitor()
    assert monitor.min_iv["GOOGL"] is None and monitor.max_iv["GOOGL"] is None
    monitor.monitor()

    # restart monitor
    monitor = StockMonitor()
    assert monitor.min_iv["GOOGL"] == .1 and monitor.max_iv["GOOGL"] == .1
    monitor.monitor()

    # restart monitor
    monitor = StockMonitor()
    assert monitor.min_iv["GOOGL"] == .5 and monitor.max_iv["GOOGL"] == .5


if __name__ == '__main__':
    unittest.main()
