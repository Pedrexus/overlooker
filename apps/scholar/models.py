"""
    The scholar will run periodically after a new Investment entry is placed.
    It communicates with the api using http.

    A new Investment needs:
        1. api
        2. market
        3. amount
        4. mstop_markup, limit_markup (%)
        5. stop_limit_expiration_time
        6. strategy_expiration_time:
            the time the BEST strategy shall hold before it is reevaluated.
        7. analysis_period: schedules the analysis process
        8. candlestick_period
        9. start_date
        10. strategies: list of strategies to be tested
        11. strategies configurations:
            1. hyperparameters

    The analysis process finds the best strategy with the best parameters. Then,
    it creates a new order entry in the broker/database for the {api, market} combination:

        1. ORDER: buy, sell, hold, end
        2. VISUALIZED: False
        3. STRATEGY
        4. PARAMETERS

    Periodically, the api.market.chart is retrieved and the strategy updates the order entry

    Beyond that, every analysis result should be LOGGED and recorded in a database
    for further analysis.
"""
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class Exchange(models.Model):
    name = models.CharField("name", max_length=100, unique=True, blank=False)

    class Meta:
        verbose_name = 'Exchange'
        verbose_name_plural = 'Exchanges'

    def __str__(self):
        return str(self.name)


class ExchangeConnection(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name="user",
                             verbose_name="user")
    exchange = models.ForeignKey(Exchange,
                                 on_delete=models.CASCADE,
                                 related_name="exchange",
                                 verbose_name="exchange")
    public_key = models.CharField("public key", max_length=1000, blank=False)
    secret_key = models.CharField("secret key", max_length=1000, blank=False)

    # binary_secret_key = models.BinaryField("binary secret key", max_length=1000, blank=True)

    class Meta:
        verbose_name = 'Exchange Connection'
        verbose_name_plural = 'Exchange Connections'

        unique_together = ('user', 'exchange', 'public_key', 'secret_key')

    def __str__(self):
        return f"{self.exchange} - {self.user.fullname}"

    def binary_secret_key(self):
        # To be used with poloniex exchange api
        return bytes(str(self.secret_key), encoding='utf-8')


class Strategy(models.Model):
    name = models.CharField("name", max_length=100, unique=True, blank=False)

    #  hyperparams = field key-value

    class Meta:
        verbose_name = 'Strategy'
        verbose_name_plural = 'Strategies'

    def __str__(self):
        return str(self.name)

    def register(self, cls):
        pass


class StrategyParameter(models.Model):
    # a abordagem pode ser outra. O usuario seleciona quais
    # parametros ele quer variar, mas os intervalos e valores padrao ja seriam pre definidos
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    min_bound = models.DecimalField("min bound", max_digits=6, decimal_places=2, blank=False) # or value
    max_bound = models.DecimalField("max bound", max_digits=6, decimal_places=2, blank=True)
    step = models.DecimalField("step", max_digits=6, decimal_places=2, blank=True)

    class Meta:
        verbose_name = 'Strategy Parameter'
        verbose_name_plural = 'Strategy Parameter'


class Investment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=False)
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, blank=False)
    market = models.CharField("market", max_length=7, blank=False)  # TODO: choices
    amount = models.DecimalField("amount", max_digits=17, decimal_places=8,
                                 blank=False)  # btc to satoshi
    stop_loss = models.DecimalField("stop loss", max_digits=2, decimal_places=2, blank=False)
    accumulated_stop_loss = models.DecimalField("accumulated stop loss", max_digits=2,
                                                decimal_places=2, blank=False)
    stop_markup = models.DecimalField("stop markup", max_digits=17, decimal_places=8, blank=False)
    limit_markup = models.DecimalField("limit markup", max_digits=17, decimal_places=8,
                                       blank=False)
    stop_limit_expiration_time = models.DurationField("stop-limit expiration time", blank=False)
    strategy_expiration_time = models.DurationField("strategy expiration time", blank=False)
    analysis_period = models.DurationField("analysis period", blank=False)
    candlestick_period = models.DurationField("candlestick period", blank=False)
    start_date = models.DateTimeField("start date", blank=False)
    strategies = models.ManyToManyField(Strategy, related_name="investments", blank=False)
    # strategies_params =

    class Meta:
        verbose_name = 'Investment'
        verbose_name_plural = 'Investments'

        unique_together = ('user', 'exchange', 'market')

    def __str__(self):
        return f"{self.market}({self.exchange}, amount={self.amount})"

    @property
    def credentials(self):
        return ExchangeConnection.objects.get(
            user=self.user,
            exchange=self.exchange
        )

    def save(self, *args, **kwargs):
        try:
            credentials = self.credentials
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist(f"Credentials not found for {self.user} with {self.exchange}")

        super(Investment, self).save(*args, **kwargs)
