from collections import OrderedDict
from functools import lru_cache

import poloniex
from django.utils.functional import cached_property
from easydict import EasyDict
from numpy import int32, float64
from pandas import Series

from apps.agent.modules.exchange.Poloniex.PoloniexTicker import PoloniexTicker
from apps.agent.modules.executing.StopLimit import StopLimit
from apps.agent.modules.processing.processing import Processing
from constants import HOLD_POSITION


class StopPoloniex(poloniex.PoloniexSocketed):

    def __init__(self, *args, **kwargs):
        super(StopPoloniex, self).__init__(*args, **kwargs)
        # holds stop orders
        self.stopOrders = []
        self.db_conn = Processing()

    def on_ticker(self, msg):
        ticker = PoloniexTicker(msg)
        # check stop orders
        mkt, la, hb = str(self._getChannelName(str(tick.id))), ticker.lowestAsk, ticker.highestBid

        for i, stop_order in enumerate(self.stopOrders):
            if stop_order.is_expired:
                del self.stopOrders[i]  # could be a weak ref list

            # market matches and the order hasnt triggered yet
            if stop_order.market == mkt and not stop_order.has_executed:
                self.logger.debug('%s lowAsk=%s highBid=%s', mkt, str(la), str(hb))
                new_state_order = stop_order.check_stop(la, hb)
                if new_state_order:
                    new_state, new_order = new_state_order
                    self.db_conn.update_state_order(stop_order.hash, new_state, new_order)

        order_table = self.db_conn.get_order_table()
        for row in order_table.itertuples():
            if row.visualized is not True and row.order is not HOLD_POSITION:
                if row.market == mkt:
                    sl = StopLimit(row, ticker)
                    self.stopOrders.append(sl)
                    self.db_conn.set_visualized(row.hash)
                    # self.logger.debug('%s stop limit set: [Amount]%.8f [Stop]%.8f [Limit]%.8f', row.market, row.amount, stop, limit)



if __name__ == '__main__':
    import logging

    logging.basicConfig()

    test = StopPoloniex('key', 'secret')
    test.logger.setLevel(logging.DEBUG)


    def callbk(id):
        print(test.stopOrders[id])


    tick = test.returnTicker()

    # remove or set 'test' to false to place real orders

    # buy order
    test.addStopLimit(market='BTC_LTC',
                      amount=0.5,
                      stop=float(tick['BTC_LTC']['lowestAsk']) + 0.000001,
                      limit=float(0.004),
                      callback=callbk,
                      test=True)

    # sell order
    test.addStopLimit(market='BTC_LTC',
                      amount=-0.5,
                      stop=float(tick['BTC_LTC']['highestBid']) - 0.000001,
                      limit=float(0.004),
                      callback=callbk,
                      # remove or set 'test' to false to place real orders
                      test=True)

    test.startws({'ticker': test.on_ticker})

    # while True:
    poloniex.sleep(120)

    test.stopws(3)
