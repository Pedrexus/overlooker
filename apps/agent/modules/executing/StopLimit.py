# this class should work as a commom stop limit and also as a
# stop loss observer, executing END POSITIOn when the profit gets too down
from django.utils.timezone import now
from easydict import EasyDict

from apps.agent.modules.exchange.Poloniex import PoloniexTicker
from apps.agent.modules.processing.investment import Investment
from constants import *


class StopLimit:
    BUY = 'BUY'
    SELL = 'SELL'

    EXPIRY_TIME = 3600  # seconds

    def __init__(self, investment: Investment, ticker: PoloniexTicker):
        self.investment = investment
        self.ticker = ticker

        self.__creation_time = now()
        self.executed = False

        self.last_order = None  # TODO: used to measure profit and exec stop loss
        self.state_order = self.investment.state, self.investment.order

    def __getattr__(self, item):
        try:
            return getattr(self.investment, item)
        except AttributeError:
            try:
                return getattr(self.ticker, item)
            except AttributeError:
                raise AttributeError(f"{item} is not a valid attribute of {self}")

    def sell(self):
        pass

    def buy(self):
        pass

    @property
    def is_expired(self):
        return (self.__creation_time - now()).total_seconds() > self.EXPIRY_TIME

    @property
    def has_executed(self):
        return self.state_order[1] is HOLD_POSITION

    ACTIONS = {
        START_LONG_POSITION: BUY,
        END_SHORT_POSITION: BUY,
        FROM_SHORT_TO_LONG_POSITION: BUY,
        START_SHORT_POSITION: SELL,
        END_LONG_POSITION: SELL,
        FROM_LONG_TO_SHORT_POSITION: SELL,
    }

    @property
    def action(self):
        return self.ACTIONS[self.state_order]

    @property
    def amount(self):
        return - self.investment.amount if self.action is self.SELL else self.investment.amount

    @property
    def stop(self):
        if self.action is self.SELL:
            return self.ticker.highestBid - self.investment.stop_markup
        else:
            return self.ticker.lowestAsk + self.investment.stop_markup

    @property
    def limit(self):
        if self.action is self.SELL:
            return self.ticker.highestBid - self.investment.limit_markup
        else:
            return self.ticker.lowestAsk + self.investment.limit_markup

    NEW_STATE_ORDER = {
        START_LONG_POSITION: HOLD_LONG_POSITION,
        END_LONG_POSITION: HOLD_NO_POSITION,
        START_SHORT_POSITION: HOLD_SHORT_POSITION,
        END_SHORT_POSITION: HOLD_NO_POSITION,
        FROM_SHORT_TO_LONG_POSITION: START_LONG_POSITION,
        FROM_LONG_TO_SHORT_POSITION: START_SHORT_POSITION,
    }

    def callback(self):
        # function called when the stop-limit is executed
        # return new_state, new_order
        self.state_order = self.NEW_STATE_ORDER[self.state_order]

    def check_stop(self, lowAsk, highBid):
        # TODO: get full ticker

        # sell
        if self.amount < 0 and self.stop >= float(highBid):
            # sell amount at limit
            self.last_order = self.sell(self.investment.market, self.limit, abs(self.amount))

            self.logger.info(
                f'{self.investment.market} sell stop order triggered at {self.stop}'
            )

            self.callback()
            return self.state_order
        # buy
        elif self.amount > 0 and self.stop <= float(lowAsk):
            # buy amount at limit
            self.last_order = self.buy(self.investment.market, self.limit, self.amount)

            self.logger.info(
                f'{self.investment.market} buy stop order triggered at {self.stop}'
            )

            self.callback()
            return self.state_order
        else:
            return False
