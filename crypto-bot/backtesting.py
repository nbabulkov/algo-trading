import argparse
from datetime import datetime
from colorama import Fore, Style, init
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind

# Create a Stratey
class TestStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        """Logging function for this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        iso = dt.isoformat()
        print(f"{iso}, {txt}")

    def __init__(self):
        sma1 = btind.SimpleMovingAverage(self.data)
        ema1 = btind.ExponentialMovingAverage()

        close_over_sma = self.data.close > sma1
        close_over_ema = self.data.close > ema1
        sma_ema_diff = sma1 - ema1

        self.buy_sig = bt.And(close_over_sma, close_over_ema, sma_ema_diff > 0)
        self.sell_sig = abs(self.data.close - sma1) / self.data.close > 0.1

    def notify_order(self, order):
        #print(self.position)
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Rejected]:
            self.log('Order Canceled/Rejected')
        elif order.status is order.Margin:
            self.log('Order Margin call')

        # Write down: no pending order
        self.order = None

    def next(self):
        # BUY, BUY, BUY!!! (with all possible default parameters)
        if self.position.size > 0 and self.sell_sig:
            self.sell()
        elif self.buy_sig and self.broker.getcash() > self.data.close:
            self.buy()


def parse_args():
    parser = argparse.ArgumentParser(description="Backtest a strategy")
    parser.add_argument(
        "--data", "-d", required=True, help="CSV with data for backtesting"
    )
    parser.add_argument("--starting-cash", "-s", default=100.0, type=float)
    return parser.parse_args()


def main(args):
    data = btfeeds.GenericCSVData(
        dataname=args.data,
        nullvalue=0.0,
        dtformat=("%Y-%m-%d %H:%M:%S"),
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=-1,
    )
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(TestStrategy)

    # Set our desired cash start
    cerebro.broker.setcash(args.starting_cash)
    cerebro.broker.setcommission(commission=0.075)


    # Print out the starting conditions
    start_cash = cerebro.broker.getvalue()

    # Run over everything
    cerebro.run()

    print("-------------------------------------\n")
    print(f"Starting Portfolio Value: {start_cash}")
    # Print out the final result
    end_cash = cerebro.broker.getvalue()
    print(f"Final Portfolio Value: {end_cash}")
    profit = (end_cash - start_cash) / start_cash * 100
    color = Fore.GREEN if profit > 0 else Fore.RED
    print(f"Profit: {end_cash - start_cash} | {color}{profit:+.2f}%")
   # cerebro.plot()

if __name__ == "__main__":
    args = parse_args()
    init(autoreset=True)
    main(args)
