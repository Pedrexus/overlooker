import pandas as pd

from apps.agent.modules.exchange.Poloniex.PoloniexStopLimit import StopPoloniex
from apps.agent.modules.processing.processing import Processing

order_table = Processing().get_order_table()
tickers = pd.DataFrame(StopPoloniex().returnTicker()).T

df = order_table.join(tickers, on="market")
df["visualized"] = False  # append in redis


def make_stop(row):
    if row.visualized is not True and row.order is not 'HOLD POSITION':
        if row.order is 'OPEN LONG POSITION' and row.state is 'NO POSITION':
            # open long position
            amount = row.amount
            stop = float(row.lowestAsk) + row.stop_markup
            limit = float(row.lowestAsk) + row.limit_markup
            # callback -> set new state as LONG POSITION
        elif row.order is 'OPEN SHORT POSITION' and row.state is 'NO POSITION':
            # open short position
            amount = -row.amount
            stop = float(row.highestBid) - row.stop_markup
            limit = float(row.highestBid) - row.limit_markup
            # callback -> set new state as SHORT POSITION
        elif row.order is 'END POSITION' and row.state is 'LONG POSITION':
            amount = -row.amount
            stop = float(row.highestBid) - row.stop_markup
            limit = float(row.highestBid) - row.limit_markup
            # callback -> set new state as NO POSITION
        elif row.order is 'END POSITION' and row.state is 'SHORT POSITION':
            amount = row.amount
            stop = float(row.lowestAsk) + row.stop_markup
            limit = float(row.lowestAsk) + row.limit_markup
            # callback -> set new state as NO POSITION
        elif row.order is 'OPEN LONG POSITION' and row.state is 'SHORT POSITION':
            # 1. close short, 2. open long -> set as end position, but when checked
            # create a new stop order
            # callback -> set new state as NO POSITION and order as OPEN LONG POSITION
            pass
        elif row.order is 'OPEN SHORT POSITION' and row.state is 'LONG POSITION':
            # 1. close long, 2. open short
            # callback -> set new state as NO POSITION and order as OPEN SHORT POSITION
            pass

        stop_limit = {
            'market': row.market,
            'amount': amount,
            'stop': stop,
            'limit': limit,
            'callback': callback,  # for when the order is executed
            'test': False,
            'order': None,
            'executed': False,
        }