"""
Core engine of the stock monitor
keeps track of all stock variables across multiple cron instances
"""
from pathlib import Path
from API.compositeIVFinder import load_symbols, SchwabIV, CompositeIVResult
from API.telegramMessager import send_telegram
from Engine.SlidingValue import SlidingValue, MaxSlidingValue, MinSlidingValue

BASE_THRESHOLD_IV = .9


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
        self.symbols_list = load_symbols(Path("blob/optionSymbols.txt"))
        self.min_iv : dict[str, SlidingValue] = {} #SlidingValue.get_value() returns a float
        self.max_iv : dict[str, SlidingValue] = {}
        self.iv_finder = SchwabIV()
        # database connector here
        #
        print(self.symbols_list)
    def check_IV_range(self, symbol):
        """
        if IV exceeds a certain range during the day, alert
        """
        if self.min_iv[symbol].val and self.max_iv[symbol].val and self.max_iv[symbol].get_iv - self.min_iv[symbol].get_iv > 20:
            send_telegram(str(symbol) + "abnormal change in IV")


    @staticmethod
    def check_IV_threshold(iv_result : CompositeIVResult):
        """
        if IV exceeds a certain base threshold during the day, alert
        TODO: make it adjustable for each individual stock
        """
        if iv_result.iv > BASE_THRESHOLD_IV:
            #print("------------")
            send_telegram(str(iv_result.symbol) + " exceeds base threshold of " + str(BASE_THRESHOLD_IV) + " at " + str(round(iv_result.iv, 2)))

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

                #check base threshold
                self.check_IV_threshold(composite_iv_result)

                if not self.max_iv.get(symbol):
                    self.max_iv[symbol] = MaxSlidingValue()
                if not self.min_iv.get(symbol):
                    self.min_iv[symbol] = MinSlidingValue()

                #check IV range
                self.check_IV_range(symbol)


                iv = composite_iv_result.iv
                self.max_iv[symbol].update_value(iv)
                self.min_iv[symbol].update_value(iv)



            except IVNotInterpolatedError as e:
                print(e.message)
            #except Exception as e:
             #   print("something happened for " + symbol + '\n' + str(e))
