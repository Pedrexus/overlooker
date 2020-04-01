import abc
from functools import lru_cache

from pandas import DataFrame
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

from modules.Strategy.context import Context
from modules.constants.orders import CLOSE_SHORT_POSITION, OPEN_LONG_POSITION, CLOSE_LONG_POSITION, \
    OPEN_SHORT_POSITION, \
    HOLD_POSITION
from modules.constants.states import SHORT_POSITION, NO_POSITION, LONG_POSITION, State
from modules.profit.profit import Profit


class Strategy(metaclass=abc.ABCMeta):

    def __init__(self, chart: DataFrame):
        self.chart = chart
        self.context = Context()

    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)

    def __repr__(self):
        return repr(self.chart)

    def plot(self, *args, **kwargs):
        df = self.chart.copy()

        def colorize(row):
            if row.trend < 0:
                return "r"
            elif row.trend > 0:
                return "g"
            else:
                return "w"

        df["color"] = df.apply(colorize, axis=1)

        axes = df['close'].plot(*args, **kwargs)
        for i, j in zip(df.index, df.index[1:]):
            axes.axvspan(i, j, 0, 1, facecolor=df.color[i], alpha=0.5)

        return axes

    @abc.abstractmethod
    def strategy(self, *args, **kwargs):
        """

        @param args:
        @param kwargs:
        @return:
        """
        raise NotImplementedError

    @abc.abstractmethod
    def evaluate(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        raise NotImplementedError


class AdaptivePQ(Strategy):

    @lru_cache(maxsize=512)
    def get_indicators(self, rsi_n=14, ema_n=12):
        indicator_rsi = RSIIndicator(close=self.chart.close, n=int(rsi_n), fillna=False).rsi()
        indicator_rsi_ema = EMAIndicator(close=indicator_rsi, n=int(ema_n)).ema_indicator()

        indicator_rsi[:int(ema_n) - 1] = 0

        return DataFrame({"rsi": indicator_rsi, "ema": indicator_rsi_ema}, index=self.chart.index)

    def get_current_indicators(self, rsi_n=14, ema_n=12):
        return self.get_indicators(rsi_n, ema_n).iloc[self.context.i, :].values

    def evaluate(self, rsi_n=14, ema_n=12, lower_limit=40, upper_limit=60, *args, **kwargs):
        profit = Profit(*args, **kwargs)
        self.context.reset()

        for row in self.chart.itertuples():
            open, close = row.open, row.close
            rsi, rsi_ema = self.get_current_indicators(rsi_n, ema_n)

            orders = self.strategy(
                self.context.state, open, close, rsi, rsi_ema, lower_limit, upper_limit)
            evaluated_orders = profit.record(orders, self.context, close)

        # api.execute_order(evaluated_orders)

        return profit(self)

    @staticmethod
    def strategy(state: State, open, close, rsi, rsi_ema, lower_limit=40, upper_limit=40) -> tuple:
        # price is advancing
        if close > open and rsi > rsi_ema and (rsi_ema < lower_limit or rsi_ema > upper_limit):
            if state is SHORT_POSITION:
                return CLOSE_SHORT_POSITION, OPEN_LONG_POSITION
            elif state is NO_POSITION:
                return OPEN_LONG_POSITION,
        # price is decreasing
        elif close < open and rsi < rsi_ema and (rsi_ema < lower_limit or rsi_ema > upper_limit):
            if state is LONG_POSITION:
                return CLOSE_LONG_POSITION, OPEN_SHORT_POSITION
            elif state is NO_POSITION:
                return OPEN_SHORT_POSITION,
        return HOLD_POSITION,

    def execute(self, rsi_n=14, ema_n=12, lower_limit=40, upper_limit=60):
        raise DeprecationWarning

        df = self.chart.copy()

        indicator_rsi = RSIIndicator(close=df.close, n=int(rsi_n), fillna=False).rsi()
        indicator_rsi_ema = EMAIndicator(close=indicator_rsi, n=int(ema_n)).ema_indicator()

        indicator_rsi[:int(ema_n) - 1] = 0

        df["rsi"], df["rsi_ema"] = indicator_rsi, indicator_rsi_ema.fillna(0)

        trend = df.apply(self._strategy, axis=1, lower_limit=lower_limit, upper_limit=upper_limit)
        df["trend"] = trend

        ffill_trend = trend.fillna(method='ffill').fillna(0)
        df["state"] = ffill_trend

        trend_change = ffill_trend - ffill_trend.shift(1).fillna(0)
        df["change"] = trend_change != 0

        self.chart = df
        return Profit(df)

    @staticmethod
    def _strategy(row, lower_limit=40, upper_limit=60):
        # TODO: profit calculado na operaçao
        open, close = row.open, row.close  # close == preço atual
        rsi, rsi_ema = row.rsi, row.rsi_ema

        if close - open > 0:
            if rsi > rsi_ema and (rsi_ema < lower_limit or rsi_ema > upper_limit):
                # open long | close short
                return 1
        elif close - open < 0:
            if rsi < rsi_ema and (rsi_ema < lower_limit or rsi_ema > upper_limit):
                # open short | close long
                return -1
        else:
            return