from abc import abstractmethod
from typing import Protocol, runtime_checkable

from thinking_injection.lifecycle import Initializable
from thinking_reflection.discovery import discover


@runtime_checkable
class Injectable(Initializable, Protocol):

    @abstractmethod
    def inject_requirements[T](self, **dependencies: T) -> None: pass #todo -> inject(**)

    def __init_subclass__(cls, **kwargs):
        discover(cls)


InjectableType = type[Injectable]
