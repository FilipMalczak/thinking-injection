from abc import abstractmethod
from typing import Protocol

from calc.operators.protocol import BinaryOperator
from thinking_injection.interfaces import interface


@interface
class ExpressionNode(Protocol):
    @abstractmethod
    def evaluate(self) -> float: pass


class ValueNode(ExpressionNode):
    def __init__(self, val: float):
        self.val = val

    def evaluate(self) -> float:
        return self.val

    def __str__(self):
        return f"Value({self.val})"

@interface
class OperatorNode[Op: BinaryOperator](ExpressionNode):
    def __init__(self, executor: Op, l: ExpressionNode, r: ExpressionNode):
        self.executor = executor
        self.l = l
        self.r = r

    def evaluate(self) -> float:
        return self.executor.on(self.l.evaluate(), self.r.evaluate())

    def __str__(self):
        return f"({self.l} {self.executor.text()} {self.r})"

