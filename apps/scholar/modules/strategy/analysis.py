from collections import OrderedDict
from itertools import product
from random import shuffle

from hyperopt import hp, tpe, fmin
from scipy.optimize import minimize
from tqdm import tqdm


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
        space = OrderedDict([(name, range(a, b + 1, c)) for name, a, b, c in bounds])
        grid = list(product(*space.values()))

        if max_iter:
            shuffle(grid)
        else:
            max_iter = float("inf")

        gen = tqdm(enumerate(grid), total=min(max_iter, len(grid)))

        _max = dict(__profit=-float("inf"), strategy=self.strategy.__class__.__name__)
        for i, args in gen:
            if i > max_iter:
                break

            kwargs = {name: v for name, v in zip(space.keys(), args)}
            new = {**kwargs, "__profit": -self.func(args)}
            _max = max(_max, new, key=lambda d: d["best_profit"])

            gen.set_postfix_str(s=f"max profit = {_max['__profit']:.3f}")

        return _max
