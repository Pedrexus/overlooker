import abc

from pandas import DataFrame

from modules.profit.measure import Accountant


class Strategy(metaclass=abc.ABCMeta):

    def __init__(self, chart: DataFrame):
        self.chart = chart

    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)

    def __repr__(self):
        return repr(self.chart)

    def plot(self, figsize=(10, 10), *args, **kwargs):
        df = self.get_chart_with_indicators(*args, **kwargs)

        def colorize(row):
            if row.state_start < 0:
                return "r"
            elif row.state_start > 0:
                return "g"
            else:
                return "w"

        df_orders = df[df.change].append(df.tail(1))
        df_orders = df_orders\
            .join(df_orders.shift(-1), lsuffix="_start", rsuffix="_end")\
            .drop(df_orders.index[-1])

        df_orders["color"] = df_orders.apply(colorize, axis=1)

        axes = df.set_index("date")['close'].plot(figsize=figsize)
        for row in df_orders.itertuples():
            axes.axvspan(row.date_start, row.date_end, 0, 1, facecolor=row.color, alpha=0.5)

        return axes

    @staticmethod
    def get_profit(chart_with_trend: DataFrame, *args, **kwargs):
        profit_data = chart_with_trend \
            .join(chart_with_trend.shift(1), rsuffix="_previous") \
            .apply(Accountant().describe_profit, axis=1, *args, **kwargs) \
            .tolist()
        return DataFrame(profit_data)

    @abc.abstractmethod
    def strategy(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def evaluate(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def describe(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def get_chart_with_indicators(self, *args, **kwargs) -> DataFrame:
        raise NotImplementedError
