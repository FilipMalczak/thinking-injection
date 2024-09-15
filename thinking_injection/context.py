from abc import abstractmethod
from contextlib import contextmanager
from typing import NamedTuple, ContextManager, Callable, runtime_checkable, Protocol, Iterable

from thinking_injection.dependencies import DependencyGraph, Dependency, DependencyKind
from thinking_injection.ordering import TypeComparator
from thinking_injection.implementations import Implementations, ImplementationDetails
from thinking_injection.injectable import Injectable
from thinking_injection.lifecycle import HasLifecycle, Resettable, composite_lifecycle
from thinking_injection.requirements import RequirementsGraph
from thinking_injection.scope import ContextScope
from thinking_injection.typeset import TypeSet


@runtime_checkable
class ObjectLifecycle[T](Protocol):
    target: T

    @abstractmethod
    def lifecycle(self) -> ContextManager: pass


class ValueLifecycle[T](NamedTuple):
    target: T

    @contextmanager
    def lifecycle(self) -> ContextManager:
        yield


class LifecycleDelegator[T: HasLifecycle](NamedTuple):
    target: T

    @contextmanager
    def lifecycle(self) -> ContextManager:
        with self.target.lifecycle():
            yield


class InitializableLifecycle[T: HasLifecycle](NamedTuple):
    target: T
    injector: Callable[[], None]

    @contextmanager
    def lifecycle(self) -> ContextManager:
        try:
            self.injector()
            with self.target.lifecycle():
                yield
        finally:
            if isinstance(self.target, Resettable):
                self.target.reset()


@runtime_checkable
class Context(HasLifecycle, Protocol):
    # dependencies: DependencyGraph
    # implementations: Implementations
    # requirements: RequirementsGraph
    # lifecycles: dict[type, ObjectLifecycle]

    @abstractmethod
    def dependencies[T: type](self, t: T) -> frozenset[Dependency]: pass

    @abstractmethod
    def implementation_details[T: type](self, t: T) -> ImplementationDetails: pass

    @abstractmethod
    def prerequisites[T: type](self, t: T) -> frozenset[type]: pass

    @property
    @abstractmethod
    def types(self) -> Iterable[type]: pass

    @abstractmethod
    def instance[T](self, t: type[T]) -> T: pass

    @abstractmethod
    def instances[T](self, t: type[T]) -> frozenset[T]: pass


class AbstractContext(Context):
    _lifecycles: dict[type, ObjectLifecycle]

    def instance[T](self, t: type[T]) -> T:
        return self._lifecycles[self.implementation_details(t).primary].target

    def instances[T](self, t: type[T]) -> frozenset[T]:
        return frozenset(self._lifecycles[x].target for x in self.implementation_details(t).implementations)

    def _make_lifecycle[T: type](self, t: T) -> ObjectLifecycle[T]:
        instance = t()
        if issubclass(t, Injectable):
            return InitializableLifecycle(instance, lambda: self._inject_instance(t))
        if issubclass(t, HasLifecycle):
            return LifecycleDelegator(instance)
        return ValueLifecycle(instance)

    def _to_target(self, d: Dependency):
        chosen = d.kind.value.choose_implementations(self.implementation_details(d.type_))
        if d.kind == DependencyKind.COLLECTIVE: #todo externalize to dep kind or smth
            return [
                self._lifecycles[i].target
                for i in chosen
            ]
        return self._lifecycles[chosen].target

    def _inject_instance[T: type[Injectable]](self, t: T):
        instance: Injectable = self._lifecycles[t].target
        deps = self.dependencies(t)
        kwargs = {
            d.name: self._to_target(d)
            for d in deps
        }
        instance.inject_requirements(**kwargs)

    @contextmanager
    def lifecycle(self) -> ContextManager:
        try:
            lifecycles = []
            for t in self.types:
                lifecycle = self._make_lifecycle(t)
                lifecycles.append(lifecycle)
                self._lifecycles[t] = lifecycle
            with composite_lifecycle(lifecycles):
                yield
        finally:
            self._lifecycles.clear()

#todo context itself cannot be injected just yet


class BasicContext(AbstractContext):

    def __init__(self, scope: ContextScope, cyclic_resolver: TypeComparator = None):
        self._requirements = RequirementsGraph.build(scope)
        self._cyclic_resolver = cyclic_resolver
        self._lifecycles: dict[type, ObjectLifecycle] = {}

    def dependencies[T: type](self, t: T) -> frozenset[Dependency]:
        return frozenset(self._requirements.dependencies[t])

    def implementation_details[T: type](self, t: T) -> ImplementationDetails:
        return self._requirements.implementations[t]

    def prerequisites[T: type](self, t: T) -> frozenset[type]:
        return frozenset(self._requirements[t])

    @property
    def types(self) -> Iterable[type]:
        return self._requirements.order(self._cyclic_resolver)
