import pkgutil
from importlib import import_module
from pathlib import Path
from typing import List

from apps.scholar.models import Exchange
from apps.scholar.modules.exchange.asset import Asset


def get_exchange_class(exchange: Exchange):
    return Asset.registry[exchange.name]


# dynamically import the custom api, adding to Asset.registry
for (_, name, _) in pkgutil.iter_modules([Path(__file__).parent]):
    import_module('.' + name, package=__name__)
