import abc
from typing import TypeVar, Generic, Callable, Union

from tryp.tc.base import TypeClass
from tryp import maybe  # NOQA
from tryp.boolean import Boolean

F = TypeVar('F')
A = TypeVar('A')
B = TypeVar('B')


class Optional(Generic[F], TypeClass):

    @abc.abstractmethod
    def to_maybe(self, fa: F) -> 'maybe.Maybe[B]':
        ...

    def get_or_else(self, fa: F, a: Union[A, Callable[[], A]]):
        return self.to_maybe(fa).get_or_else(a)

    @abc.abstractmethod  # type: ignore
    def to_either(self, fb: F, left: Union[A, Callable[[], A]]
                  ) -> 'Either[A, B]':
        ...

    __or__ = get_or_else

    def contains(self, fa: F, item):
        return self.to_maybe(fa).contains(item)

    @abc.abstractmethod
    def present(self, fa: F) -> Boolean:
        ...

    def or_else(self, fa: F, a: Union[F, Callable[[], F]]):
        return fa if self.present(fa) else maybe.call_by_name(a)

    def task(self, fa: F, err: str=''):
        from tryp.task import Task
        return Task.from_either(self.to_either(fa, err))

__all__ = ('Optional',)
