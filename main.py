# This is a sample Python script.
from time import sleep
from datetime import datetime, timedelta

from controller.scheduler import start_daemon
# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from controller.stock_iv_monitor import StockMonitor

import controller.scheduler


if __name__ == '__main__':
    start_daemon()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
