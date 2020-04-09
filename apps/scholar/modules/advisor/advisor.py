from functools import lru_cache
from itertools import product

from celery import group

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

    def __hash__(self):
        return hash(self.key(self.investment))

    @staticmethod
    def key(investment: Investment):
        return investment.user.pk, investment.exchange.pk, investment.market  # unique together

    @classmethod
    def get(cls, investment):
        return cls.registry[cls.key(investment)]

    @classmethod
    def update_and_retrieve(cls, investment):
        advisor = cls.get(investment)

        # advisor.investment = investment
        # advisor.api.cache_clear()
        # advisor.strategies.cache_clear()

        # also possible, but probably more expensive:
        advisor = cls(investment)
        cls.registry[cls.key(investment)] = advisor

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
        from apps.scholar.tasks import evaluate_strategy_total_profit as evaluate
        from apps.scholar.tasks import maximum, make_order, include_extra_info, save_on_redis

        chart = self.api()().date_as_datetime().as_dataframe()

        strategies = [StrategyClass(chart) for StrategyClass in self.strategies()]
        params = [dict(
            lower_limit=[40], upper_limit=[60],
            rsi_n=list(range(10, 15, 2)), ema_n=list(range(100, 200, 40))
        )]

        def gen(strategies_list: list, params_list: list):
            for st, args in zip(strategies_list, params_list):
                for point in product(*args.values()):
                    yield {"strategy": st, **dict(zip(args.keys(), point))}

        evaluation = (
                group(evaluate.s(**kwargs) for kwargs in gen(strategies, params))
                | maximum.s()
                | make_order.s(strategies)
                | include_extra_info.s(self.investment)
                | save_on_redis.s(hash(self))
        ).apply_async()

        return evaluation
