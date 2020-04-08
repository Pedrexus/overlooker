from easydict import EasyDict
from rest_framework import serializers

from apps.scholar.models import Exchange, ExchangeConnection, Strategy, Investment
from apps.scholar.signals import serializer_created


class ExchangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exchange
        fields = '__all__'


class ExchangeConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeConnection
        fields = '__all__'


class InvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investment
        fields = '__all__'

    def create(self, validated_data):
        serializer_created.send(sender=self.__class__, instance=EasyDict(validated_data))
        return super().create(validated_data)


class StrategySerializer(serializers.ModelSerializer):
    investments = InvestmentSerializer(many=True, read_only=True)

    class Meta:
        model = Strategy
        fields = '__all__'
