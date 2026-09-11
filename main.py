# This is a sample Python script.
from asyncio import sleep
from datetime import datetime, timedelta
from API import compositeIVFinder
from API.compositeIVFinder import load_symbols


# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from Engine.stock_monitor import StockMonitor


monitor = StockMonitor()

def start_monitoring():

    next_update = datetime.now()

    while True:
        now = datetime.now()
        if now >= next_update:
            print("process ran at " + str(now))
            next_update = now + timedelta(minutes = 15)
            monitor.monitor()
        sleep(60)

if __name__ == '__main__':
    start_monitoring()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
