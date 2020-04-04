import functools
import inspect
import types


def argsdispatch(func):
    """Single-dispatch generic function decorator.
    Transforms a function into a generic function, which can have different
    behaviours depending upon the values of its arguments. The decorated
    function acts as the default implementation, and additional
    implementations can be registered using the register() attribute of the
    generic function.
    """

    registry = {}

    # a list with the function parameters names
    params = list(inspect.signature(func).parameters)

    # No weakref is used in this implementation.
    # TODO: It might be useful to add weakref dispatch_cache in future.
    #  More study is necessary.

    def dispatch(kwargs):
        """generic_func.dispatch(kwargs) -> <function implementation>
        Runs the dispatch algorithm to return the best available implementation
        for the given *kwargs* registered on *generic_func*.
        """
        # the registered kwargs are found
        reg_kw = [kwargsfrset for kwargsfrset in registry.keys() if
                  dict(kwargsfrset).items() <= kwargs.items()]

        if reg_kw:
            # the most specific registry is chosen == the longest one
            most_specific_key = max(reg_kw)  # key = len
            # fetch the arguments exclusive to this impl
            excl_kw_keys = kwargs.keys() - dict(most_specific_key).keys()
            exclusive_kwargs = {key: kwargs[key] for key in excl_kw_keys}

            return registry[most_specific_key](**exclusive_kwargs)
        else:
            return func(**kwargs)

    def register(*args, **kw):
        """generic_func.register(kwarg)(func) -> func
        Registers a new implementation for the given *kw* on a *generic_func*.
        """
        if args:
            raise ValueError(f'{funcname}.register only accepts'
                             f' keyword arguments')
        elif not kw:
            raise TypeError(f'{funcname}.register requires at least '
                            '1 keyword argument')
        elif not set(kw.keys()) & set(params):
            unexpected = set(kw.keys()) - set(params)
            raise TypeError(f'{funcname}.register got unexpected keyword '
                            f'arguments {", ".join(unexpected)!r}')

        # TODO: try a better name
        def implementation(impl):
            impl__parameters = inspect.signature(impl).parameters
            if set(impl__parameters) == set(params) - set(kw):
                key = frozenset(kw.items())
                if key not in registry:
                    registry[key] = impl
                else:
                    raise ValueError(f'{funcname}.register cannot set a new '
                                     f'impl to arguments already registered.')

                return impl
            else:
                implname = getattr(impl, '__name__', 'registered function')
                diff = set(impl__parameters) - set(params)
                if diff:
                    raise TypeError(f'{implname} has arguments not listed '
                                    f'in {funcname}: {", ".join(diff)!r}')
                else:
                    diff = set(params) - set(kw) - set(impl__parameters)
                    raise TypeError(f'{implname} lacks arguments required '
                                    f'by {funcname}: {", ".join(diff)!r}')

        return implementation

    def wrapper(*args, **kw):
        # TODO: error and traceback needs improvement.
        # args and kw are joined into a dict
        kwargs = function_input_as_dict(func, *args, **kw)

        return dispatch(kwargs)

    funcname = getattr(func, '__name__', 'argument_dispatch function')

    wrapper.register = register
    wrapper.dispatch = dispatch
    wrapper.registry = types.MappingProxyType(registry)
    functools.update_wrapper(wrapper, func)

    return wrapper


def function_input_as_dict(func, *args, **kw):
    """auxiliar function of argument_dispatch decorator
    Inspect a function and some given *args and **kwargs and returns a dict
    with the equivalent arguments.
    """
    funcname = getattr(func, '__name__', 'argument_dispatch function')
    params = inspect.signature(func).parameters

    # 1. dict containing the default values
    defaults_dict = {param.name: param.default for param in params.values() if
                     param.default is not inspect.Parameter.empty}

    # 2. dict with positional arguments values
    args_dict = {param.name: arg for param, arg in zip(params.values(), args)}

    # 3. assert there is no argument being assigned multiple times
    multiple = set(args_dict) & set(kw)

    if multiple:
        raise TypeError(f'{funcname}() got multiple values for '
                        f'arguments {", ".join(multiple)!r}')
    else:
        # 4. dict with all respective values as kwargs is built.
        # Notice that deafults_dict may be overwritten.
        kwargs = {**defaults_dict, **args_dict, **kw}

    if set(params) ^ set(kwargs):
        if set(params) - set(kwargs):
            miss = set(params) - set(kwargs)
            raise TypeError(f'{funcname}() missing {len(miss)} required '
                            f'arguments: {", ".join(miss)!r}')
        elif set(kwargs) - set(params):
            unexpected = set(kwargs) - set(params)
            raise TypeError(f'{funcname}() got unexpected keyword '
                            f'arguments {", ".join(unexpected)!r}')
    else:
        return kwargs