import logging

from celery import shared_task

from apps.scholar.models import Investment
from apps.scholar.modules.advisor import Advisor

import numpy as np

from apps.scholar.modules.constants.states import NO_POSITION
from overlooker.redis import get_redis_connection

logger = logging.getLogger('info-console')


@shared_task
def get_best_strategy(investment: Investment):
    # investment actually is an EasyDict - Duck Typing

    # no async - add analysis_period, strategy_expiration_time
    # actually, run() should initiate a scheduler
    try:
        advisor = Advisor.update_and_retrieve(investment)
    except KeyError:
        # if not found, it is retrieved as new
        advisor = Advisor(investment)

    logger.info("advisor is starting to run")
    return advisor.run()


@shared_task
def evaluate_strategy_total_profit(strategy, **kwargs):
    return (
        strategy.evaluate(**kwargs).total_profit,
        {"strategy": strategy.__class__.__name__, **kwargs}
    )


@shared_task
def maximum(evaluation_group):
    a = np.array(evaluation_group)
    idx = a[:, 0].argmax()
    profit, data = a[idx, :].tolist()

    return {**data, "profit": profit}


@shared_task
def make_order(data: dict, strategies: list):
    strategy = next(s for s in strategies if s.__class__.__name__ == data["strategy"])

    rkeys = {"strategy", "profit"}
    kwargs = {key: data[key] for key in data.keys() - rkeys}

    current_state = NO_POSITION  # initial state

    order = strategy.execute(current_state, **kwargs)

    return {**data, "state": str(current_state), "order": str(order)}


@shared_task
def include_extra_info(data: dict, investment: Investment):
    return {
        **data,
        "amount": float(investment.amount),
        "market": str(investment.market),
        "stop loss": float(investment.stop_loss),
        "acc stop loss": float(investment.accumulated_stop_loss),
        "user": int(investment.user),
        "exchange": int(investment.exchange)
    }


@shared_task
def save_on_redis(data: dict, hash):
    redis = get_redis_connection()
    for key, val in data.items():
        redis.hset(hash, key, val)

    return data
