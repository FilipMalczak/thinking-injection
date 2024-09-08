from abc import abstractmethod
from contextlib import contextmanager
from typing import NamedTuple, ContextManager, Callable, runtime_checkable, Protocol

from thinking_injection.dependencies import DependencyGraph, Dependency, DependencyKind
from thinking_injection.ordering import TypeComparator
from thinking_injection.implementations import Implementations
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
    dependencies: DependencyGraph
    implementations: Implementations
    requirements: RequirementsGraph
    lifecycles: dict[type, ObjectLifecycle]

    @abstractmethod
    def instance[T](self, t: type[T]) -> T: pass

    @abstractmethod
    def instances[T](self, t: type[T]) -> frozenset[T]: pass

#todo context itself cannot be injected just yet

class BasicContext(NamedTuple):
    requirements: RequirementsGraph
    cyclic_resolver: TypeComparator
    lifecycles: dict[type, ObjectLifecycle]

    @property
    def dependencies(self) -> DependencyGraph:
        return self.requirements.dependencies

    @property
    def implementations(self) -> Implementations:
        return self.requirements.implementations

    @property
    def scope(self) -> ContextScope:
        return self.requirements.scope

    #todo types property?

    @classmethod
    def build(cls, scope: ContextScope, cyclic_resolver: TypeComparator = None):
        requirements = RequirementsGraph.build(scope)
        lifecycles: dict[type, ObjectLifecycle] = {}
        return cls(requirements, cyclic_resolver, lifecycles)

    def instance[T](self, t: type[T]) -> T:
        return self.lifecycles[self.implementations[t].primary].target

    def instances[T](self, t: type[T]) -> frozenset[T]:
        return frozenset(self.lifecycles[x].target for x in self.implementations[t].implementations)

    def _make_lifecycle[T: type](self, t: T) -> ObjectLifecycle[T]:
        instance = t()
        if issubclass(t, Injectable):
            return InitializableLifecycle(instance, lambda: self._inject_instance(t))
        if issubclass(t, HasLifecycle):
            return LifecycleDelegator(instance)
        return ValueLifecycle(instance)

    def _to_target(self, d: Dependency):
        chosen = d.kind.value.choose_implementations(self.implementations[d.type_])
        if d.kind == DependencyKind.COLLECTIVE: #todo externalize to dep kind or smth
            return [
                self.lifecycles[i].target
                for i in chosen
            ]
        return self.lifecycles[chosen].target

    def _inject_instance[T: type[Injectable]](self, t: T):
        instance: Injectable = self.lifecycles[t].target
        deps = self.dependencies[t]
        kwargs = {
            d.name: self._to_target(d)
            for d in deps
        }
        instance.inject_requirements(**kwargs)



    @contextmanager
    def lifecycle(self) -> ContextManager:
        try:
            lifecycles = []
            for t in self.requirements.order(self.cyclic_resolver):
                lifecycle = self._make_lifecycle(t)
                lifecycles.append(lifecycle)
                self.lifecycles[t] = lifecycle
            with composite_lifecycle(lifecycles):
                yield
        finally:
            self.lifecycles.clear()
