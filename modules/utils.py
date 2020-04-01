import numpy as np
import pandas as pd
import datetime as dt
import time as T
from poloniex import Poloniex
import re


# import stockstats as st


######## DATE/TIME CONTROL ########

def timestamp_to_UTC(DataFrame):
	UTC_dates = []
	dates = np.array(DataFrame)
	for timestamp in dates:
		time = dt.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
		UTC_dates.append(time)
	return np.array([dt.datetime.strptime(date, '%Y-%m-%d %H:%M:%S') for date in UTC_dates])


def UTC_to_timestamp(DataFrame):
	timestamps = []
	dates = np.array(DataFrame)
	for UTC in dates:
		time = T.mktime(dt.datetime.strptime(UTC, '%Y-%m-%d %H:%M:%S').timetuple())
		timestamps.append(time)
	return np.array(timestamps)


def now():
	return int(dt.datetime.utcnow().timestamp())


def days_ago(days=1):
	return int((dt.datetime.utcnow() - dt.timedelta(days)).timestamp())


def timestamp_from_string(time):
	string = time.lower()
	string_groups = re.match("(\d+)? ?(\w+)", string).groups()

	if 'now' in string_groups:
		return now()
	else:
		amount = int(string_groups[0])
		unit = string_groups[1]

		units = {'hours': 1 / 24, 'days': 1, 'weeks': 7, 'months': 31, 'years': 365}

		for u in units.keys():
			if unit in u:
				time_in_days = amount * units[u]
				break

		return days_ago(time_in_days)


def period_from_string(time):
	string = time.lower()
	string_groups = re.match("(\d+)? ?(\w+)", string).groups()

	amount = int(string_groups[0])
	unit = string_groups[1]

	units = {'seconds': 1, 'minutes': 60, 'hours': 60 * 60, 'days': 24 * 60 * 60}

	for u in units.keys():
		if unit in u:
			time_in_seconds = amount * units[u]
			break

	return time_in_seconds


########## DATAFRAME-WISE FUNCTIONS ########

def max_df(df_1, df_2):
	return (df_1 + df_2 + abs(df_1 - df_2)) / 2


def min_df(df_1, df_2):
	return (df_1 + df_2 - abs(df_1 - df_2)) / 2


############# PLOTING PLUGINS #######################

def volume_colors(close, INCREASING_COLOR='#20C73C', DECREASING_COLOR='#CC0000'):
	colors = []
	for i in range(len(close)):
		if i != 0:
			if close[i] > close[i - 1]:
				colors.append(INCREASING_COLOR)
			else:
				colors.append(DECREASING_COLOR)
		else:
			colors.append(DECREASING_COLOR)
	return colors


########## POLONIEX PUBLIC API ##############

def get_poloniex_tickers(coin='BTC'):
	returnTicker = Poloniex().returnTicker()
	tickers = np.array(list(returnTicker.keys()))
	coin_ = re.compile(coin)
	coin_tickers = np.array(list(filter(coin_.search, tickers)))

	return coin_tickers


def get_poloniex_close_tickers(tickers, period=86400, start_ohlc=days_ago(days=365), end_ohlc=now()):
	main_df = pd.DataFrame()

	for count, ticker in enumerate(tickers):
		df = pd.DataFrame(
			Poloniex().returnChartData(currencyPair=ticker, period=period, start=start_ohlc, end=end_ohlc)).astype(
			float)
		df.index = timestamp_to_UTC(df['date'])

		df.rename(columns={'close': ticker}, inplace=True)
		df = pd.DataFrame(df[ticker])

		if main_df.empty:
			main_df = df
		else:
			main_df = main_df.join(df, how='outer')

		main_df.fillna(value=0.0, inplace=True)

	return main_df.copy()


def get_indicator(ticker, indicator, candlestick_period=86400, chart_start=days_ago(days=365), chart_end=now()):
	ticker_chart_data = pd.DataFrame(
		Poloniex().returnChartData(currencyPair=ticker, period=candlestick_period, start=chart_start,
		                           end=chart_end)).astype(float)
	ticker_chart_data.date = timestamp_to_UTC(ticker_chart_data['date'])
	ticker_as_stock = st.StockDataFrame.retype(ticker_chart_data)

	return ticker_as_stock[indicator.lower()]
