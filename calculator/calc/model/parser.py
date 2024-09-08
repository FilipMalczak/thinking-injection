from typing import Iterable

from calc.model.node import ExpressionNode, OperatorNode, ValueNode
from calc.operators.protocol import BinaryOperator
from thinking_injection.injectable import Injectable


class RPNParser(Injectable):
    def __init__(self):
        self.operators: list[BinaryOperator] = None

    def inject_requirements(self, operators: list[BinaryOperator]) -> None:
        self.operators = operators

    def parse(self, symbols: Iterable[str]) -> ExpressionNode:
        stack = []
        for s in symbols:
            is_operator = False
            for o in self.operators:
                if o.text() == s:
                    r = stack[-1]
                    l = stack[-2]
                    stack = stack[:-2]
                    new = OperatorNode(o, l, r)
                    stack.append(new)
                    is_operator = True
                    break
            if not is_operator:
                stack.append(ValueNode(float(s)))
        #todo handle malformed input
        assert len(stack) == 1
        return stack[0]