from pandas import DataFrame
# from functools import cached_property
from pip._vendor.distlib.util import cached_property


class EvaluationLedger:
    LENDING_PERIOD = 86400  # 1 day in seconds

    # LENDING_PERIOD = 86400 * 30 - 1 month in seconds

    def __init__(self, chart: DataFrame, stop_loss=0.85, acc_stop_loss=.725, rate=9e-4, leverage=1,
                 lending_rate=2e-2):
        self.chart = chart
        self.stop_loss = stop_loss
        self.acc_stop_loss = acc_stop_loss
        self.rate = rate
        self.leverage = leverage
        self.lending_rate = lending_rate

    def __repr__(self):
        return repr(self.chart)

    def __getattr__(self, item):
        try:
            return getattr(self.chart, item)
        except AttributeError:
            raise AttributeError(f"{self.__class__} object has no attribute {item}")

    @property
    def initial(self):
        return self.chart.iloc[0]

    @property
    def final(self):
        return self.chart.iloc[-1]

    @property
    def total_profit(self):
        return self.final.acc_profit

    @property
    def buy_and_hold_profit(self):
        return ((1 - self.rate) ** 2) * (self.final.close / self.initial.close)

    @property
    def sell_and_hold_profit(self):
        time = (self.final.date - self.initial.date).seconds / self.LENDING_PERIOD
        interest = (1 + self.lending_rate) ** time
        return ((1 - self.rate) ** 2) * (self.initial.close / self.final.close) / float(interest)


class DescriptionLedger(EvaluationLedger):

    def __init__(self, *args, **kwargs):
        super(DescriptionLedger, self).__init__(*args, **kwargs)

        self.chart["normalized_close"] = self.min_max_rescale(self.chart["close"])
        self.chart["buy_and_hold"] = self.chart.apply(self.buy_and_hold, axis=1)
        self.chart["sell_and_hold"] = self.chart.apply(self.sell_and_hold, axis=1)

    def plot(self, cols=("profit", "acc_profit"), *args, **kwargs):
        df = self.chart.set_index("date")

        axes = df[list(cols)].plot(*args, **kwargs)

        if "profit" in cols:
            axes.hlines(self.stop_loss, df.index[0], df.index[-1], color="r", label="stop loss")
        if "acc_profit" in cols:
            axes.hlines(self.acc_stop_loss, df.index[0], df.index[-1], color="y",
                        label="acc stop loss")
        if len({"profit", "acc_profit"}.intersection(cols)) != 0:
            axes.hlines(1., df.index[0], df.index[-1], color="g")

        axes.legend(loc="upper left")

        return axes

    @staticmethod
    def min_max_rescale(col):
        return (col - col.min()) / (col.max() - col.min())

    @property
    def buy_total(self):
        return NotImplemented

    @property
    def sell_total(self):
        return NotImplemented

    def buy_and_hold(self, row):
        return row.close / self.initial.close

    def sell_and_hold(self, row):
        time = (row.date - self.initial.date).seconds / self.LENDING_PERIOD
        interest = (1 + self.lending_rate) ** time

        return (self.initial.close / row.close) / float(interest)
