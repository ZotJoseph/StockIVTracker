"""
Core common of the stock monitor
keeps track of all stock variables across multiple cron instances
"""
from dataclasses import dataclass
from pathlib import Path
from controller.composite_iv_finder import load_symbols, SchwabIV, CompositeIVResult
from common.notifier import send_telegram
from common.database import DatabaseConnection



@dataclass
class StockConfig:
    symbol : str
    base_iv : float #  compare new results with base_IV to see if range exceeded, replace when it does
    threshold : float # used to check when stock goes above or below the threshold
    threshold_alert_direction : str | None # "up" = when exceed threshold, alert, "down" = when go below threshold, None = not set yet (when first ran)


UNIVERSAL_RANGE_THRESHOLD = 0.03 # 3 percent point change usually indicate IV crush
UNIVERSAL_BASE_THRESHOLD_RANGE = 0.005 # base_threshold has a range where if change didn't exceed this number, the threshold will not trigger (otherwise it triggers too often)

OPTION_SYMBOLS_PATH = "optionSymbols.txt"
#OPTIONS_SYMBOLS_PATH_DEBUG = "blob/testSymbols.txt"

class IVNotInterpolatedError(Exception):
    """
    custom error for when controller or IVCalculator could not interpolate IV
    usually when stock symbol does not exist
    """
    def __init__(self, message, error_code = None):
        super().__init__(message)
        self.error_code = error_code
        self.message = message

    def __str__(self):
        return f"{self.message} (Code: {self.error_code})"


class StockMonitor:
    def __init__(self):
        """
        configurate stock and database
        """
        symbols_list = load_symbols(Path(OPTION_SYMBOLS_PATH))
        self.stocks : dict[str, StockConfig] = {}
        self.iv_finder = SchwabIV()


        self.database = DatabaseConnection()
        self.database.makeDatabase()

        for stock in symbols_list:
            self.configurate_stock(stock)


    def configurate_stock(self, stock_symbol : str):
        """
        given a stock symbol, add a StockConfig for monitoring purposes
        grabs the latest stock IV (if exist) for the symbol to set as base_iv and threshold
        """
        latest_stock_iv = self.database.getLatestIVFromStock(stock_symbol)
        self.stocks[stock_symbol] = (
            StockConfig(
                symbol = stock_symbol,
                base_iv = latest_stock_iv,
                threshold = latest_stock_iv,
                threshold_alert_direction = None
            )
        )

    @staticmethod
    def check_and_update_iv_range(stock : StockConfig, updated_stock : CompositeIVResult) -> bool:
        """
        returns whether last updated IV range exceeds the UNIVERSAL_RANGE_THRESHOLD
        has the side effect of alerting telegram and updating base_iv of stock if it exceeds;

        does not update anything
        """

        if not stock.base_iv:
            stock.base_iv = updated_stock.iv

        if abs(updated_stock.iv - stock.base_iv) >= UNIVERSAL_RANGE_THRESHOLD:
            send_telegram(str(stock.symbol) + " has abnormal change in composite 30 day IV from : "
                          + str(round(stock.base_iv, 5) * 100) + "% to " + str(round(updated_stock.iv, 5) * 100) + "%")
            stock.base_iv = updated_stock.iv
            return True

        return False

    @staticmethod
    def check_and_update_iv_threshold(stock : StockConfig, updated_stock : CompositeIVResult) -> bool:
        """
        returns whether last updated stock IV goes past the set throttle for said IV
        has side effect of alerting telegram and updating threshold direction if threshold is hit
        """


        # no stock IV
        if not stock.threshold:
            stock.threshold = updated_stock.iv

        stock_iv_delta = updated_stock.iv - stock.threshold   # show how much iv has changed (and in what direction)

        if (stock.threshold_alert_direction is None or stock.threshold_alert_direction == "up") and stock_iv_delta > UNIVERSAL_BASE_THRESHOLD_RANGE:  # stock IV went up
            send_telegram(str(stock.symbol) + " went above the threshold of "
                          + str(round(stock.threshold, 5) * 100) + "% at " + str(round(updated_stock.iv, 5) * 100) + "%")
            stock.threshold_alert_direction = "down"
            return True

        if (stock.threshold_alert_direction is None or stock.threshold_alert_direction == "down") and stock_iv_delta < -UNIVERSAL_BASE_THRESHOLD_RANGE:
            send_telegram(str(stock.symbol) + " went below the threshold of "
                          + str(round(stock.threshold, 5) * 100) + "% at " + str(round(updated_stock.iv, 5) * 100) + "%")
            stock.threshold_alert_direction = "up"
            return True

        return False



    def monitor(self):
        """
        Check IV
        check if IV exceed throttle (alert)
        check if exceed min/max IV (alert)
        send alerts
        update min/max IV
        update IV in daily database
        """

        for symbol, stock in self.stocks.items():
            try:
                composite_iv_result = self.iv_finder.fetch_composite_iv(stock.symbol)

                print(str(composite_iv_result.symbol) + " " + str(composite_iv_result.iv))
                print(str(stock))
                if composite_iv_result.iv is None:
                    raise IVNotInterpolatedError(str(stock.symbol) + " could not be interpolated")

                #update database
                self.database.update_stock(composite_iv_result)

                #check base threshold
                self.check_and_update_iv_threshold(stock, composite_iv_result)

                #update and check IV range
                self.check_and_update_iv_range(stock, composite_iv_result)


            except IVNotInterpolatedError as e:
                print(e.message)
            #except Exception as e:
                #print("something happened for " + symbol + '\n' + str(e))
