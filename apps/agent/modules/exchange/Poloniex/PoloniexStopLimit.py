from collections import OrderedDict
from functools import lru_cache

import poloniex
from django.utils.functional import cached_property
from easydict import EasyDict
from numpy import int32, float64
from pandas import Series

from apps.agent.modules.processing.processing import Processing


class StopPoloniex(poloniex.PoloniexSocketed):

    def __init__(self, *args, **kwargs):
        super(StopPoloniex, self).__init__(*args, **kwargs)
        # holds stop orders
        self.stopOrders = {}
        self.db_conn = Processing()

    def on_ticker(self, msg):
        tick = PoloniexTicker(msg)

        # check stop orders
        mkt, la, hb = str(self._getChannelName(str(tick.id))), tick.lowestAsk, tick.highestBid
        for id, stop_order in self.stopOrders.items():
            if stop_order.is_expired:
                del self.stopOrders[id]

            # market matches and the order hasnt triggered yet
            if str(self.stopOrders[id]['market']) == mkt and not self.stopOrders[id]['executed']:
                self.logger.debug('%s lowAsk=%s highBid=%s', mkt, str(la), str(hb))
                self._check_stop(id, la, hb)

        order_table = self.db_conn.get_order_table()
        tickers = self.returnTicker()

        for row in order_table.itertuples():
            if row.visualized is not True and row.order is not 'HOLD POSITION':
                if row.order is 'OPEN LONG POSITION' and row.state is 'NO POSITION':
                    self.addStopLimit(
                        market=row.market,
                        amount=row.amount,
                        stop=float(tickers[row.market]['lowestAsk']) + row.stop_markup,
                        limit=float(tickers[row.market]['lowestAsk']) + row.limit_markup,
                        callback=lambda x: 'update db: put order as HOLD and changes state',
                        test=False,
                        # api = api(secret_key, public_Key)
                    )
                elif row.order is 'OPEN SHORT POSITION' and row.state is 'NO POSITION':
                    self.addStopLimit(
                        market=row.market,
                        amount=-row.amount,
                        stop=float(tickers[row.market]['highestBid']) - row.stop_markup,
                        limit=float(tickers[row.market]['highestBid']) - row.limit_markup,
                        callback=lambda x: 'update db: put order as HOLD and changes state',
                        test=False,
                        # api = api(secret_key, public_Key)
                    )
                elif row.order is 'OPEN LONG POSITION' and row.state is 'SHORT POSITION':
                    self.addStopLimit(
                        market=row.market,
                        amount=row.amount,
                        stop=float(tickers[row.market]['lowestAsk']) + row.stop_markup,
                        limit=float(tickers[row.market]['lowestAsk']) + row.limit_markup,
                        callback=lambda x: 'update db: put order as OPEN LONG and changes state',
                        test=False,
                        # api = api(secret_key, public_Key)
                    )
                elif row.order is 'OPEN SHORT POSITION' and row.state is 'LONG POSITION':
                    self.addStopLimit(
                        market=row.market,
                        amount=row.amount,
                        stop=float(tickers[row.market]['highestBid']) - row.stop_markup,
                        limit=float(tickers[row.market]['highestBid']) - row.limit_markup,
                        callback=lambda x: 'update db: put order as OPEN SHORT and changes state',
                        test=False,
                        # api = api(secret_key, public_Key)
                    )

    def _check_stop(self, id, lowAsk, highBid):
        amount = self.stopOrders[id]['amount']
        stop = self.stopOrders[id]['stop']
        test = self.stopOrders[id]['test']
        # sell
        if amount < 0 and stop >= float(highBid):
            # dont place order if we are testing
            self.stopOrders[id]['executed'] = True
            if test:
                self.stopOrders[id]['order'] = None
            else:
                # sell amount at limit
                self.stopOrders[id]['order'] = self.sell(
                    self.stopOrders[id]['market'],
                    self.stopOrders[id]['limit'],
                    abs(amount))

            self.logger.info('%s sell stop order triggered! (%s)',
                             self.stopOrders[id]['market'],
                             str(stop))
            if self.stopOrders[id]['callback']:
                self.stopOrders[id]['callback'](id)

        # buy
        if amount > 0 and stop <= float(lowAsk):
            # dont place order if we are testing
            self.stopOrders[id]['executed'] = True
            if test:
                self.stopOrders[id]['order'] = None
            else:
                # buy amount at limit
                self.stopOrders[id]['order'] = self.buy(
                    self.stopOrders[id]['market'],
                    self.stopOrders[id]['limit'],
                    amount)

            self.logger.info('%s buy stop order triggered! (%s)',
                             self.stopOrders[id]['market'],
                             str(stop))
            if self.stopOrders[id]['callback']:
                self.stopOrders[id]['callback'](id)

    def addStopLimit(self, market, amount, stop, limit, callback=None, test=False):
        self.stopOrders[market + str(stop)] = {
            'market': market,
            'amount': amount,
            'stop': stop,
            'limit': limit,
            'callback': callback,
            'test': test,
            'order': None,
            'executed': False,
        }
        self.logger.debug('%s stop limit set: [Amount]%.8f [Stop]%.8f [Limit]%.8f',
                          market, amount, stop, limit)


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
