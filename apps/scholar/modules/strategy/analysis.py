from collections import OrderedDict
from itertools import product
from random import shuffle

import numpy as np
from hyperopt import hp, tpe, fmin
from scipy.optimize import minimize
from celery import group


class Optimization:

    def __init__(self, strategy, *args, **kwargs):
        self.strategy = strategy

        self.args = args
        self.kwargs = kwargs

    def func(self, args):
        return - self.strategy.evaluate(*args, *self.args, **self.kwargs).total_profit

    def minimization(self, x, **kwargs):
        opt_result = minimize(self.func, x0=x, **kwargs)
        return opt_result

    def hypertuning(self, bounds, **kwargs):
        space = [hp.uniform(name, a, b) for name, a, b in bounds]
        best = fmin(self.func, space=space, algo=tpe.suggest, **kwargs)

        return best

    def grid_search(self, bounds, max_iter=100):
        from apps.scholar.tasks import evaluate_strategy_total_profit as ev

        space = OrderedDict([(name, range(a, b + 1, c)) for name, a, b, c in bounds])
        grid = list(product(*space.values()))

        if max_iter:
            shuffle(grid)
            grid = grid[:max_iter]

        func = lambda args: ev.s(self.strategy, *args, *self.args, **self.kwargs)
        result = group(func(args) for args in grid).apply_async()
        idx = np.array(result).argmax()

        return {**{name: v for name, v in zip(space.keys(), grid[idx])}, "__profit": result[idx]}
