from functools import cmp_to_key
from typing import Protocol, runtime_checkable, Optional, Self, Iterable, NamedTuple

from thinking_injection.common.dependencies import Dependencies
from thinking_injection.interfaces import ConcreteType, is_concrete
from thinking_injection.lifecycle import HasLifecycle
from thinking_injection.ordering import TypeComparator, requirement_comparator, CyclicResolver
from thinking_injection.typeset import ImmutableTypeSet
from thinking_programming.collectable import Collectable

DiscoveredTypes = ImmutableTypeSet
Implementations = frozenset[ConcreteType]
Prerequisites = frozenset[ConcreteType]



class TypeIndexMixin:
    def known_concrete_types(self) -> frozenset[ConcreteType]:
        return frozenset(t for t in self.known_types() if is_concrete(t))

    def least_requiring(self) -> frozenset[ConcreteType]:
        counts = {
            t: len(self.prerequisites(t))
            for t in self.known_concrete_types()
        }
        min_count = min(counts.values())
        return frozenset(k for k in counts.keys() if counts[k] == min_count)

    def order(self, cyclic_resolver: TypeComparator = None) -> Iterable[ConcreteType]:
        comparator = requirement_comparator(self.requires, cyclic_resolver or CyclicResolver())
        key_foo = cmp_to_key(comparator)
        if self.known_types():
            least_dependent = self.least_requiring()
            order = sorted(least_dependent, key=key_foo)
            for x in order:
                yield x
            remainder = self.without(least_dependent)
            yield from remainder.order(cyclic_resolver)



@runtime_checkable
class TypeIndex(Protocol):

    def dependencies[T: type](self, t: T) -> Dependencies: pass

    def implementations[T: type](self, t: T) -> Implementations: pass

    def primary_implementation[T: type](self, t: T) -> Optional[ConcreteType]: pass

    def prerequisites[T: type](self, t: T) -> Prerequisites: pass

    def known_types(self) -> ImmutableTypeSet: pass

    def known_concrete_types(self) -> frozenset[ConcreteType]: pass

    def least_requiring(self) -> frozenset[ConcreteType]: pass

    def without(self, *t: Collectable[type]) -> Self: pass

    def order(self, cyclic_resolver: TypeComparator = None) -> Iterable[ConcreteType]: pass



@runtime_checkable
class TypeRegistry(HasLifecycle, Protocol):
    def register(self, *t: Collectable[type]) -> DiscoveredTypes: pass

    def known_types(self) -> ImmutableTypeSet: pass

    def snapshot(self) -> TypeIndex: pass