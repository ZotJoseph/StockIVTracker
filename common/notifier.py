import os


import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(string : str):
    print("\n ---------------------------------------------------------- \n" + string)
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": f"{string}"
        }
    )

    if not response.json()["ok"]:
        print(response.json()["description"])
