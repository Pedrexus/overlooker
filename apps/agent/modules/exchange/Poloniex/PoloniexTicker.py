from collections import OrderedDict
from functools import lru_cache

from numpy import int32, float64
from pandas import Series


class PoloniexTicker:
    ref = OrderedDict([
        ('id', int32),
        ('last', float64),
        ('lowestAsk', float64),
        ('highestBid', float64),
        ('percentChange', float64),
        ('baseVolume', float64),
        ('quoteVolume', float64),
        ('isFrozen', bool),
        ('high24hr', float64),
        ('low24hr', float64)
    ])

    def __init__(self, data: list):
        self.data = data

    @lru_cache(maxsize=16)
    def __getattr__(self, item: str):
        try:
            idx = list(self.ref.keys()).index(item)
        except ValueError:
            raise AttributeError(f"{item} is not in {self.__class__.__name__}")

        return self.ref[item](self.data[idx])

    @lru_cache(maxsize=2)
    def as_series(self):
        return Series({key: _type(val) for (key, _type), val in zip(self.ref.items(), self.data)})
