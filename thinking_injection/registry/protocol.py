from contextlib import contextmanager
from enum import Enum
from functools import cmp_to_key
from typing import Protocol, runtime_checkable, Optional, Self, Iterable

from pydot import Dot

from thinking_injection.cloneable import Cloneable
from thinking_injection.common.dependencies import Dependencies
from thinking_injection.common.index import TypeIndex
from thinking_types.interfaces import ConcreteType, is_concrete
from thinking_injection.lifecycle import HasLifecycle
from thinking_injection.ordering import TypeComparator, requirement_comparator, CyclicResolver
from thinking_injection.typeset import ImmutableTypeSet
from thinking_programming.collectable import Collectable

DiscoveredTypes = ImmutableTypeSet
Implementations = frozenset[ConcreteType]
Prerequisites = frozenset[ConcreteType]


def requires(idx: TypeIndex, depending: ConcreteType, dependency: ConcreteType) -> bool:
    return dependency in idx.prerequisites(depending)


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
        comparator = requirement_comparator(lambda x, y: requires(self, x, y), cyclic_resolver or CyclicResolver())
        key_foo = cmp_to_key(comparator)
        # if self.known_types(): #fixme or known_concrete_types?
        if self.known_concrete_types():
            least_dependent = self.least_requiring()
            order = sorted(least_dependent, key=key_foo)
            for x in order:
                yield x
            remainder = self.without(least_dependent)
            yield from remainder.order(cyclic_resolver)


#fixme not the best way, not the best placement
class GraphEdge(Enum):
    IMPLEMENTS = "implements"
    DEPENDS_ON = "depends on"
    REQUIRES = "requires"


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

    # todo untested
    def graph(self, name: str = "index", edges: set[GraphEdge] = None) -> Dot: pass


@runtime_checkable
class TypeRegistry(HasLifecycle, Cloneable, Protocol):
    def register(self, *t: Collectable[type]) -> DiscoveredTypes: pass

    def remove(self, *t: Collectable[type]):
        '''raises UnknownTypesException'''

    #todo make this a property across the implementations
    def known_types(self) -> ImmutableTypeSet: pass

    def type_index(self) -> TypeIndex: pass

    @contextmanager
    def lifecycle(self) -> TypeIndex:
        yield self.type_index()
