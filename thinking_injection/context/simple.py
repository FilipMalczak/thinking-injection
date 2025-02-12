from abc import abstractmethod
from contextlib import contextmanager
from logging import getLogger
from typing import runtime_checkable, Protocol, NamedTuple, ContextManager, Callable, Self

from thinking_injection.cloneable import Cloneable
from thinking_injection.common.dependencies import Dependency, DependencyKind, KindDefinition
from thinking_injection.common.implementations import ImplementationDetails
from thinking_injection.context.protocol import InstanceIndex, ApplicationContext
from thinking_injection.injectable import Injectable
from thinking_injection.invoker.contextful import ContextfulInvoker
from thinking_injection.invoker.protocol import Invoker
from thinking_injection.lifecycle import HasLifecycle, Resettable, composite_lifecycle
from thinking_injection.ordering import TypeComparator, CyclicResolver
from thinking_injection.registry.customizable.protocol import CustomizableTypeRegistry
from thinking_injection.registry.delegating import TypeRegistryDelegateMixin
from thinking_injection.registry.protocol import TypeIndex
from thinking_injection.registry.simple import SimpleRegistry
from thinking_injection.typeset import AnyTypeSet
from thinking_programming.collectable import Collectable
from thinking_programming.exceptions import NoneValueException

log = getLogger(__name__)


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


class SimpleInstanceIndex(InstanceIndex):
    def __init__(self, index: TypeIndex, cyclic_resolver: CyclicResolver):
        NoneValueException.guard(index)
        self.index = index #todo make private
        self.cyclic_resolver = cyclic_resolver #todo get rid of this; with networkx we disallow circulars
        self._lifecycles = { #todo injecting internals is untested
            #todo we may wanna inject it by SimpleInstanceIndex/ContextfulInvoker too; besides, ConfigurableContext should inject smth else than this
            InstanceIndex: ValueLifecycle(self),
            Invoker: ValueLifecycle(ContextfulInvoker(self))
        }
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
            # order = list(self.index.order(self.cyclic_resolver)) #todo
            order = list(self.index.order())
            log.info("Lifecycle ordering:")
            for i, t in enumerate(order):
                log.info(f"{i}: {t}")
            for t in order:
                lifecycle = self._make_lifecycle(t)
                lifecycles.append(lifecycle)
                self._lifecycles[t] = lifecycle
            with composite_lifecycle(lifecycles):
                yield
        finally:
            self._lifecycles.clear()

    def instance[T](self, t: type[T]) -> T:
        #todo test "no instance for the type" cases
        primary_type = self.index.primary_implementation(t)
        if primary_type is None:
            return None
        return self._lifecycles[primary_type].target

    def instances[T](self, t: type[T]) -> frozenset[T]:
        return frozenset(self._lifecycles[x].target for x in self.index.implementations(t))

    def _make_lifecycle[T: type](self, t: T) -> ObjectLifecycle[T]:
        try:
            instance = t()
        except:
            raise
        if issubclass(t, Injectable):
            return InitializableLifecycle(instance, lambda: self._inject_instance(t))
        if issubclass(t, HasLifecycle):
            return LifecycleDelegator(instance)
        return ValueLifecycle(instance)

    def resolve_requirement(self, t: type, kind: DependencyKind | KindDefinition):
        if isinstance(kind, DependencyKind):
            kind = kind.value
        details = ImplementationDetails(self.index.implementations(t), self.index.primary_implementation(t))
        chosen = kind.choose_injected_types(details)
        kind.validate_injected_types(chosen)
        instances = [
                self._lifecycles[i].target
                for i in chosen
            ]
        result = kind.as_injected_value(instances)
        return result

    def _inject_instance[T: type[Injectable]](self, t: T):
        instance: Injectable = self._lifecycles[t].target
        deps = self.index.dependencies(t)
        kwargs = {
            d.name: self.resolve_dependency(d)
            for d in deps
        }
        instance.inject_requirements(**kwargs)

    def type_index(self) -> TypeIndex:
        return self.index


class SimpleContext(TypeRegistryDelegateMixin, ApplicationContext[SimpleInstanceIndex]):
    def __init__(self, typeset: AnyTypeSet = None, cyclic_resolver: TypeComparator = None):
        self.registry: CustomizableTypeRegistry = SimpleRegistry(typeset or [])
        self._cyclic_resolver = cyclic_resolver

    def lifecycle(self) -> SimpleInstanceIndex:
        out = SimpleInstanceIndex(self.registry.type_index(), self._cyclic_resolver)
        return out

    def remove(self, *t: Collectable[type]):
        self.registry.remove(*t)

    def clone(self) -> Self:
        out = SimpleContext()
        out.registry = self.registry.clone()
        resolver = self._cyclic_resolver.clone() if isinstance(self._cyclic_resolver, Cloneable) else self._cyclic_resolver
        out._cyclic_resolver = resolver
        return out
