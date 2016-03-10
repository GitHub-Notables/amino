class AnonGetter:

    def __init__(self, pre: 'AnonFunc', name: str) -> None:
        self.pre = pre
        self.name = name

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.name)

    def __call__(self, obj):
        pre = self.pre(obj)
        if not hasattr(pre, self.name):
            raise AttributeError(
                '{!r} has no method \'{}\''.format(obj, self.name))
        return self._dispatch(getattr(pre, self.name))

    def _dispatch(self, obj):
        return obj


class AnonFunc(AnonGetter):

    def __init__(self, pre: 'AnonFunc', name: str, a, kw) -> None:
        super().__init__(pre, name)
        self.a = a
        self.kw = kw

    def _dispatch(self, obj):
        return obj(*self.a, **self.kw)

    def __getattr__(self, name):
        return MethodRef(self, name)


class MethodRef:

    def __init__(self, pre: AnonFunc, name: str) -> None:
        self.pre = pre
        self.name = name

    def __call__(self, *a, **kw):
        return AnonFunc(self.pre, self.name, a, kw)

    def __getattr__(self, name):
        pre = AnonGetter(self.pre, self.name)
        return MethodRef(pre, name)


class IdAnonFunc:

    def __call__(self, obj):
        return obj


class MethodLambda:

    def __getattr__(self, name):
        return MethodRef(IdAnonFunc(), name)

__ = MethodLambda()

__all__ = ('__', )
