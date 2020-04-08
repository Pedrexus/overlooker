import logging

from django.db.models.signals import post_delete
from django.dispatch import receiver
from apps.scholar.models import Investment
from apps.scholar.modules.advisor.advisor import Advisor
from .signals import serializer_created
from ..serializers import InvestmentSerializer as InvSerial
from ..tasks import get_best_strategy

logger = logging.getLogger('info-console')


@receiver(serializer_created, sender=InvSerial, weak=False, dispatch_uid="start_analysis")
def start_analysis(sender: InvSerial, instance: Investment, **kwargs):
    # instance actually is an EasyDict - Duck Typing
    get_best_strategy.delay(instance)


@receiver(post_delete, sender=Investment, weak=False, dispatch_uid="stop_analysis")
def stop_analysis(sender: Investment, instance: Investment, **kwargs):
    try:
        advisor = Advisor.get(instance)

        logger.info("advisor is going to stop")
        # advisor.stop()
        logger.info("advisor is stopping")
    except KeyError:
        logger.error("advisor was not found")
