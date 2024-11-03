from typing import Protocol, runtime_checkable

from thinking_injection.registry.customizable.customizer import TypeRegistryCustomizer
from thinking_injection.registry.protocol import TypeRegistry


@runtime_checkable
class CustomizableTypeRegistry(TypeRegistry, Protocol):
    def customizer(self) -> TypeRegistryCustomizer: pass