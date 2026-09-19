StockIVTracker 0.1v

Tracks a stock's Composite 30 day IV (implied volatility) and puts them in a SQLite database

Will alert you when: 
  - a stock's Composite30DayIV exceeds a base threshold
  - a range of a stock's Composite30DayIV within a market day exceeds a base threshold


------------------------------
Installation: 
------------------------------
1) make a .env file in the project folder
2) insert the following in .env
  SCHWAB_APP_KEY="schwab_api_key_here"
  SCHWAB_APP_SECRET="secret_here"
  TELEGRAM_BOT_TOKEN="make_telegram_bot_and_put_token_here"
  TELEGRAM_CHAT_ID="get_bot_chat_id_here"

  ! visit https://api.telegram.org/bot{YOUR_BOT_TOKEN}/getUpdates to get chat ID

3) grab Schwab Bearer tokens via OAuth 2.0, put the tokens.json inside project directory

4) in optionSymbols.txt add the symbols of your preferred stock to monitor
5) run, it's preferred that you don't stop the program when the market is open (useless when its' closed since no one can make calls/puts)
