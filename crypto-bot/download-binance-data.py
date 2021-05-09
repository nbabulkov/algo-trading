import argparse
import json
import os
from datetime import datetime

import pandas as pd
from binance.client import Client

DEFAULT_CONFIG = os.path.join(os.path.dirname(__file__), "config.json")
INTERVALS = [
    Client.KLINE_INTERVAL_1MINUTE,
    Client.KLINE_INTERVAL_5MINUTE,
    Client.KLINE_INTERVAL_30MINUTE,
    Client.KLINE_INTERVAL_1HOUR,
]


def read_config(path):
    with open(path) as f:
        config = json.load(f)
        return config


def parse_args():
    parser = argparse.ArgumentParser(description="Download data from Binance API")
    parser.add_argument(
        "--config", "-c", default=DEFAULT_CONFIG, help="Path to JSON config file"
    )
    parser.add_argument(
        "--ticker", "-t", required=True, help="Crypto Symbol e.g. ETHUSDT, ADABTC..."
    )
    parser.add_argument(
        "--start-date", "-s", required=True, help="Start date e.g. 1 Jan 2000"
    )
    parser.add_argument(
        "--end-date", "-s", default=datetime.today(), help="End date e.g. 21 Dec 2021"
    )
    parser.add_argument(
        "--interval", "-i", default=Client.KLINE_INTERVAL_1MINUTE, choices=INTERVALS
    )
    return parser.parse_args()


def symbol_exists(ticker, bclient):
    ticker_prices = bclient.get_all_tickers()
    tickers = [t["symbol"] for t in ticker_prices]
    return ticker in tickers


def main(args):
    config = read_config(args.config)
    bclient = Client(api_key=config["api_key"], api_secret=config["api_secret"])

    if not symbol_exists(args.ticker, bclient):
        raise ValueError("No such symbol on Binance: {args.ticker}")

    start_date = datetime.strptime(args.start_date, "%d %b %Y")
    end_date = args.end_date
    if isinstance(args.end_date, str):
        end_date = datetime.strptime(args.end_date, "%d %b %Y")

    print("working...")
    klines = bclient.get_historical_klines(
        args.ticker,
        args.interval,
        start_date.strftime("%d %b %Y %H:%M:%S"),
        end_date.strftime("%d %b %Y %H:%M:%S"),
        1000,
    )
    data = pd.DataFrame(
        klines,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_av",
            "trades",
            "tb_base_av",
            "tb_quote_av",
            "ignore",
        ],
    )
    data["timestamp"] = pd.to_datetime(data["timestamp"], unit="ms")

    data.set_index("timestamp", inplace=True)
    output_file = f"{args.ticker}_{args.interval}_{args.start_date}.csv"
    data.to_csv(output_file)
    print("finished!")


if __name__ == "__main__":
    args = parse_args()
    main(args)
