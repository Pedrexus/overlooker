from functools import lru_cache

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/btc_ltc.csv", sep=";", index_col=0,
                 parse_dates=[1], infer_datetime_format=True)

df2 = df.set_index("date")["close"]

# df2.plot()
# plt.show()

# jupyter notebook

class Prices:

    def __init__(self, prices):
        self.prices = prices

    @lru_cache(maxsize=4096)
    def ema(self, t: int = 0, n: float = 10):
        if t == 0:
            return self.prices[0]
        else:
            return self.prices[t] + self.ema(t - 1) * (1 - 2 / (n + 1))

    def as_ema(self, *args, **kwargs):
        return [self.ema(t, *args, **kwargs) for t, _ in enumerate(self.prices)]

if __name__ == "__main__":
    pr = Prices(df2.values)
    ema = pr.as_ema(n=7)
