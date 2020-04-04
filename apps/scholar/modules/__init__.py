"""
import pandas as pd
import matplotlib.pyplot as plt

from modules.strategy import AdaptivePQ

df = pd.read_csv("../data/btc_ltc.csv", sep=";", index_col=0, parse_dates=[1], infer_datetime_format=True)

strategy = AdaptivePQ(df)

strategy.plot(figsize=(20, 10))

plt.show()
"""