from functools import lru_cache

from apps.scholar.models import Investment
from apps.scholar.modules.strategy import get_strategies_classes
from apps.scholar.modules.exchange import get_exchange_class


class Advisor:
    registry = {}

    def __init__(self, investment: Investment):
        # if new investment is created, a new advisor is created for it
        # there is only 1 advisor for investment
        if len(investment.strategies) == 0:
            raise ValueError("investment strategies cannot be empty")

        self.investment = investment
        self.registry[self.key(investment)] = self

    def __repr__(self):
        return (
            f"Advisor("
            f"market={self.investment.market}, "
            f"amount={float(self.investment.amount)}, "
            f"exchange={self.investment.exchange}, "
            f"strategies={[s.name for s in self.investment.strategies]})"
        )

    @staticmethod
    def key(investment: Investment):
        return investment.user.pk, investment.exchange.pk, investment.market  # unique together

    @classmethod
    def get(cls, investment):
        return cls.registry[cls.key(investment)]

    @classmethod
    def update_and_retrieve(cls, investment):
        advisor = cls.get(investment)

        advisor.investment = investment
        advisor.api.cache_clear()
        advisor.strategies.cache_clear()

        # also possible, but probably more expensive:
        # advisor = cls(investment)
        # cls.registry[investment.pk] = advisor

        return advisor

    @lru_cache(maxsize=2)
    def api(self):
        ExchangeAPIClass = get_exchange_class(self.investment.exchange)
        return ExchangeAPIClass(
            self.investment.market,
            self.investment.candlestick_period,
            self.investment.start_date
        )

    @lru_cache(maxsize=2)
    def strategies(self):
        return get_strategies_classes(self.investment.strategies)

    def run(self):
        chart = self.api()().date_as_datetime().as_dataframe()

        best_strategy = []
        for StrategyClass in self.strategies():
            strategy = StrategyClass(chart)
            # FIXME: make for generic strategy
            analysis = strategy.optimize(lower_limit=40, upper_limit=60).grid_search(
                bounds=[("rsi_n", 1, 5, 2), ("ema_n", 1, 20, 5)],
                max_iter=None,
            )
            best_strategy.append(analysis)

        return max(best_strategy, key=lambda s: s["__profit"])
