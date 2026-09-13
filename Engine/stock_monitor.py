"""
Core engine of the stock monitor
keeps track of all stock variables across multiple cron instances
"""
from pathlib import Path
from API.compositeIVFinder import load_symbols, SchwabIV, CompositeIVResult
from API.telegramMessager import send_telegram
from Engine.databaseUpdater import DatabaseUpdater


BASE_IV_THRESHOLD = .9
BASE_RANGE_THRESHOLD = 0.05
OPTIONS_SYMBOLS_PATH_DEBUG = "blob/testSymbols.txt"
OPTION_SYMBOLS_PATH = "blob/optionSymbols.txt"


class IVNotInterpolatedError(Exception):
    """
    custom error for when API or IVCalculator could not interpolate IV
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
        symbols_list = symbols of all stocks we wish to monitor
        min_iv = symbols : priority_queue, the top being the smallest IV of stock [key] in the last 24 hours
        max_iv symbols : priority_queue, the top being the largest IV stock [key] in the last 24 hours
        """
        self.symbols_list = load_symbols(Path(OPTION_SYMBOLS_PATH))
        self.min_iv : dict[str, float] = {} #SlidingValue.get_value() returns a float
        self.max_iv : dict[str, float] = {}

        self.iv_finder = SchwabIV()

        self.database = DatabaseUpdater()
        self.database.makeDatabase()

        for stock in self.symbols_list:
            self.initialize_iv_range(stock)


    def initialize_iv_range(self, stock_symbol : str):
        """
        given a stock symbol, grab the latest IV value from database, if it does not exist, set both to None
        TODO: if data for today's stock exist, retrieve the smallest and largest value 30 day composite IV and set them to min/max respectively
        """
        stock_iv = self.database.getLatestIVFromStock(stock_symbol)
        self.min_iv[stock_symbol], self.max_iv[stock_symbol] = stock_iv, stock_iv


    def update_IV_range(self, composite_iv_result : CompositeIVResult):
        """
        given compositeIVResult, update existing IV range
        """
        symbol = composite_iv_result.symbol
        if not self.min_iv.get(symbol) or self.min_iv[symbol] > composite_iv_result.iv:
            self.min_iv[symbol] = composite_iv_result.iv
        if not self.max_iv.get(symbol) or self.max_iv[symbol] < composite_iv_result.iv:
            self.max_iv[symbol] = composite_iv_result.iv

    def check_IV_range(self, symbol):
        """
        if IV's range exceeds a certain percent, alert
        """
        if self.min_iv.get(symbol) and self.max_iv.get(symbol) and self.max_iv[symbol] - self.min_iv[symbol] > BASE_RANGE_THRESHOLD:
            send_telegram(str(symbol) + " abnormal change in IV, IV range is at: " + str(self.max_iv[symbol] - self.min_iv[symbol] * 100) + "%")


    @staticmethod
    def check_IV_threshold(iv_result : CompositeIVResult):
        """
        if IV exceeds a certain base threshold during the day, alert
        TODO: make it adjustable for each individual stock
        """
        if iv_result.iv > BASE_IV_THRESHOLD:
            #print("------------")
            send_telegram(str(iv_result.symbol) + " exceeds base threshold of " + str(BASE_IV_THRESHOLD) + " at " + str(round(iv_result.iv, 2)))


    def monitor(self):
        """
        Check IV
        check if IV exceed throttle (alert)
        check if exceed min/max IV (alert)
        send alerts
        update min/max IV
        update IV in daily database
        """

        for symbol in self.symbols_list:
            try:
                composite_iv_result = self.iv_finder.fetch_composite_iv(symbol)
                print(str(composite_iv_result.symbol) + " " + str(composite_iv_result.iv))
                if composite_iv_result.status !="interpolated":
                    raise IVNotInterpolatedError(str(symbol) + " could not be interpolated")

                #update database
                self.database.update_stock(composite_iv_result)

                #check base threshold
                self.check_IV_threshold(composite_iv_result)

                #update and check IV range
                self.update_IV_range(composite_iv_result)
                self.check_IV_range(symbol)

                self.database.connection.commit()


            except IVNotInterpolatedError as e:
                print(e.message)
            #except Exception as e:
                #print("something happened for " + symbol + '\n' + str(e))
