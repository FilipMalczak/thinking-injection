from typing import Protocol, Optional, runtime_checkable, ContextManager, Self

from thinking_injection.cloneable import Cloneable
from thinking_injection.lifecycle import HasLifecycle
from thinking_injection.registry.protocol import TypeRegistry, TypeIndex

from thinking_programming.collectable import Collectable

@runtime_checkable
class InstanceIndex(ContextManager, Protocol):
    def instance[T](self, t: type[T]) -> Optional[T]: pass

    def instances[T](self, t: type[T]) -> frozenset[T]: pass



@runtime_checkable
class ApplicationContext[ContextLifetime: InstanceIndex](TypeRegistry,
                                                         HasLifecycle[ContextLifetime],
                                                         Cloneable,
                                                         Protocol):
    def remove(self, *t: Collectable[type]):
        '''raises UnknownTypesException'''
