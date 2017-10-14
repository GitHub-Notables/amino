import inspect
from typing import TypeVar, Type, Any, Generic, GenericMeta, cast, Generator

from amino import Map, Lists, List, Nil, _, Either, Right, Maybe
from amino.util.string import ToStr
from amino.func import Val
from amino.do import tdo
from amino.lazy import lazy

A = TypeVar('A')


class KeepField:
    pass


def qualified_type(tpe: Type) -> str:
    return tpe.__name__ if tpe.__module__ == 'builtins' else f'{tpe.__module__}.{tpe.__name__}'


class Field(ToStr):

    def __init__(self, name: str, tpe: Type) -> None:
        self.name = name
        self.tpe = tpe

    @property
    def qualified_type(self) -> None:
        return qualified_type(self.tpe)

    def _arg_desc(self) -> List[str]:
        return List(self.name, self.qualified_type)

    @property
    def param_str(self) -> str:
        return f'''{self.name}: '{self.qualified_type}'=Dat.Keep'''


Sub = TypeVar('Sub', bound='Dat')


class FieldMutator(Generic[Sub]):

    def __init__(self, name: str, target: 'Dat[Sub]') -> None:
        self.name = name
        self.target = target


class FieldSetter(Generic[Sub], FieldMutator[Sub]):

    def __call__(self, value) -> Sub:
        return self.target.copy(**{self.name: value})


class FieldModifier(Generic[Sub], FieldMutator[Sub]):

    def __call__(self, f) -> Sub:
        return self.target.copy(**{self.name: f(getattr(self.target, self.name))})


class FieldAppender(Generic[Sub], FieldMutator[Sub]):

    def __call__(self, value) -> Sub:
        return self.target.mod(self.name, _ + value)


class FieldAppender1(Generic[Sub], FieldMutator[Sub]):

    def __call__(self, value) -> Sub:
        return self.target.mod(self.name, _ + List(value))


class FieldProxy(Generic[Sub], FieldMutator[Sub]):

    def __init__(self, target: 'Dat', tpe: type) -> None:
        self.target = target
        self.tpe = tpe

    def __getattr__(self, name):
        return self(name)

    def __call__(self, name):
        return self.tpe(name, self.target)


def init_fields(spec: inspect.FullArgSpec) -> List[Field]:
    args = Lists.wrap(spec.args).tail | Nil
    types = Map(spec.annotations)
    def field(name: str) -> Field:
        tpe = types.lift(name) | Val(Any)
        return Field(name, tpe)
    return args / field


class DatMeta(GenericMeta):

    def __new__(cls: type, name: str, bases: tuple, namespace: dict, **kw) -> type:
        fs = Map(namespace).lift('__init__') / inspect.getfullargspec / init_fields | Nil
        inst = super().__new__(cls, name, bases, namespace, **kw)
        if fs:
            inst._dat__fields = fs
        return inst


class Dat(Generic[Sub], metaclass=DatMeta):
    Keep = KeepField()

    @lazy
    def _dat__values(self) -> List[Any]:
        return self._dat__fields.traverse(lambda a: Maybe.getattr(self, a.name), Maybe)

    def copy(self, **kw: Any) -> Sub:
        updates = Map(kw)
        def update(f: Field) -> Any:
            return updates.lift(f.name) | getattr(self, f.name)
        updated = self._dat__fields / update  # type: ignore
        return cast(Dat, type(self)(*updated))

    @property
    def append(self) -> FieldProxy:
        return FieldProxy(self, FieldAppender)

    @property
    def append1(self) -> FieldProxy:
        return FieldProxy(self, FieldAppender1)

    @property
    def mod(self) -> FieldProxy:
        return FieldProxy(self, FieldModifier)

    @property
    def set(self) -> FieldProxy:
        return FieldProxy(self, FieldSetter)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and self._dat__values == other._dat__values

    def _lens_setattr(self, name, value):
        return self.set(name)(value)

__all__ = ('Dat',)
