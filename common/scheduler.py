import logging

import exchange_calendars as xcals
from datetime import datetime, time
from apscheduler.schedulers.blocking import BlockingScheduler
from zoneinfo import ZoneInfo
from controller.stock_iv_monitor import StockMonitor

logger = logging.getLogger(__name__)

eastern = ZoneInfo("America/New_York")
scheduler = BlockingScheduler()


# runs once every day: check if market opens today and if opens does its thing
def start_daemon():
    scheduler.add_job(
        checkDay,
        trigger = "cron",
        hour = 9,
        timezone = ZoneInfo("America/New_York"),
        id = "check_day"
    )
    scheduler.start()


def checkDay():
    nyse = xcals.get_calendar("NYSE")
    if nyse.is_session(datetime.now(eastern).date()):
        logging.info("market day detected")
        runMarketDay()
    return

# runs once every 15 minutes: poll
def runMarketDay():
    monitor = StockMonitor()
    scheduler.add_job(
        monitor.monitor,
        trigger="interval",
        minutes=15,
        start_date=datetime.combine(datetime.now(eastern).date(), time(9,30), tzinfo = eastern),
        end_date=datetime.combine(datetime.now(eastern).date(), time(16,0), tzinfo = eastern),
        id = "market_poll"
    )
