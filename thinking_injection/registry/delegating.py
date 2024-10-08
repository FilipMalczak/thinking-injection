from thinking_injection.registry.protocol import TypeRegistry, DiscoveredTypes, TypeIndex
from thinking_injection.typeset import ImmutableTypeSet
from thinking_programming.collectable import Collectable


class TypeRegistryDelegateMixin:
    registry: TypeRegistry

    def register(self, *t: Collectable[type]) -> DiscoveredTypes:
        return self.registry.register(*t)

    @property
    def known_types(self) -> ImmutableTypeSet:
        return self.registry.known_types

    def snapshot(self) -> TypeIndex:
        return self.registry.snapshot()