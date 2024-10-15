from abc import abstractmethod
from contextlib import contextmanager
from typing import runtime_checkable, Protocol, NamedTuple, ContextManager, Callable, Self

from thinking_injection.cloneable import Cloneable
from thinking_injection.common.implementations import ImplementationDetails
from thinking_injection.context.protocol import InstanceIndex, ApplicationContext
from thinking_injection.common.dependencies import Dependency, DependencyKind
from thinking_injection.injectable import Injectable
from thinking_injection.lifecycle import HasLifecycle, Resettable, composite_lifecycle
from thinking_injection.ordering import TypeComparator
from thinking_injection.registry.delegating import TypeRegistryDelegateMixin
from thinking_injection.registry.protocol import TypeIndex, TypeRegistry
from thinking_injection.registry.simple import SimpleRegistry
from thinking_injection.typeset import AnyTypeSet
from thinking_programming.collectable import Collectable


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




class SimpleIndex(InstanceIndex):
    def __init__(self, index: TypeIndex):
        assert index is not None #todo msg
        self.index = index
        self._lifecycles = {}
        self._raw_manager = self._lifecyle_context_manager()

    def __enter__(self):
        self._raw_manager.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        result = self._raw_manager.__exit__(exc_type, exc_value, traceback)
        return result

    @contextmanager
    def _lifecyle_context_manager(self) -> ContextManager:
        try:
            lifecycles = []
            for t in self.index.known_concrete_types():
                lifecycle = self._make_lifecycle(t)
                lifecycles.append(lifecycle)
                self._lifecycles[t] = lifecycle
            with composite_lifecycle(lifecycles):
                yield
        finally:
            self._lifecycles.clear()

    def instance[T](self, t: type[T]) -> T:
        return self._lifecycles[self.index.primary_implementation(t)].target

    def instances[T](self, t: type[T]) -> frozenset[T]:
        return frozenset(self._lifecycles[x].target for x in self.index.implementations(t))

    def _make_lifecycle[T: type](self, t: T) -> ObjectLifecycle[T]:
        instance = t()
        if issubclass(t, Injectable):
            return InitializableLifecycle(instance, lambda: self._inject_instance(t))
        if issubclass(t, HasLifecycle):
            return LifecycleDelegator(instance)
        return ValueLifecycle(instance)

    def _to_target(self, d: Dependency):
        details = ImplementationDetails(self.index.implementations(d.type_), self.index.primary_implementation(d.type_))
        chosen = d.kind.value.choose_implementations(details)
        if d.kind == DependencyKind.COLLECTIVE: #todo externalize to dep kind or smth
            return [
                self._lifecycles[i].target
                for i in chosen
            ]
        return self._lifecycles[chosen].target

    def _inject_instance[T: type[Injectable]](self, t: T):
        instance: Injectable = self._lifecycles[t].target
        deps = self.index.dependencies(t)
        kwargs = {
            d.name: self._to_target(d)
            for d in deps
        }
        instance.inject_requirements(**kwargs)


class SimpleContext(ApplicationContext[SimpleIndex], TypeRegistryDelegateMixin):
    def __init__(self, typeset: AnyTypeSet = None, cyclic_resolver: TypeComparator = None):
        self.registry: TypeRegistry = SimpleRegistry(typeset or [])
        self._cyclic_resolver = cyclic_resolver

    def lifecycle(self) -> SimpleIndex:
        return SimpleIndex(self.registry.type_index())

    def remove(self, *t: Collectable[type]):
        self.registry.remove(*t)

    def clone(self) -> Self:
        out = SimpleContext()
        out.registry = self.registry.clone()
        resolver = self._cyclic_resolver.clone() if isinstance(self._cyclic_resolver, Cloneable) else self._cyclic_resolver
        out._cyclic_resolver = resolver