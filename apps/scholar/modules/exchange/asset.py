import abc
from copy import deepcopy

from celery import shared_task

import apps.scholar.modules.utils as utils
import pandas as pd


class Asset(metaclass=abc.ABCMeta):
    """ASSET object:
        responsible for getting public chart data of a specific ticker and
        making a few possible analysis from it.

        ABLE to:
            1. retrieve ticker chart data from poloniex.
    """

    registry = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Asset.registry[cls.__name__] = cls

    def __init__(self, currency_pair, candlestick_period, start, end='Now'):
        self.currency_pair = currency_pair
        self.candlestick_period = candlestick_period.total_seconds()
        self.chart_start = start.timestamp()
        self.chart_end = utils.timestamp_from_string(end)

        self.ticker_chart_data = None

    def __repr__(self):
        return repr(self.ticker_chart_data)

    def __call__(self):
        # updates ticker_chart_data
        self.ticker_chart_data = pd.DataFrame(
            self.return_chart_data()
        ).astype("float64").astype({"date": "int64"})

        return self

    def call(self, *args, **kwargs):
        return pd.Series(self.return_ticker(), name=self.currency_pair)

    @abc.abstractmethod
    def return_chart_data(self):
        raise NotImplementedError

    @abc.abstractmethod
    def return_ticker(self):
        raise NotImplementedError

    def validate_self(self):
        if self.ticker_chart_data is None:
            raise ValueError("Asset has to be called once")

    def date_as_datetime(self):
        self.validate_self()

        obj = deepcopy(self)

        df = obj.ticker_chart_data
        df.date = pd.to_datetime(df.date, unit="s")
        obj.ticker_chart_data = df

        return obj

    def date_as_index(self):
        obj = self.date_as_datetime()
        obj.ticker_chart_data.set_index("date", inplace=True)
        return obj

    def as_dataframe(self):
        self.validate_self()
        return self.ticker_chart_data


if __name__ == '__main__':
    btc_ltc = Asset("BTC_LTC", candlestick_period="30 min", start='1 Month',
                    end='Now').date_as_datetime()

    from modules.strategy import AdaptivePQ

    strategy = AdaptivePQ(btc_ltc.as_dataframe())

    profit = strategy(rsi_n=10, ema_n=119, lower_limit=40, upper_limit=60).profit(stop_loss=0.85,
                                                                                  leverage=1)
