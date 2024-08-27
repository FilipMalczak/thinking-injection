from abc import abstractmethod
from contextlib import contextmanager
from typing import NamedTuple, ContextManager, Callable, runtime_checkable, Protocol

from thinking_injection.dependencies import DependencyGraph
from thinking_injection.ordering import TypeComparator
from thinking_injection.implementations import Implementations
from thinking_injection.injectable import Injectable
from thinking_injection.lifecycle import HasLifecycle, Resettable, composite_lifecycle
from thinking_injection.requirements import RequirementsGraph
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
    dependencies: DependencyGraph
    implementations: Implementations
    requirements: RequirementsGraph
    cyclic_resolver: TypeComparator
    lifecycles: dict[type, ObjectLifecycle]

    @classmethod
    def build(cls, types: TypeSet, defaults: dict[type, type] = None, force: dict[type, type] = None, cyclic_resolver: TypeComparator = None):
        dependencies = DependencyGraph.build(types)
        implementations = Implementations.build(set(dependencies.keys()), defaults, force)
        requirements = RequirementsGraph.build(dependencies, implementations)
        lifecycles: dict[type, ObjectLifecycle] = {}
        return cls(dependencies, implementations, requirements, cyclic_resolver, lifecycles)

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

    def _inject_instance[T: type[Injectable]](self, t: T):
        instance: Injectable = self.lifecycles[t].target
        deps = self.dependencies[t]
        kwargs = {
            d.name: d.kind.value.choose_implementations(self.implementations[t])
            for d in deps
        }
        instance.inject_requirements(**kwargs)



    @contextmanager
    def lifecycle(self) -> ContextManager:
        try:
            lifecycles = []
            for t in self.requirements.order(self.cyclic_resolver):
                instance = t()
                lifecycle = self._make_lifecycle(instance)
                lifecycles.append(lifecycle)
                self.lifecycles[t] = lifecycle
            with composite_lifecycle(lifecycles):
                yield
        finally:
            self.lifecycles.clear()
