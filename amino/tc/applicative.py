import abc
from typing import TypeVar, Generic

from amino.tc.apply import Apply

F = TypeVar('F')
A = TypeVar('A')


class Applicative(Generic[F], Apply[F]):

    @abc.abstractmethod
    def pure(self, a: A) -> F:
        ...

    @property
    def unit(self) -> F:
        return self.pure(None)

__all__ = ('Applicative',)
