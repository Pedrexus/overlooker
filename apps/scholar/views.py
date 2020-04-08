from rest_framework import viewsets, permissions

from apps.scholar.models import Exchange, ExchangeConnection, Strategy, Investment
from apps.scholar.serializers import ExchangeSerializer, ExchangeConnectionSerializer, \
    StrategySerializer, InvestmentSerializer


class ExchangeViewSet(viewsets.ModelViewSet):
    queryset = Exchange.objects.all()
    serializer_class = ExchangeSerializer
    permission_classes = [permissions.AllowAny]

    # authentication_classes = [authentication.TokenAuthentication, jwt_auth.JWTAuthentication]
    # permission_classes = [permissions.AllowAny]


class ExchangeConnectionViewSet(viewsets.ModelViewSet):
    queryset = ExchangeConnection.objects.all()
    serializer_class = ExchangeConnectionSerializer
    permission_classes = [permissions.AllowAny]


class StrategyViewSet(viewsets.ModelViewSet):
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer
    permission_classes = [permissions.AllowAny]


class InvestmentViewSet(viewsets.ModelViewSet):
    queryset = Investment.objects.all()
    serializer_class = InvestmentSerializer
    permission_classes = [permissions.AllowAny]
