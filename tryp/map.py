from typing import TypeVar, Dict, Generic, Tuple, Callable

from toolz import dicttoolz  # type: ignore

from tek.tools import find  # type: ignore

from tryp.maybe import may, Maybe
from tryp.list import List

A = TypeVar('A')
B = TypeVar('B')


class Map(Dict[A, B], Generic[A, B]):  # type: ignore

    @staticmethod
    def wrap(d: Dict[A, B]) -> 'Map[A, B]':
        return Map(d)

    @may
    def get(self, key):
        return Dict.get(self, key)

    def __add__(self, item: Tuple[A, B]):
        return Map(dicttoolz.assoc(self, *item))

    def __pow__(self, other: 'Map[A, B]'):
        return Map(dicttoolz.merge(self, other))

    def find(self, f: Callable[[B], bool]) -> Maybe[Tuple[A, B]]:
        return Maybe(find(lambda a: f(self[a]), self.keys_view))\
            .map(lambda k: (k, self[k]))

    def find_key(self, f: Callable[[A], bool]) -> Maybe[Tuple[A, B]]:
        return Maybe(find(f, self.keys_view))\
            .map(lambda k: (k, self[k]))

    @property
    def keys_view(self):
        return Dict.keys(self)

    @property
    def values_view(self):
        return Dict.values(self)

    @property
    def keys(self):
        return List(*Dict.keys(self))

    @property
    def values(self):
        return List(*Dict.values(self))

    @property
    def is_empty(self):
        return self.keys.is_empty

__all__ = ['Map']
