import logging

from celery import shared_task

from apps.scholar.models import Investment
from apps.scholar.modules.advisor.advisor import Advisor

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
        try:
            advisor = Advisor(investment)
        except ValueError:
            return

    logger.info("advisor is starting to run")
    advisor.run()
    logger.info("advisor is running")
