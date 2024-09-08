from abc import abstractmethod
from typing import Protocol

from thinking_injection.interfaces import interface


@interface
class BinaryOperator(Protocol):
    @abstractmethod
    def on(self, val1: float, val2: float) -> float: pass

    @abstractmethod
    def text(self) -> str: pass
