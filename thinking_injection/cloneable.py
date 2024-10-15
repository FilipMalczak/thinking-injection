from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class Cloneable(Protocol):
    def clone(self) -> Self: pass