from contextlib import contextmanager
from enum import Enum
from functools import cmp_to_key
from logging import getLogger
from typing import Protocol, runtime_checkable, Optional, Self, Iterable

from pydot import Dot

from thinking_injection.cloneable import Cloneable
from thinking_injection.common.dependencies import Dependencies
from thinking_injection.common.index import TypeIndex
from thinking_injection.lifecycle import HasLifecycle
from thinking_injection.ordering import TypeComparator, requirement_comparator, CyclicResolver
from thinking_injection.typeset import ImmutableTypeSet
from thinking_programming.collectable import Collectable
from thinking_reflection.interfaces import ConcreteType, is_concrete


log = getLogger(__name__)


DiscoveredTypes = ImmutableTypeSet
Implementations = frozenset[ConcreteType]
Prerequisites = frozenset[ConcreteType]

#fixme I think its unused
def requires(idx: TypeIndex, depending: ConcreteType, dependency: ConcreteType) -> bool:
    return dependency in idx.prerequisites(depending)


#fixme this mixin became aenemic
class TypeIndexMixin:
    def known_concrete_types(self) -> frozenset[ConcreteType]:
        return frozenset(t for t in self.known_types() if is_concrete(t))


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

#todo cleanup
    # def least_requiring(self) -> frozenset[ConcreteType]: pass

    def without(self, *t: Collectable[type]) -> Self: pass

    # def order(self, cyclic_resolver: TypeComparator = None) -> Iterable[ConcreteType]: pass
    def order(self) -> Iterable[ConcreteType]: pass

    # todo untested
    def graph(self, name: str = "index", edges: set[GraphEdge] = None, colors: dict[str, str]=None) -> Dot: pass


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
