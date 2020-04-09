import abc

from pandas import DataFrame

from ..strategy.analysis import Optimization
from ..constants.orders import END_POSITION, OPEN_SHORT_POSITION, OPEN_LONG_POSITION
from ..constants.states import SHORT_POSITION, NO_POSITION, LONG_POSITION


class Strategy(metaclass=abc.ABCMeta):

    execution_relation = {
            NO_POSITION: END_POSITION,
            SHORT_POSITION: OPEN_SHORT_POSITION,
            LONG_POSITION: OPEN_LONG_POSITION
        }

    registry = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Strategy.registry[cls.__name__] = cls

    def __init__(self, chart: DataFrame):
        self.chart = chart

    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)

    def __repr__(self):
        return repr(self.chart)

    def plot(self, figsize=(10, 10), *args, **kwargs):
        df = self.get_chart_with_indicators(*args, **kwargs)

        if not df.change.any():
            return df.set_index("date")['close'].plot(figsize=figsize)

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

    def optimize(self, *args, **kwargs) -> Optimization:
        return Optimization(self, *args, **kwargs)

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
