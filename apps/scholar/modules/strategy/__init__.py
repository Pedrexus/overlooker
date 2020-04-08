import pkgutil
from importlib import import_module
from pathlib import Path
from typing import List

from .strategy import Strategy
from ...models import Strategy as StrategyModel


def get_strategies_classes(strategies: List[StrategyModel]):
    return [Strategy.registry[st.name] for st in strategies]


# dynamically import the custom strategies
for (_, name, _) in pkgutil.iter_modules([Path(__file__).parent]):
    import_module('.' + name, package=__name__)
