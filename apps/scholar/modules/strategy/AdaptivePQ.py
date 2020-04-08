from functools import lru_cache

from pandas import DataFrame
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

from .strategy import Strategy
from ..constants.states import SHORT_POSITION, NO_POSITION, LONG_POSITION
from ..profit.ledger import DescriptionLedger, EvaluationLedger
from ..profit.measure import Accountant


class AdaptivePQ(Strategy):

    @staticmethod
    def strategy(row, lower_limit=40, upper_limit=40) -> tuple:
        open, close, rsi, rsi_ema = row.open, row.close, row.rsi, row.rsi_ema

        # price is advancing
        if close > open and rsi > rsi_ema and (rsi_ema < lower_limit or rsi_ema > upper_limit):
            return LONG_POSITION
        # price is decreasing
        elif close < open and rsi < rsi_ema and (rsi_ema < lower_limit or rsi_ema > upper_limit):
            return SHORT_POSITION
        return NO_POSITION

    # TODO: turn into task
    def evaluate(self, rsi_n=14, ema_n=12, lower_limit=40, upper_limit=60, *args, **kwargs):
        df = self.get_chart_with_indicators(rsi_n, ema_n, lower_limit, upper_limit)

        df_orders = df[df.change | df.index.isin([0, df.index[-1]])]

        df_profit = DataFrame(
            df_orders
                .join(df_orders.shift(-1), lsuffix="_start", rsuffix="_end")
                .apply(Accountant.Evaluate().evaluate_profit, axis=1, *args, **kwargs)
                .tolist(),
            index=df_orders.index
        ).fillna(method="ffill")

        df_profit["date"], df_profit["close"] = df_orders["date"], df_orders["close"]
        # result = df_orders.join(df_profit, rsuffix="_profit")

        return EvaluationLedger(df_profit, *args, **kwargs)

    def describe(self, rsi_n=14, ema_n=12, lower_limit=40, upper_limit=60, *args, **kwargs):
        df = self.get_chart_with_indicators(rsi_n, ema_n, lower_limit, upper_limit)

        df_profit = DataFrame(
            df
                .join(df.shift(1), rsuffix="_previous")
                .apply(Accountant.Describe().describe_profit, axis=1, *args, **kwargs)
                .tolist()
        )

        df["state"] = df_profit["state"]
        result = df.join(df_profit.drop(["close", "state"], axis=1), rsuffix="_profit")

        return DescriptionLedger(result, *args, **kwargs)

    def execute(self, *args, **kwargs):
        pass

    @lru_cache(maxsize=512)
    def get_indicators(self, rsi_n=14, ema_n=12):
        indicator_rsi = RSIIndicator(close=self.chart.close, n=int(rsi_n), fillna=False).rsi()
        indicator_rsi_ema = EMAIndicator(close=indicator_rsi, n=int(ema_n)).ema_indicator()

        indicator_rsi[:int(ema_n) - 1] = 0

        return indicator_rsi, indicator_rsi_ema.fillna(0)

    def get_chart_with_indicators(self, rsi_n=14, ema_n=12, lower_limit=40, upper_limit=60):
        df = self.chart.copy()
        df["rsi"], df["rsi_ema"] = self.get_indicators(rsi_n, ema_n)

        trend = df.apply(self.strategy, axis=1, lower_limit=lower_limit, upper_limit=upper_limit)
        ffill_trend = trend.replace(NO_POSITION, None).fillna(method='ffill').fillna(NO_POSITION)
        trend_change = ffill_trend - ffill_trend.shift(1).fillna(0)

        df["trend"], df["state"], df["change"] = trend, ffill_trend, trend_change != NO_POSITION

        return df
