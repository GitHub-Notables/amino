from functools import wraps, partial  # type: ignore
from inspect import getfullargspec  # type: ignore

import fn  # type: ignore


class F(fn.F):

    def __truediv__(self, f):
        return self >> (lambda a: a / f)

    def __floordiv__(self, f):
        return self >> (lambda a: a // f)


def curried(func):
    @wraps(func)
    def _curried(*args, **kwargs):
        f = func
        count = 0
        while isinstance(f, partial):
            if f.args:
                count += len(f.args)
            f = f.func
        spec = getfullargspec(f)
        if count == len(spec.args) - len(args):
            return func(*args, **kwargs)
        else:
            return curried(partial(func, *args, **kwargs))
    return _curried

__all__ = ('curried', 'F')
