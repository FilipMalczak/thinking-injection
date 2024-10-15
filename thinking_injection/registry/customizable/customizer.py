from typing import runtime_checkable, Protocol, Optional

from thinking_injection.interfaces import is_concrete
from thinking_injection.registry.protocol import DiscoveredTypes

from thinking_programming.collectable import Collectable


@runtime_checkable
class TypeImplementationsCustomizer(Protocol):
    @property
    def all(self) -> frozenset[type]: pass

    @property
    def primary(self) -> Optional[type]: pass

    @primary.setter
    def primary(self, t: type) -> None: pass


@runtime_checkable
class ImplementationsCustomizer(Protocol):
    def of(self, t: type) -> TypeImplementationsCustomizer:
        """
        Should raise UnknownTypeException
        """

    __getitem__ = of


@runtime_checkable
class TypeRegistryCustomizer(Protocol):
    def known_types(self) -> frozenset[type]: pass

    def known_concrete_types(self) -> frozenset[type]:
        return frozenset([x for x in self.known_types() if is_concrete(x)])

    def register(self, *t: Collectable[type]) -> DiscoveredTypes: pass

    def unregister(self, *t: Collectable[type]): pass

    @property
    def implementations(self) -> ImplementationsCustomizer: pass
