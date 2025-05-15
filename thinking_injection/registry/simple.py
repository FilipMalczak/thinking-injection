from collections import defaultdict
from dataclasses import dataclass, field
from functools import cache
from logging import getLogger
from typing import NamedTuple, Optional, Self, Callable, Iterable, Any

from frozendict import frozendict
from networkx.algorithms.cycles import simple_cycles
from networkx.algorithms.dag import topological_sort, lexicographical_topological_sort
from networkx.classes import DiGraph
from networkx.exception import NetworkXUnfeasible
from pydot import Dot, Node, Edge

from thinking_injection.cloneable import Cloneable
from thinking_injection.common.dependencies import Dependencies, DependencyKind, get_type_dependencies, Dependency
from thinking_injection.common.exceptions import UnknownTypesException, UnknownTypeException
from thinking_injection.common.implementations import ImplementationDetails
from thinking_injection.exceptions import ConcreteTypeExpectedException, InvalidInternalTypeException, \
    InvalidThinkingStateException
from thinking_injection.ordering import TypeComparator
from thinking_injection.registry.customizable.customizer import TypeRegistryCustomizer, ImplementationsCustomizer, \
    TypeImplementationsCustomizer
from thinking_injection.registry.customizable.protocol import CustomizableTypeRegistry
from thinking_injection.registry.protocol import TypeIndex, Implementations, Prerequisites, DiscoveredTypes, \
    TypeIndexMixin, GraphEdge
from thinking_injection.typeset import ImmutableTypeSet
from thinking_programming.collectable import Collectable, collect
from thinking_reflection.discovery import PrimaryImplementation
from thinking_reflection.interfaces import ConcreteType, is_concrete

log = getLogger(__name__)

class TypeDescriptor(NamedTuple):
    dependencies: Dependencies
    implementations: Implementations
    primary: Optional[ConcreteType]

    def without(self, ts: set[type]) -> Self:
        p = self.primary if self.primary not in ts else None
        # log.info(f"Pre {self}")
        out = TypeDescriptor(
            frozenset(x for x in self.dependencies if x.type_ not in ts),
            frozenset(x for x in self.implementations if x not in ts),
            p
        )
        return out


@dataclass
class MutableTypeDescriptor(Cloneable):
    dependencies: set[Dependency] = field(default_factory=set)
    implementations: set[ConcreteType] = field(default_factory=set)
    forced_primary: Optional[ConcreteType] = None

    def freeze(self, primary_provider: Callable[[], Optional[ConcreteType]]) -> TypeDescriptor:
        return TypeDescriptor(
            frozenset(self.dependencies),
            frozenset(self.implementations),
            self.forced_primary or primary_provider()
        )

    def clone(self) -> Self:
        return MutableTypeDescriptor(set(self.dependencies), set(self.implementations), self.forced_primary)

class CyclicDependencyGraphException(InvalidThinkingStateException):
    def __init__(self, cycles: list[list[type]], dot: str):
        self.cycles = cycles
        self.dot = dot
        msg = [ "Dependency graph contains following cycles:" ]
        for c in cycles:
            msg.append(
                f"\t{', '.join(map(str, c))}"
            )
        msg.append("")
        msg.append("DOT for current index:")
        msg.append(dot)
        InvalidThinkingStateException.__init__(self, "\n".join(msg))

class SimpleTypeIndex(NamedTuple):
    data: frozendict[type, TypeDescriptor]

    def dependencies[T: type](self, t: T) -> Dependencies:
        if t not in self.data:
            return frozenset()
        return self.data[t].dependencies

    def implementations[T: type](self, t: T) -> Implementations:
        if t not in self.data:
            return frozenset()
        return self.data[t].implementations

    def primary_implementation[T: type](self, t: T) -> Optional[ConcreteType]:
        if t not in self.data:
            return None
        return self.data[t].primary

    @cache
    def prerequisites[T: type](self, t: T) -> Prerequisites:
        #fixme these exceptions can bubble up in thinking_injection/registry/delegating.py:65
        log.debug(f"Looking for prerequisites of {t}")
        requirements: set[Any] = set()
        if is_concrete(t):
            log.debug("Type is concrete, lets go forth")
            ds = self.dependencies(t)
            log.debug(f"Its dependencies: {ds}")
            if ds is not None:
                for d in ds:
                    log.debug(f"\tLooking into dep {d}")
                    dep_type = d.type_
                    implementations = self.implementations(dep_type)
                    log.debug(f"\tImpls: {implementations}")
                    primary = self.primary_implementation(dep_type)
                    log.debug(f"Primary: {primary}")
                    details = ImplementationDetails(implementations, primary)
                    dep_kind = d.kind.value
                    prereqs = dep_kind.choose_injected_types(details)
                    dep_kind.validate_injected_types(dep_type, prereqs)
                    requirements.update(prereqs)
        for r in requirements:
            ConcreteTypeExpectedException.guard(r)
        return frozenset(requirements)

    def known_types(self) -> ImmutableTypeSet:
        return frozenset(self.data.keys())

    def without(self, *t: Collectable[type]) -> Self:
        ts = set(collect(type, *t))
        out =  SimpleTypeIndex(
            frozendict({
                k: v.without(ts)
                for k, v in self.data.items()
                if k not in ts
            })
        )
        return out

    def known_concrete_types(self) -> frozenset[ConcreteType]:
        return TypeIndexMixin.known_concrete_types(self)

    def order(self) -> Iterable[ConcreteType]:
        # edge X -> Y means "Y requires X" - the direction is reversed, because we want topological sort result to start with no-dependency types
        graph = DiGraph()
        current_idx = 0
        type_to_idx: dict[ConcreteType, int] = {}
        idx_to_type: list[ConcreteType] = []
        # this can probably be done in a single loop, but let's optimize later
        #todo optimize
        for t in self.known_types():
            type_to_idx[t] = current_idx
            assert len(idx_to_type) == current_idx
            idx_to_type.append(t)
            graph.add_node(current_idx)
            current_idx += 1
        for t in self.known_concrete_types():
            for prerequisite in self.prerequisites(t):
                try:
                    graph.add_edge(type_to_idx[prerequisite], type_to_idx[t])
                except:
                    raise
        try:
            for i in lexicographical_topological_sort(graph, key=lambda i: idx_to_type[i].__name__):
                t = idx_to_type[i]
                if is_concrete(t):
                    yield t
        except NetworkXUnfeasible:
            cycles = simple_cycles(graph)
            cycle_strs = [ [idx_to_type[n] for n in c] for c in cycles]
            colored = set()
            colored.update(*cycle_strs)
            raise CyclicDependencyGraphException(
                cycle_strs,
                self.graph(edges={GraphEdge.REQUIRES}, colors={k: "red" for k in colored}).to_string()
            )

    @classmethod
    def build(cls, d: dict[type, TypeDescriptor] = None) -> Self:
        d = d or {}
        log.info(f"Building TypeIndex {d}")
        return SimpleTypeIndex(frozendict(d))

    def graph(self, name: str = "index", edges: set[GraphEdge] = None, colors: dict[str, str]=None) -> Dot:
        edges = edges or set(GraphEdge)
        colors = colors or dict()
        result = Dot(graph_name=name, graph_type="digraph", suppress_disconnected=True)
        for k in self.data.keys():
            kwargs = {
                "shape": "box" if is_concrete(k) else "diamond"
            }
            if k in colors:
                kwargs["color"] = colors[k]
            result.add_node(Node(k.__name__, **kwargs))
        def _coloring(x, y):
            if x in colors and y in colors:
                return {"color": f"{colors[x]}:{colors[y]}"}
            return {}
        for k in self.data.keys():
            if GraphEdge.IMPLEMENTS in edges:
                primary = self.primary_implementation(k)
                for i in self.implementations(k):
                    result.add_edge(
                        Edge(
                            i.__name__, k.__name__,
                            style="bold" if i == primary else "solid",
                            label=GraphEdge.IMPLEMENTS.value,
                            arrowhead="empty",
                            **_coloring(i, k)
                        )
                    )
            if GraphEdge.DEPENDS_ON in edges:
                for d in self.dependencies(k):
                    result.add_edge(
                        Edge(
                            k.__name__, d.type_.__name__,
                            label=GraphEdge.DEPENDS_ON.value,
                            arrowhead="open",
                            headlabel="?" if d.kind == DependencyKind.OPTIONAL else ("*" if d.kind == DependencyKind.COLLECTIVE else ""),
                            **_coloring(k, d)
                        )
                    )
            if GraphEdge.REQUIRES in edges:
                for r in self.prerequisites(k):
                    result.add_edge(
                        Edge(
                            k.__name__, r.__name__,
                            label=GraphEdge.REQUIRES.value,
                            style="dashed",
                            arrowhead="open",
                            **_coloring(k, r)
                        )
                    )
        return result


InvalidInternalTypeException.guard(SimpleTypeIndex, TypeIndex)


class SimpleTypeImplementationsCustomizer(TypeImplementationsCustomizer):
    def __init__(self, descriptor: MutableTypeDescriptor, primary_provider: Callable[[], Optional[ConcreteType]]):
        self._descriptor = descriptor
        self._primary_provider = primary_provider

    @property
    def all(self) -> frozenset[type]:
        return frozenset(self._descriptor.implementations)

    @property
    def primary(self) -> Optional[type]:
        return self._descriptor.forced_primary or self._primary_provider()

    @primary.setter
    def primary(self, t: type) -> None:
        #todo check invariants, like t implements this type or at least is concrete?
        self._descriptor.forced_primary = t

    def __str__(self):
        return f"{type(self).__name__}(all={self.all}, forcedPrimary={self._descriptor.forced_primary}, effectivePrimary={self.primary})"

    __repr__ = __str__

class SimpleImplementationsCustomizer(ImplementationsCustomizer):
    def __init__(self, registry: 'SimpleRegistry'):
        self._registry = registry

    def of(self, t: type) -> TypeImplementationsCustomizer:
        if t not in self._registry.known_types():
            raise UnknownTypeException("Cannot customize implementations because type is not registered", t)
        return SimpleTypeImplementationsCustomizer(self._registry.data[t], lambda: self._registry._figure_out_primary(t))


class SimpleTypeRegistryCustomizer(TypeRegistryCustomizer):
    def __init__(self, registry: 'SimpleRegistry'):
        self._registry = registry

    def known_types(self) -> frozenset[type]:
        return self._registry.known_types()

    def register(self, *t: Collectable[type]) -> DiscoveredTypes:
        return self._registry.register(*t)

    def unregister(self, *t: Collectable[type]):
        return self._registry.remove(*t)

    @property
    def implementations(self) -> ImplementationsCustomizer:
        return SimpleImplementationsCustomizer(self._registry)


class SimpleRegistry(CustomizableTypeRegistry):
    def __init__(self, *t: Collectable[type]):
        self.data = defaultdict(MutableTypeDescriptor)
        self.register(*t)

    def register(self, *t: Collectable[type]) -> DiscoveredTypes:
        out = set()

        def scan(x: type):
            if x not in self.data:
                out.add(x)
                desc = self.data[x]
                if is_concrete(x):
                    desc.implementations.add(x)
                deps = get_type_dependencies(x)
                desc.dependencies = deps
                for d in deps:
                    if d.kind != DependencyKind.OPTIONAL:
                        scan(d.type_)

        for x in collect(type, *t):
            scan(x)
        for newly_scanned in out:
            for already_scanned in self.data:
                if already_scanned != newly_scanned:
                    try:
                        if is_concrete(newly_scanned) and issubclass(newly_scanned, already_scanned):
                            self.data[already_scanned].implementations.add(newly_scanned)
                        if is_concrete(already_scanned) and issubclass(already_scanned, newly_scanned):
                            self.data[newly_scanned].implementations.add(already_scanned)
                    except:
                        raise
        return frozenset(out)

    def remove(self, *t: Collectable[type]):
        unknowns = []
        for x in collect(type, *t):
            if x in self.data:
                del self.data[x]
            else:
                unknowns.append(x)
            for v in self.data.values():
                v.dependencies = {d for d in v.dependencies if d.type_ != x}
                v.implementations.discard(x)
                if v.forced_primary == x:
                    v.forced_primary = None
        #todo replace the following with the warning
        # if unknowns:
        #     #todo UnknownTypesException.guard(unknowns)
        #     raise UnknownTypesException("Cannot remove unknown types from type registry", unknowns)

    def known_types(self) -> ImmutableTypeSet:
        return frozenset(self.data.keys())

    def _figure_out_primary(self, t: type) -> Optional[ConcreteType]:
        log.debug(f"No forced implementation for {t}, figuring primary out")
        assert t in self.data  # todo msg
        # if t in self.forced[t]:
        #     return self.forced[t]
        impls = self.data[t].implementations
        hint = PrimaryImplementation(t).get()
        log.debug(f"Implementations: {impls}")
        log.debug(f"Hint: {hint}")
        if hint is not None:
            if hint in impls:
                log.debug(f"Returning hint {hint}")
                return hint
        if len(impls) == 1:
            return list(impls)[0]
        if is_concrete(t):
            assert t in impls  # todo msg
            log.debug(f"Returning sole implementation {t}")
            return t
        # if t in self.defaults:
        #     return self.defaults[t]
        log.debug("No other option, returning None")
        return None

    def type_index(self) -> TypeIndex:
        log.debug("TypeRegistry to TypeIndex")
        log.debug(f"Registry {self.data}")
        out = SimpleTypeIndex(frozendict({
            t: desc.freeze(lambda: self._figure_out_primary(t))
            for t, desc in self.data.items()
        }))
        log.debug(f"Index {out.data}")
        return out

    def customizer(self) -> TypeRegistryCustomizer:
        return SimpleTypeRegistryCustomizer(self)

    def clone(self) -> Self:
        return SimpleRegistry({k: v.clone() for k, v in self.data.items()})


InvalidInternalTypeException.guard(SimpleRegistry, CustomizableTypeRegistry)
