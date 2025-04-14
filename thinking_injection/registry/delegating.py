from typing import Optional, Iterable, Self

from pydot import Dot, Cluster

from thinking_injection.common.dependencies import Dependencies
from thinking_injection.ordering import TypeComparator
from thinking_injection.registry.protocol import TypeRegistry, DiscoveredTypes, TypeIndex, Implementations, \
    Prerequisites, GraphEdge
from thinking_injection.typeset import ImmutableTypeSet
from thinking_programming.collectable import Collectable
from thinking_programming.exceptions import UnreachableInstructionException
from thinking_reflection.interfaces import ConcreteType, is_concrete


class TypeRegistryDelegateMixin:
    registry: TypeRegistry

    def register(self, *t: Collectable[type]) -> DiscoveredTypes:
        result = self.registry.register(*t)
        return result

    def remove(self, *t: Collectable[type]):
        self.registry.remove(*t)

    def known_types(self) -> ImmutableTypeSet:
        return self.registry.known_types()

    def type_index(self) -> TypeIndex:
        return self.registry.type_index()


class TypeIndexUnion(TypeIndex):
    """
    This represents an union of indexes that refer to disjoint typesets. The indexes are browsed (and ordered)
    in the order passed to constructor.
    """
    def __init__(self, indexes: Iterable[TypeIndex], names: Iterable[str] = None):
        self.indexes: tuple[TypeIndex, ...] = tuple(indexes)
        self.names: tuple[str, ...] = tuple(names) or tuple()

    def dependencies[T: type](self, t: T) -> Dependencies:
        for i in self.indexes:
            deps = i.dependencies(t)
            if deps:
                return deps
        return frozenset([])

    def implementations[T: type](self, t: T) -> Implementations:
        for i in self.indexes:
            impls = i.implementations(t)
            if impls:
                return impls
        return frozenset([])

    def primary_implementation[T: type](self, t: T) -> Optional[ConcreteType]:
        for i in self.indexes:
            primary = i.primary_implementation(t)
            if primary:
                return primary

    def prerequisites[T: type](self, t: T) -> Prerequisites:
        for i in self.indexes:
            try:
                return i.prerequisites(t)
            except AssertionError: #fixme this will be dedicated exception at some point
                pass
        UnreachableInstructionException.guard()

    def known_types(self) -> ImmutableTypeSet:
        return frozenset([
            t
            for i in self.indexes
            for t in i.known_types()
        ])

    def known_concrete_types(self) -> frozenset[ConcreteType]:
        return frozenset([t for t in self.known_types() if is_concrete(t)])

    def least_requiring(self) -> frozenset[ConcreteType]:
        return frozenset([
            t
            for i in self.indexes
            for t in i.least_requiring()
        ])

    def without(self, *t: Collectable[type]) -> Self:
        return TypeIndexUnion([i.without(*t) for i in self.indexes])

    def order(self, cyclic_resolver: TypeComparator = None) -> Iterable[ConcreteType]:
        for i in self.indexes:
            yield from i.order(cyclic_resolver)

    def graph(self, name: str = "index", edges: set[GraphEdge] = None, colors: dict[str, str]=None) -> Dot:
        result = Dot(graph_name=name, suppress_disconnected=True)
        for i, sub in enumerate(self.indexes):
            name = self.names[i] if i < len(self.names) else f"subindex{i}"
            index_graph = sub.graph(edges=edges, colors=colors)
            subgraph = Cluster(graph_name=name, suppress_disconnected=True, label=name, style="dotted")
            for n in index_graph.get_nodes():
                subgraph.add_node(n)
            for e in index_graph.get_edges():
                subgraph.add_edge(e)
            result.add_subgraph(subgraph)
        return result
