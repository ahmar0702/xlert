
import requests
import pandas as pd
import time
from binance.client import Client

# === CONFIG ===
BINANCE_API_KEY = 'Vm1iKL5d40R2XYY9FNEMZawRxJRpHTtMmfthk8dXO1BopKWm14dE3ZixGsQzZlqX'
BINANCE_SECRET_KEY = 'b360ia3IcletiyGeM2sVDcf4NQotJpLy3ZTZuPfBYXgOyEMmCCocarPxAdEQE1xV'
TELEGRAM_BOT_TOKEN = '8009615316:AAFmAiAA9_bjZaH4225zUVZ__Gfifq3l1ok'
TELEGRAM_CHAT_ID = ' 1973506173'
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'DOGEUSDT']  # Add more if needed
INTERVAL = '3m'
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
CHECK_INTERVAL_SECONDS = 180  # Every 3 minutes

client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

def rsi_tradingview(ohlc: pd.DataFrame, period: int = 14, round_rsi: bool = True):
    delta = ohlc["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    if round_rsi:
        return rsi.round()
    return rsi

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram error:", e)

def get_ohlcv(symbol):
    klines = client.get_historical_klines(symbol, INTERVAL, "600 minutes ago UTC")
    df = pd.DataFrame(klines, columns=["time", "open", "high", "low", "close", "volume",
                                       "close_time", "quote_asset_volume", "num_trades",
                                       "taker_base_vol", "taker_quote_vol", "ignore"])
    df = df[["time", "close"]].copy()
    df.columns = ["Time", "Close"]
    df["Time"] = pd.to_datetime(df["Time"], unit="ms")
    df["Close"] = df["Close"].astype(float)
    return df

def run_multi_coin_bot():
    print("Multi-coin signal bot started...")
    last_signals = {}  # Save last sent signals per symbol

    while True:
        for symbol in SYMBOLS:
            try:
                df = get_ohlcv(symbol)
                df["RSI"] = rsi_tradingview(df, RSI_PERIOD)
                latest_rsi = df["RSI"].iloc[-1]

                last_signal = last_signals.get(symbol)

                if latest_rsi > RSI_OVERBOUGHT and last_signal != "SELL":
                    send_telegram_message(f"🔻 {symbol} RSI: {latest_rsi} — Consider SELL (Overbought)")
                    last_signals[symbol] = "SELL"
                elif latest_rsi < RSI_OVERSOLD and last_signal != "BUY":
                    send_telegram_message(f"🔺 {symbol} RSI: {latest_rsi} — Consider BUY (Oversold)")
                    last_signals[symbol] = "BUY"
                else:
                    print(f"{symbol} — No signal. RSI: {latest_rsi}")
            except Exception as e:
                print(f"Error checking {symbol}: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)

# To run:
# run_multi_coin_bot()
