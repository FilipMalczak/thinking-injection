from typing import Protocol, Optional, runtime_checkable, ContextManager, Any

from thinking_injection.cloneable import Cloneable
from thinking_injection.common.dependencies import DependencyKind, Dependency, KindDefinition
from thinking_injection.lifecycle import HasLifecycle
from thinking_injection.registry.protocol import TypeRegistry, TypeIndex
from thinking_programming.collectable import Collectable
from thinking_reflection.interfaces import interface


@interface
class InstanceIndex(ContextManager, Protocol):
    def instance[T](self, t: type[T]) -> Optional[T]: ...

    def instances[T](self, t: type[T]) -> frozenset[T]: ...

    def type_index(self) -> TypeIndex: ...

    def resolve_requirement(self, t: type, kind: DependencyKind | KindDefinition) -> Any: ...

    def resolve_dependency(self, d: Dependency) -> Any:
        return self.resolve_requirement(d.type_, d.kind)

@interface
class ApplicationContext[ContextLifetime: InstanceIndex](TypeRegistry,
                                                         HasLifecycle[ContextLifetime],
                                                         Cloneable,
                                                         Protocol):
    def remove(self, *t: Collectable[type]):
        '''raises UnknownTypesException''' #todo fix this docstring
