# This is a sample Python script.
from time import sleep
from datetime import datetime, timedelta

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from controller.stock_iv_monitor import StockMonitor


MINUTES_PER_MONITOR = 15


monitor = StockMonitor()

def start_monitoring():

    next_update = datetime.now()
    #TODO: dynamically control when to monitor: only when market is open, and reset everyday
    while True:
        now = datetime.now()
        if now >= next_update:
            print("process ran at " + str(now))
            next_update = now + timedelta(minutes = MINUTES_PER_MONITOR)
            monitor.monitor()
        sleep(55)

if __name__ == '__main__':
    start_monitoring()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
