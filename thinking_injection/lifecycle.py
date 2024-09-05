from abc import abstractmethod
from contextlib import contextmanager, ExitStack

from dataclasses import dataclass
from logging import getLogger
from typing import Callable, Iterable, TypeVar, Protocol, ContextManager, runtime_checkable

log = getLogger(__name__)


@runtime_checkable
class Resettable(Protocol):
    def reset(self): pass


@runtime_checkable
class HasLifecycle(Protocol):
    @abstractmethod
    def lifecycle(self) -> ContextManager:
        yield


@runtime_checkable
class Initializable(HasLifecycle, Protocol):
    def initialize(self) -> None: pass

    def deinitialize(self, exc: BaseException | None) -> None: pass
        #todo type(self).__init__(self)

    def _initialize(self):
        log.info(f"Initializing {self}")
        self.initialize()
        log.debug(f"Initialization of {self} complete")

    def _deinitialize(self, exc):
        before_log_method = log.info if exc is None else log.error
        after_log_method = log.debug if exc is None else log.error
        log_detail = f" (exception: {exc!r})" if exc is not None else ""
        before_log_method(f"Deinitializing {self}{log_detail}")
        self.deinitialize(exc)
        after_log_method(f"Deinitialization of {self} complete")

    @contextmanager
    def lifecycle(self) -> ContextManager:
        self._initialize()
        exc = None
        try:
            yield
        except Exception as e:
            exc = e
            raise
        finally:
            self._deinitialize(exc)


def no_op(*args, **kwargs): pass


@dataclass
class CustomInitializable(Initializable):
    initialize: Callable[[], None] = no_op
    deinitialize: Callable[[BaseException | None], None] = no_op


@contextmanager
def composite_lifecycle(delegates: Iterable[HasLifecycle]) -> ContextManager:
    with ExitStack() as stack:
        for d in delegates:
            stack.enter_context(d.lifecycle())
        yield


@dataclass
class ReentrantLifecycleProxy[T: HasLifecycle](HasLifecycle):
    delegate: T
    already_entered: bool = False

    @contextmanager
    def lifecycle(self) -> ContextManager:
        if self.already_entered:
            yield
        else:
            #this is probably an overkill, but if python loses GIL, we may be already in luck
            prev_entered = self.already_entered
            try:
                self.already_entered = True
                with self.delegate.lifecycle():
                    yield
            finally:
                self.already_entered = prev_entered

    def __getattr__(self, item):
        return getattr(self.delegate, item)

    def __setattr__(self, key, value):
        return setattr(self.delegate, key, value)


def reentrant_proxy[T](delegate: T) -> T:
    return ReentrantLifecycleProxy(delegate)
