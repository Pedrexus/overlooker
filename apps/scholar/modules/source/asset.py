from copy import deepcopy

import modules.utils as utils
import pandas as pd
import numpy as np
from poloniex import Poloniex


class Asset:
	"""ASSET object:
		responsible for getting public chart data of a specific ticker and
		making a few possible analysis from it.

		ABLE to:
			1. retrieve ticker chart data from poloniex.
	"""

	def __init__(self, coin_ticker, candlestick_period="1 hour", start='1 Month', end='Now'):
		self.coin_ticker = coin_ticker
		self.candlestick_period = utils.period_from_string(candlestick_period)
		self.chart_start = utils.timestamp_from_string(start)
		self.chart_end = utils.timestamp_from_string(end)

		self.ticker_chart_data = pd.DataFrame(
			Poloniex().returnChartData(
				currencyPair=self.coin_ticker,
				period=self.candlestick_period,
				start=self.chart_start,
				end=self.chart_end
			)
		).astype("float64").astype({"date": "int64"})

	def __repr__(self):
		return repr(self.ticker_chart_data)

	def __call__(self, *args, **kwargs):
		return pd.Series(Poloniex().returnTicker()[self.coin_ticker], name=self.coin_ticker)

	def date_as_datetime(self):
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
		return self.ticker_chart_data


if __name__ == '__main__':
	btc_ltc = Asset("BTC_LTC", candlestick_period="30 min", start='1 Month', end='Now').date_as_datetime()

	from modules.strategy import AdaptivePQ
	strategy = AdaptivePQ(btc_ltc.as_dataframe())

	profit = strategy(rsi_n=10, ema_n=119, lower_limit=40, upper_limit=60).profit(stop_loss=0.85, leverage=1)

