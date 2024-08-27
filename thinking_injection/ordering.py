from typing import Callable, NamedTuple, Self

from thinking_injection.interfaces import ConcreteType

TypeComparator = Callable[[ConcreteType, ConcreteType], int]

class TypeOrder(NamedTuple):
    before: ConcreteType
    after: ConcreteType

class CyclicResolver:
    def __init__(self):
        self.rules = set()

    def left_before_right(self, t1: ConcreteType, t2: ConcreteType) -> Self:
        self.rules.add(TypeOrder(t1, t2))
        return self

    def right_before_left(self, t1: ConcreteType, t2: ConcreteType) -> Self:
        return self.left_before_right(t2, t1)

    def __call__(self, t1: ConcreteType, t2: ConcreteType) -> int:
        if TypeOrder(t1, t2) in self.rules:
            return -1
        elif TypeOrder(t2, t1) in self.rules:
            return 1
        else:
            assert False, f"Cannot resolve order, add a rule for {t1} and {t2}" #todo better msg

Requires = Callable[[ConcreteType, ConcreteType], bool]

def requirement_comparator(requires: Requires, cyclic_resolver: TypeComparator) -> TypeComparator:
    def comparator(t1: ConcreteType, t2: ConcreteType) -> int:
        if requires(t1, t2):
            if not requires(t2, t1):
                # t1 should be initialized later than t2
                return 1
            else:
                # cyclic dependency
                return cyclic_resolver(t1, t2)
        else:
            if requires(t2, t1):
                # t2 should be initialized later than t1
                return -1
            else:
                # no dependency between types, order doesn't matter
                # there's no way names are the same, so no 0 case
                return -1 if t1.__name__ < t2.__name__ else 1
    return comparator