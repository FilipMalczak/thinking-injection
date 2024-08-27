from abc import ABC, abstractmethod
from logging import getLogger
from typing import Protocol, runtime_checkable

from thinking_injection.discovery import discover
from thinking_injection.lifecycle import Initializable

log = getLogger(__name__)

@runtime_checkable
class Injectable(Initializable, Protocol):

    @abstractmethod
    def inject_requirements(self, **dependencies: type) -> None: pass #todo -> inject(**)

    def __init_subclass__(cls, **kwargs):
        discover(cls)

InjectableType = type[Injectable]
