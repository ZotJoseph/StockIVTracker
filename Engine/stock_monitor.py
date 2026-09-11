"""
Core engine of the stock monitor
keeps track of all stock variables across multiple cron instances
"""
from pathlib import Path
from API.compositeIVFinder import load_symbols, SchwabIV
from API.telegramMessager import send_telegram
from Engine.SlidingValue import SlidingValue, MaxSlidingValue, MinSlidingValue


class IVNotInterpolatedError(Exception):
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
        self.symbols_list = load_symbols(Path("../blob/optionSymbols.txt"))
        self.min_iv : dict[str, SlidingValue] = {} #SlidingValue.get_value() returns a float
        self.max_iv : dict[str, SlidingValue] = {}
        self.iv_finder = SchwabIV()
        # database connector here
        #

    def check_IV_range(self, symbol):
        if self.min_iv[symbol] and self.max_iv[symbol] and self.max_iv[symbol].get_val - self.min_iv[symbol].get_val > 10:
            send_telegram(str(symbol) + "abnormal change in IV")

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
                if composite_iv_result.status is not "interpolated":
                    raise IVNotInterpolatedError(str(symbol) + " could not be interpolated")
                iv = composite_iv_result.iv



                if not self.max_iv.get(symbol):
                    self.max_iv[symbol] = MaxSlidingValue(60)
                if not self.min_iv.get(symbol):
                    self.min_iv[symbol] = MinSlidingValue(40)

                self.check_IV_range(symbol)

                self.max_iv[symbol].update_value(iv)
                self.min_iv[symbol].update_value(iv)



            except IVNotInterpolatedError as e:
                print(e.message)
            except Exception:
                print("something happened for " + symbol)
