from collections import defaultdict

from pandas import DataFrame


class Profit:
	# TODO: numero de operacoes, positivas, negativas, risco, exposicao, etc

	def __init__(self, chart: DataFrame):
		self.chart = chart.copy()

	def __call__(self, *args, **kwargs):
		return self.profit(*args, **kwargs)

	def __repr__(self):
		return repr(self.chart)

	def profit(self, *args, **kwargs):
		if self.chart["change"].any():
			df = self.chart
			df_join = df.join(df.shift(1), rsuffix="_previous")

			pm = ProfitMeasure(*args, **kwargs)

			for i, (prev_row, row) in enumerate(zip(df_join.itertuples(), df_join.iloc[1:, :].itertuples())):
				time = (row.date - prev_row.date).seconds / (60 * 60 * 24 * 30)

				if row.change:
					if row.trend > 0:  # buy order
						if prev_row.state < 0:  # close short and open long
							pm.close_short_and_open_long_position(row.close, time)
						else:  # open long
							pm.open_long_position(row.close)
					elif row.trend < 0:  # sell order
						if prev_row.state > 0:  # close long and open short
							pm.close_long_and_open_short_position(row.close)
						else:  # open short
							pm.open_short_position(row.close)
					else:
						pm.default_position()
				else:
					if row.state > 0:  # hold long
						pm.hold_long_position(row.close)
					elif row.state < 0:  # hold short
						pm.hold_short_position(row.close, time)
					else:
						pm.default_position()

			self.chart = self.chart.join(DataFrame(pm.result, index=self.chart.index))
			self.chart["acc profit"] = self.chart.apply(self.acc_profit, axis=1, initial_position=self.chart["position"][0])
			self.chart["buy_n_hold"] = self.chart.apply(self.buy_and_hold, axis=1, initial_close=self.chart["close"][0])
		else:
			self.chart["position"] = 1
			self.chart["profit"] = 1
			self.chart["acc profit"] = 1
			self.chart["comission"] = 0
			self.chart["lending debt"] = 0

		return self

	@property
	def total(self):
		return float(self.chart["acc profit"].tail(1))

	@property
	def buy_total(self):
		df = self.chart[self.chart.trend > 0]
		return df.apply(self.acc_profit, axis=1, initial_position=df["position"][0])

	@property
	def sell_total(self):
		df = self.chart[self.chart.trend > 0]
		return df.apply(self.acc_profit, axis=1, initial_position=df["position"][0])

	@staticmethod
	def acc_profit(row, initial_position=1):
		if row.state < 0:
			return (row.position - row.lending_debt * row.close) / initial_position
		elif row.state > 0:
			return (row.position * row.close) / initial_position
		else:
			return row.position / initial_position

	@staticmethod
	def buy_and_hold(row, initial_close):
		return row.close / initial_close

	@staticmethod
	def sell_and_hold(row, initial_close):
		return NotImplementedError


class ProfitMeasure:

	def __init__(self, cash=1, stop_loss=0.85, buy_rate=9e-4, sell_rate=9e-4, leverage=1, lending_rate=2e-2):
		self.cash = cash
		self.stop_loss = stop_loss
		self.buy_rate = buy_rate
		self.sell_rate = sell_rate
		self.leverage = leverage
		self.lending_rate = lending_rate

		self.orders = dict(position=[1], commission=[0], lending_debt=[0], profit=[1], close=[1])
		self.last_order = None

	def record_order(self, position, commission, lending_debt, profit, close, order=False):
		self.orders["position"].append(position)
		self.orders["commission"].append(commission)
		self.orders["lending_debt"].append(lending_debt)
		self.orders["profit"].append(profit)
		self.orders["close"].append(close)

		if order:
			self.last_order = len(self.orders["profit"]) - 1

	@property
	def result(self):
		orders = {**self.orders}
		orders.pop("close")
		return orders

	@property
	def current_lending_debt(self):
		return self.orders["lending_debt"][-1]

	@property
	def current_position(self):
		return self.orders["position"][-1]

	@property
	def last_order_position(self):
		return self.orders["position"][self.last_order - 1]

	@property
	def last_order_lending_debt(self):
		return self.orders["lending_debt"][self.last_order - 1]

	@property
	def last_order_close(self):
		return self.orders["close"][self.last_order - 1]

	def get_lending_debt(self, time):
		return self.current_lending_debt * (1 + self.lending_rate) ** time  # unit = other

	def get_buy_commission(self):
		return self.current_position * self.buy_rate  # unit = mine

	def get_long_position(self, close, lending_debt):
		return self.current_position / close - self.get_buy_commission() - lending_debt  # unit = other

	def get_long_profit(self, position, close, lending_debt):
		return (position * close) / (self.current_position - lending_debt * close)

	def close_short_and_open_long_position(self, close, time):
		lending_debt = self.get_lending_debt(time)  # extra_debt = lending_debt - self.current_lending_debt
		commission = self.get_buy_commission()
		position = self.get_long_position(close, lending_debt)
		profit = self.get_long_profit(position, close, lending_debt)

		lending_debt = 0

		self.record_order(position, commission, lending_debt, profit, close, order=True)

	def open_long_position(self, close):
		lending_debt = 0
		commission = self.get_buy_commission()
		position = self.get_long_position(close, lending_debt)
		profit = self.get_long_profit(position, close, lending_debt)

		self.record_order(position, commission, lending_debt, profit, close, order=True)

	def get_sell_commission(self, close):
		return self.current_position * self.sell_rate * close  # unit = mine

	def get_short_position(self, close, lending_debt):
		return self.current_position * close - self.get_sell_commission(close) - lending_debt  # unit = mine

	def get_short_profit(self, position, close, lending_debt):
		return (position - lending_debt * close) / (self.current_position * close)

	def close_long_and_open_short_position(self, close):
		# close long
		commission = self.get_sell_commission(close)
		lending_debt = 0
		position = self.get_short_position(close, lending_debt)

		# open short
		lending_debt = position * self.leverage / close  # unit = other
		commission += position * self.leverage * self.sell_rate  # unit = mine
		position = position * (1 + self.leverage) - commission  # unit = mine
		profit = self.get_short_profit(position, close, lending_debt)

		self.record_order(position, commission, lending_debt, profit, close, order=True)

	def open_short_position(self, close):
		lending_debt = self.current_position * self.leverage / close  # unit = other
		commission = self.current_position * self.leverage * self.sell_rate  # unit = mine
		position = self.current_position * (1 + self.leverage) - commission  # unit = mine

		profit = (position - lending_debt * close) / self.current_position

		self.record_order(position, commission, lending_debt, profit, close, order=True)

	def hold_short_position(self, close, time):
		commission = 0
		lending_debt = self.current_lending_debt * (1 + self.lending_rate) ** time
		position = self.current_position
		profit = (position - lending_debt * close) / self.last_order_position

		self.record_order(position, commission, lending_debt, profit, close, order=False)

	def hold_long_position(self, close):
		commission = 0
		lending_debt = 0
		position = self.current_position
		profit = position * close / (self.last_order_position - self.last_order_lending_debt * self.last_order_close)

		self.record_order(position, commission, lending_debt, profit, close, order=False)

	def default_position(self):
		self.record_order(self.current_position, 0, 0, 1, 0, order=False)
