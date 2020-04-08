from django.contrib import admin
from .models import Exchange, ExchangeConnection, Strategy, Investment

admin.site.register(Exchange)
admin.site.register(ExchangeConnection)
admin.site.register(Strategy)
admin.site.register(Investment)
