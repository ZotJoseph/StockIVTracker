import unittest
from datetime import timedelta, datetime
from typing import Any, Generator

import common
from controller.stock_iv_monitor import StockMonitor
from controller.composite_iv_finder import CompositeIVResult
from tests.test_database import wipe_db
from unittest.mock import MagicMock
import controller.stock_iv_monitor


common.database.DATABASE_NAME = "test_stocks.db"
controller.stock_iv_monitor.OPTION_SYMBOLS_PATH = "tests/testSymbols.txt"


def patch_fetch_composite_iv(mocker, iv_list: list[float]):
    """
    patches controller, mock a few returns
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
    mocker.patch("controller.composite_iv_finder.SchwabIV.fetch_composite_iv", side_effect = iv_results)


def patch_send_to_telegram(mocker) -> unittest.mock.MagicMock:
    """
    patches send_telegram
    does nothing
    test uses mock.call_count to ascertain success
    """

    #need to patch stock_monitor's reference of the function
    #stock_monitor has its own reference because it imported via "from ... import" instead of "import"
    return mocker.patch("controller.stock_iv_monitor.send_telegram")



def test_iv_updates(mocker):
    """
    simulate when program updates IV, closes, and restarts, it should pull said latest IV
    :return:
    """
    # SchwabIV, the class used to access APi and find IV, is being mocked
    patch_fetch_composite_iv(mocker, [.1, .5])
    patch_send_to_telegram(mocker)

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


def test_iv_range(mocker):
    """
    alerts when iv exceeds range, otherwise doesn't
    """


    # SchwabIV, the class used to access APi and find IV, is being mocked
    patch_fetch_composite_iv(mocker, [.1, .14, .16])

    # wipe database
    monitor = StockMonitor()
    wipe_db(monitor.database)

    #telegram order: don't send the first two, send the last one
    mock_telegram = patch_send_to_telegram(mocker)

    monitor = StockMonitor()
    monitor.monitor()
    assert mock_telegram.call_count == 0
    monitor.monitor()
    assert mock_telegram.call_count == 0
    monitor.monitor()
    assert mock_telegram.call_count == 1

def test_iv_threshold(mocker):
    """
    alerts when iv exceeds threshold, otherwise doesn't
    """


    # SchwabIV, the class used to access controller and find IV, is being mocked
    patch_fetch_composite_iv(mocker, [.8999, .9])

    # wipe database
    monitor = StockMonitor()
    wipe_db(monitor.database)

    #telegram order: don't send the first two, send the last one
    mock_telegram = patch_send_to_telegram(mocker)

    monitor = StockMonitor()
    monitor.monitor()
    assert mock_telegram.call_count == 0
    monitor.monitor()
    assert mock_telegram.call_count == 1


if __name__ == '__main__':
    unittest.main()
