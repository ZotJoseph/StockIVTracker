import unittest
from datetime import timedelta, datetime
from typing import Any, Generator

import common
from controller.stock_iv_monitor import StockMonitor, StockConfig
from controller.composite_iv_finder import CompositeIVResult, SchwabIV
from tests.test_database import wipe_db
from unittest.mock import MagicMock
import controller.stock_iv_monitor


common.database.DATABASE_NAME = "test_stocks.db"
controller.stock_iv_monitor.OPTION_SYMBOLS_PATH = "tests/test_symbols.txt"
controller.stock_iv_monitor.UNIVERSAL_RANGE_THRESHOLD = .03
controller.stock_iv_monitor.UNIVERSAL_BASE_THRESHOLD_RANGE = .005


def mock_schwab_init(mocker):
    """
    prevent credential-related failures during test
    """
    mocker.patch("controller.composite_iv_finder.SchwabIV.__init__", return_value = None)

def mock_fetch_composite_iv(mocker, iv_list: list[float]):
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
                                        minutes = minutes_before_present), iv = iv,
                                    status = "interpolated")

    iv_results = composite_iv_result_generator()
    mocker.patch("controller.composite_iv_finder.SchwabIV.fetch_composite_iv",
                 side_effect = iv_results)


def mock_send_to_telegram(mocker) -> unittest.mock.MagicMock:
    """
    patches send_telegram
    does nothing
    test uses mock.call_count to ascertain success
    """

    # need to patch stock_monitor's reference of the function
    # stock_monitor has its own reference because it imported via "from ... import" instead of "import"
    return mocker.patch("controller.stock_iv_monitor.send_telegram")


def test_iv_updates(mocker):
    """
    simulate when program updates IV, closes, and restarts, it should update some value according a stock's data
    :return:
    """
    # SchwabIV, the class used to access APi and find IV, is being mocked
    mock_schwab_init(mocker)
    mock_fetch_composite_iv(mocker, [.1, .5])
    mock_send_to_telegram(mocker)

    # wipe database
    monitor = StockMonitor()
    wipe_db(monitor.database)

    # first start
    monitor = StockMonitor()
    assert monitor.stocks["GOOGL"].base_iv is None
    monitor.monitor()

    # restart monitor
    monitor = StockMonitor()
    assert monitor.stocks["GOOGL"].base_iv == .1
    monitor.monitor()

    # restart monitor
    monitor = StockMonitor()
    assert monitor.stocks["GOOGL"].base_iv == .5


def test_iv_range(mocker):
    """
    alerts when iv exceeds range, otherwise doesn't
    """

    # SchwabIV, the class used to access APi and find IV, is being mocked
    mock_schwab_init(mocker)
    mock_fetch_composite_iv(mocker, [.52, .53, .50])
    Schwab_api = SchwabIV()
    mock_send_to_telegram(mocker)

    #  setting StockConfig.threshold to None has the side effect of asserting unused variables should not affect range checking procedures
    stock = StockConfig("GOOGL", .5, None, None)
    assert (StockMonitor.check_and_update_iv_range(stock,
                                                   Schwab_api.fetch_composite_iv("GOOGL"))) == False

    assert (StockMonitor.check_and_update_iv_range(stock,
                                                   Schwab_api.fetch_composite_iv("GOOGL"))) == True

    assert (StockMonitor.check_and_update_iv_range(stock,
                                                   Schwab_api.fetch_composite_iv("GOOGL"))) == True

    # range triggers at .03


def test_iv_threshold(mocker):
    """
    alerts when iv exceeds threshold, otherwise doesn't
    """

    # SchwabIV, the class used to access controller and find IV, is being mocked
    mock_schwab_init(mocker)
    mock_fetch_composite_iv(mocker, [.5, .501, .506, .499, .49])
    Schwab_api = SchwabIV()
    mock_send_to_telegram(mocker)

    stock = StockConfig("GOOGL", None, None, None)
    assert (StockMonitor.check_and_update_iv_threshold(stock,
                                                   Schwab_api.fetch_composite_iv("GOOGL"))) == False  #None and .5

    assert (StockMonitor.check_and_update_iv_threshold(stock,
                                                   Schwab_api.fetch_composite_iv("GOOGL"))) == False  #.5 and .501

    assert (StockMonitor.check_and_update_iv_threshold(stock,
                                                   Schwab_api.fetch_composite_iv("GOOGL"))) == True  #.5 and .506
    assert stock.threshold_alert_direction == "down"


    assert (StockMonitor.check_and_update_iv_threshold(stock,
                                                   Schwab_api.fetch_composite_iv("GOOGL"))) == False  #.5 and .499

    assert (StockMonitor.check_and_update_iv_threshold(stock,
                                                   Schwab_api.fetch_composite_iv("GOOGL"))) == True  #.5 and .49
    assert stock.threshold_alert_direction == "up"
