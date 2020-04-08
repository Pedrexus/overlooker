from rest_framework import routers

from apps.scholar.views import ExchangeViewSet, ExchangeConnectionViewSet, StrategyViewSet, \
    InvestmentViewSet

router = routers.DefaultRouter()

router.register('exchange', ExchangeViewSet, basename='exchange')
router.register('connection', ExchangeConnectionViewSet, basename='exchange-connection')
router.register('strategy', StrategyViewSet, basename='strategy')
router.register('investment', InvestmentViewSet, basename='investment')

urlpatterns = router.urls
