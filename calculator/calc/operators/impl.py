from calc.operators.protocol import BinaryOperator

from thinking_injection.discovery import discover
from thinking_injection.injectable import Injectable


@discover
class Adding:
    def on(self, val1: float, val2: float) -> float:
        return val1 + val2

    def text(self):
        return "+"

@discover
class Multiplying:
    def on(self, val1: float, val2: float) -> float:
        return val1 * val2

    def text(self):
        return "*"

@discover
class Subtracting(Injectable):
    def __init__(self):
        self.adding: BinaryOperator = None
        self.multiplying: BinaryOperator = None

    def inject_requirements(self, add: Adding, mult: Multiplying) -> None:
        self.adding = add
        self.multiplying = mult

    def on(self, val1: float, val2: float) -> float:
        return self.adding.on(val1, self.multiplying.on(val2, -1))

    def text(self):
        return "-"

@discover
class Dividing:
    def on(self, val1: float, val2: float) -> float:
        return val1/val2

    def text(self):
        return "/"