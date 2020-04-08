from celery import shared_task

from .asset import Asset
from poloniex import Poloniex as PoloniexAPI


class Poloniex(Asset):

    def return_ticker(self):
        return PoloniexAPI().returnTicker()[self.currency_pair]

    def return_chart_data(self):
        return PoloniexAPI().returnChartData(
            self.currency_pair,
            self.candlestick_period,
            self.chart_start,
            self.chart_end
        )
