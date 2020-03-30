import abc
from pandas import DataFrame
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

from modules.profit import Profit


class Strategy(metaclass=abc.ABCMeta):

	def __init__(self, chart: DataFrame):
		self.chart = chart

	def __call__(self, *args, **kwargs):
		return self._execute(*args, **kwargs)

	def __repr__(self):
		return repr(self.chart)

	def plot(self, *args, **kwargs):
		df = self.chart.copy()

		def colorize(row):
			if row.trend < 0:
				return "r"
			elif row.trend > 0:
				return "g"
			else:
				return "w"

		df["color"] = df.apply(colorize, axis=1)

		axes = df['close'].plot(*args, **kwargs)
		for i, j in zip(df.index, df.index[1:]):
			axes.axvspan(i, j, 0, 1, facecolor=df.color[i], alpha=0.5)

		return axes

	@abc.abstractmethod
	def _execute(self, *args, **kwargs):
		return NotImplemented

	@abc.abstractmethod
	def _strategy(self, *args, **kwargs):
		return NotImplemented


class AdaptivePQ(Strategy):

	def _execute(self, rsi_n=14, ema_n=12, lower_limit=40, upper_limit=60):
		df = self.chart.copy()

		indicator_rsi = RSIIndicator(close=df.close, n=rsi_n, fillna=False).rsi()
		indicator_rsi_ema = EMAIndicator(close=indicator_rsi, n=ema_n).ema_indicator()

		indicator_rsi[:ema_n - 1] = 0

		df["rsi"], df["rsi_ema"] = indicator_rsi, indicator_rsi_ema.fillna(0)

		trend = df.apply(self._strategy, axis=1, lower_limit=lower_limit, upper_limit=upper_limit)
		df["trend"] = trend

		ffill_trend = trend.fillna(method='ffill').fillna(0)
		trend_change = ffill_trend - ffill_trend.shift(1).fillna(0)
		df["trend change"] = trend_change != 0

		self.chart = df
		return Profit(df)

	@staticmethod
	def _strategy(row, lower_limit=40, upper_limit=60):
		open, close = row.open, row.close  # close == preço atual
		rsi, rsi_ema = row.rsi, row.rsi_ema

		if close - open > 0:
			if rsi > rsi_ema and (rsi_ema < lower_limit or rsi_ema > upper_limit):
				# open long | close short
				return 1
		elif close - open < 0:
			if rsi < rsi_ema and (rsi_ema < lower_limit or rsi_ema > upper_limit):
				# open short | close long
				return -1
		else:
			return
