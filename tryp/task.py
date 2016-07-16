from typing import Callable, TypeVar, Generic, Any

from tryp import Either, Right, Left, Maybe
from tryp.tc.monad import Monad
from tryp.tc.base import ImplicitInstances, Implicits
from tryp.lazy import lazy

A = TypeVar('A')
B = TypeVar('B')


class TaskInstances(ImplicitInstances):

    @lazy
    def _instances(self):
        from tryp.map import Map
        return Map({Monad: TaskMonad()})


class Task(Generic[A], Implicits, implicits=True):

    @staticmethod
    def call(f: Callable[..., A], *a, **kw):
        return Task(lambda: f(*a, **kw))

    @staticmethod
    def now(a: A) -> 'Task[A]':
        return Task(lambda: a)

    @staticmethod
    def failed(err: str) -> 'Task[A]':
        def fail():
            raise Exception(err)
        return Task(fail)

    @staticmethod
    def from_either(a: Either[Any, A]) -> 'Task[A]':
        return a.cata(Task.failed, Task.now)

    @staticmethod
    def from_maybe(a: Maybe[A], error: str) -> 'Task[A]':
        return a / Task.now | Task.failed(error)

    def __init__(self, f: Callable[[], A]) -> None:
        self.run = f

    def unsafe_perform_sync(self) -> Either[Exception, A]:
        try:
            return Right(self.run())
        except Exception as e:
            return Left(e)


def Try(f: Callable[..., A], *a, **kw) -> Either[Exception, A]:
    return Task.call(f, *a, **kw).unsafe_perform_sync()


class TaskMonad(Monad):

    def pure(self, a: A):
        return Task(lambda: a)

    def flat_map(self, fa: Task[A], f: Callable[[A], Task[B]]) -> Task[B]:
        return Task(lambda: f(fa.run()).run())

__all__ = ('Task', 'Try')
