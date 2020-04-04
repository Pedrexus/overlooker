import pandas as pd


def peak_under_window(column: pd.Series, window):
	# FIXME: reamke with peakutils
	col = column.values
	values = list(col[:window])
	for i, value in enumerate(col[window:]):
		interval = col[i:i + window]
		peak = interval.min() if interval.argmin() > interval.argmax() else interval.max()
		values.append(peak)

	return pd.Series(values, column.index)


class Analysis:

	def __init__(self, chartdf: pd.DataFrame):
		self.chart = chartdf.set_index("date")

	def trend(self, n, w, p, q=None):
		prices = self.chart["close"]
		normalized_prices = (prices - prices.min()) / (prices.max() - prices.min())  # min max scaling

		ema = normalized_prices.ewm(span=n, adjust=False).mean()
		diff = ema - ema.shift(w).fillna(0)  #

		trend_analysis = diff.apply(self.strategy, p=p)
		trend_change = trend_analysis - trend_analysis.shift(1).fillna(0)

		df = self.chart.copy()
		df["normalized close"] = normalized_prices
		df["ema"] = ema
		df["trend"] = trend_analysis
		df["trend change"] = trend_change != 0
		df.loc[df.index[0], "trend change"] = False

		return df

	@staticmethod
	def profit(chart_with_trend: pd.DataFrame, leverage=1, lending_rate=1.001, rate=9e-4, stop_loss=.85):
		df = chart_with_trend[["close", "trend"]][chart_with_trend["trend change"] == True].copy()
		df_join = df.join(df.shift(1), rsuffix="_previous")

		def measure_profit(row, cash=1):
			last_t, last_p, p = row["trend_previous"], row["close_previous"], row["close"]

			if last_t < 0:
				_profit = cash * (1 + leverage * (last_p - p / last_p) * lending_rate * (1 - rate) ** 2)
			elif last_t > 0:
				_profit = (cash / last_p) * p * (1 - rate) ** 2
			else:
				_profit = cash

			_profit = stop_loss * cash if _profit < stop_loss * cash else _profit
			return _profit

		df["profit"] = df_join.apply(measure_profit, axis=1).shift(-1)

		return df

	@staticmethod
	def strategy(value, p):
		if value > 0 and value > p:
			return 1
		elif value < 0 and abs(value) > p:
			return -1
		else:
			return 0


if __name__ == '__main__':
	df = pd.read_csv("../data/btc_ltc.csv", sep=";", index_col=0, parse_dates=[1], infer_datetime_format=True)
	a = Analysis(df)

	df2 = a.trend(n=100, w=10, p=0.01)
	df3 = a.profit(df2)

	total_profit = df3.profit.prod()
