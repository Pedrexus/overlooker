import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("../data/btc_ltc.csv", sep=";", index_col=0, parse_dates=[1], infer_datetime_format=True)

from modules.strategy import AdaptivePQ

strategy = AdaptivePQ(df)

profits = []
for i in range(1, 5):
    ema_profits = []
    for j in range(1, 5):
        _profit = strategy(rsi_n=i, ema_n=j, lower_limit=40, upper_limit=60).profit(stop_loss=0.85, leverage=1)
        ema_profits.append(_profit)

    arr = np.array([p.total for p in ema_profits])
    argmax = arr.argmax()  # = j
    profits.append([argmax, ema_profits[argmax]])

