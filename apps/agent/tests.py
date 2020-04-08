import datetime as dt

import pytest
import pytz
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.scholar.models import Investment, Exchange, Strategy


class SetUp:

    user = {
        "email": "user@user.com",
        "fullname": "Mr. User",
        "password": "2u98@*j0"
    }

    exchange = {
        "id": 1,
        "name": "Poloniex"
    }

    strategy = {
        "id": 1,
        "name": "AdaptivePQ"
    }

    investment = {
        "user_id": None,
        "exchange_id": None,
        "market": "BTC_LTC",
        "amount": 0.001,
        "stop_markup": 1e-6,
        "limit_markup": 1e-6,
        "stop_limit_expiration_time": dt.timedelta(hours=1),
        "strategy_expiration_time": dt.timedelta(days=1),
        "analysis_period": dt.timedelta(minutes=45),
        "candlestick_period": dt.timedelta(minutes=30),
        "start_date": dt.datetime.now() - dt.timedelta(weeks=8),  # dt.datetime(2020, 1, 1, 12, 00, 00, tzinfo=pytz.UTC)  #
    }

    investment_strategies = []

    def create_user(self):
        User = get_user_model()
        user = User.objects.create(**self.user)
        user.save()

        return user

    def create_exchange(self):
        ex = Exchange.objects.create(**self.exchange)
        ex.save()

        return ex

    def create_strategy(self):
        st = Strategy.objects.create(**self.strategy)
        st.save()

        return st

    def create_investment(self):
        user = self.create_user()
        self.investment["user_id"] = user.id

        exchange = self.create_exchange()
        self.investment["exchange_id"] = exchange.id

        strategy = self.create_strategy()
        self.investment_strategies.append(strategy.id)

        investment = Investment.objects.create(**self.investment)
        investment.strategies.set(self.investment_strategies)
        investment.save()

        return investment


@pytest.mark.django_db
class TestAgent(SetUp):

    def test_(self):
        # client = APIClient()

        investment = self.create_investment()

        assert investment is not None