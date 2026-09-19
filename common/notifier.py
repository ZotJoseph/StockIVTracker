import logging
import os
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(string : str):
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": f"{string}"
        }
    )
    logging.info("sent alert: " + string)

    if not response.json()["ok"]:
        logging.critical("telegram messaging system has failed")
        print(response.json()["description"])
