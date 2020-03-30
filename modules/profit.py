from pandas import DataFrame


class Profit:

	def __init__(self, chart: DataFrame):
		self.chart = chart

	def __call__(self, *args, **kwargs):
		return self.profit(*args, **kwargs)

	def __repr__(self):
		return repr(self.chart)

	def profit(self, *args, **kwargs):
		if self.chart["trend change"].any():
			df = self.chart
			df_join = df.join(df.shift(1), rsuffix="_previous")

			profit_measure = ProfitMeasure(*args, **kwargs)

			profit = df_join.apply(profit_measure.measure_order_profit, axis=1).shift(-1)
			comission = df_join.apply(profit_measure.measure_order_comission, axis=1).shift(-1)
			lending_debt = df_join.apply(profit_measure.measure_order_lending_debt, axis=1).shift(-1)

			self.chart["profit"] = profit
			self.chart["comission"] = comission
			self.chart["lending debt"] = lending_debt
		else:
			self.chart["profit"] = 1
			self.chart["comission"] = 0
			self.chart["lending debt"] = 0

		return self

	@property
	def total(self):
		return self.chart.profit.prod()

	@property
	def buy_total(self):
		return self.chart[self.chart.trend > 0].profit.prod()

	@property
	def sell_total(self):
		return self.chart[self.chart.trend < 0].profit.prod()


class ProfitMeasure:

	def __init__(self, cash=1, stop_loss=0.85, buy_rate=9e-4, sell_rate=9e-4, leverage=1, lending_rate=2e-2):
		self.cash = cash
		self.stop_loss = stop_loss
		self.buy_rate = buy_rate
		self.sell_rate = sell_rate
		self.leverage = leverage
		self.lending_rate = lending_rate

	def measure_order_profit(self, row):
		last_t, last_p, p = row["trend_previous"], row["close_previous"], row["close"]

		if last_t < 0:
			time = (row["date"] - row["date_previous"]).seconds / (60 * 60 * 24 * 30)  # unit = months
			_profit = self.measure_short_position_profit(last_p, p, time, self.cash)
		elif last_t > 0:
			_profit = self.measure_long_position_profit(last_p, p, self.cash)
		else:
			_profit = self.cash

		_profit = self.stop_loss * self.cash if _profit < self.stop_loss * self.cash else _profit
		return _profit

	def measure_short_position_profit(self, initial_price, final_price, lending_time, cash=1):

		# open position #
		loan = self.leverage * cash / initial_price  # unit = other currency
		leveraged_cash = loan * initial_price  # unit = my currency

		sell_comission = leveraged_cash * self.sell_rate  # + 1 sell order
		initial_cash = leveraged_cash - sell_comission

		# close position #
		debt = loan * (1 + self.lending_rate) ** lending_time  # unit = other currency
		debt_cash = debt * final_price  # unit = my currency

		buy_comission = debt * self.buy_rate  # + 1 buy order
		final_cash = initial_cash - debt_cash - buy_comission

		return 1 + final_cash / cash

	def measure_long_position_profit(self, initial_price, final_price, cash=1):

		# open position #
		initial_cash = cash / initial_price * (1 - self.buy_rate)  # unit = other currency

		# close position #
		final_cash = initial_cash * final_price * (1 - self.sell_rate)  # unit = my currency

		return final_cash / cash

	def measure_order_comission(self, row):
		last_t, last_p, p = row["trend_previous"], row["close_previous"], row["close"]

		if last_t < 0:
			time = (row["date"] - row["date_previous"]).seconds / (60 * 60 * 24 * 30)  # unit = months
			_profit = self.measure_short_position_profit(last_p, p, time, self.cash)
		elif last_t > 0:
			_profit = self.measure_long_position_profit(last_p, p, self.cash)
		else:
			_profit = self.cash

		_profit = self.stop_loss * self.cash if _profit < self.stop_loss * self.cash else _profit
		return _profit