from abc import ABC

from pandas import DataFrame

from modules.constants.states import LONG_POSITION, SHORT_POSITION
from modules.profit.measure import Measure

# TODO: join - current, previous, last_order data

class Profit(Measure, ABC):
    # TODO: numero de operacoes, positivas, negativas, risco, exposicao, etc

    def __call__(self, strategy):
        df = strategy.chart.join(self.ledger.result)

        for func in (self.acc_profit, self.buy_and_hold, self.sell_and_hold):
            df[func.__name__] = df.apply(func, axis=1, initial=df.iloc[0])

        return ProfitChart(df)

    @staticmethod
    def acc_profit(row, initial):
        initial_position = initial.position

        if row.state == SHORT_POSITION:
            return (row.position - row.lending_debt * row.close) / initial_position
        elif row.state == LONG_POSITION:
            return (row.position * row.close) / initial_position
        else:
            return row.position / initial_position

    @staticmethod
    def buy_and_hold(row, initial):
        initial_close = initial.close
        return row.close / initial_close

    def sell_and_hold(self, row, initial):
        initial_close = initial.close

        idx = row.name
        interest = (1 + self.lending_rate) ** (idx * self.time)
        return (initial_close / row.close) / interest


class ProfitChart:

    def __init__(self, chart: DataFrame):
        self.chart = chart

    def __repr__(self):
        return repr(self.chart)

    @property
    def total(self):
        return float(self.chart["acc profit"].tail(1))

    @property
    def buy_total(self):
        df = self.chart[self.chart.state == LONG_POSITION]
        return NotImplemented

    @property
    def sell_total(self):
        df = self.chart[self.chart.state == SHORT_POSITION]
        raise NotImplemented
