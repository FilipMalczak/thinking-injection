from typing import Protocol, Optional, runtime_checkable, ContextManager

from thinking_injection.lifecycle import HasLifecycle
from thinking_injection.registry.protocol import TypeRegistry


@runtime_checkable
class InstanceIndex(ContextManager, Protocol):
    def instance[T](self, t: type[T]) -> Optional[T]: pass

    def instances[T](self, t: type[T]) -> frozenset[T]: pass


@runtime_checkable
class ApplicationContext[ContextLifetime: InstanceIndex](TypeRegistry, HasLifecycle[ContextLifetime], Protocol): pass
