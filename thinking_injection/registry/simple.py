from collections import defaultdict
from dataclasses import dataclass, field
from functools import cache
from typing import NamedTuple, Optional, Self, Callable, Iterable

from frozendict import frozendict

from thinking_injection.common.dependencies import Dependencies, DependencyKind, get_dependencies, Dependency
from thinking_injection.discovery import PrimaryImplementation
from thinking_injection.interfaces import ConcreteType, is_concrete
from thinking_injection.common.implementations import ImplementationDetails
from thinking_injection.lifecycle import snapshot_as_lifecycle
from thinking_injection.ordering import TypeComparator
from thinking_injection.registry.protocol import TypeIndex, Implementations, Prerequisites, DiscoveredTypes, \
    TypeIndexMixin, TypeRegistry
from thinking_injection.typeset import ImmutableTypeSet
from thinking_programming.collectable import Collectable, collect




class TypeDescriptor(NamedTuple):
    dependencies: Dependencies
    implementations: Implementations
    primary: Optional[ConcreteType]

    def without(self, ts: set[type]) -> Self:
        return TypeDescriptor(
            frozenset(x for x in self.dependencies if x not in ts),
            frozenset(x for x in self.implementations if x not in ts),
            self.primary if self.primary not in ts else None
        )


@dataclass
class MutableTypeDescriptor:
    dependencies: set[Dependency] = field(default_factory=set)
    implementations: set[ConcreteType] = field(default_factory=set)
    forced_primary: Optional[ConcreteType] = None

    def freeze(self, primary_provider: Callable[[], Optional[ConcreteType]]) -> TypeDescriptor:
        return TypeDescriptor(
            frozenset(self.dependencies),
            frozenset(self.implementations),
            self.forced_primary or primary_provider()
        )


class SimpleIndex(NamedTuple):
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
        requirements = set()
        if is_concrete(t):
            ds = self.dependencies(t)
            if ds is not None:
                for d in ds:
                    dep_type = d.type_
                    implementations = self.implementations(dep_type)
                    primary = self.primary_implementation(dep_type)
                    details = ImplementationDetails(implementations, primary)
                    dep_kind = d.kind.value
                    assert dep_kind.arity.matches(len(implementations))  # todo msg; fixme should actually check if primary is set or not too
                    impl = dep_kind.choose_implementations(details)
                    if d.kind == DependencyKind.COLLECTIVE:  # todo this should be externalized to kind too
                        requirements.update(impl)
                    # this and following could be simplified, but this is more descriptive
                    elif d.kind == DependencyKind.OPTIONAL:
                        if impl is not None:
                            requirements.add(impl)
                    else:
                        requirements.add(impl)
        for r in requirements:
            assert is_concrete(r)  # todo
        return frozenset(requirements)

    def known_types(self) -> ImmutableTypeSet:
        return frozenset(self.data.keys())

    def without(self, *t: Collectable[type]) -> Self:
        ts = set(collect(type, *t))
        return SimpleIndex(
            frozendict({
                k: v.without(ts)
                for k, v in self.data.items()
                if k not in ts
            })
        )
    #
    # known_concrete_types = TypeIndexMixin.known_concrete_types
    # least_requiring = TypeIndexMixin.least_requiring
    # order = TypeIndexMixin.order

    def known_concrete_types(self) -> frozenset[ConcreteType]:
        return TypeIndexMixin.known_concrete_types(self)

    def least_requiring(self) -> frozenset[ConcreteType]:
        return TypeIndexMixin.least_requiring(self)

    def order(self, cyclic_resolver: TypeComparator = None) -> Iterable[ConcreteType]:
        return TypeIndexMixin.order(self, cyclic_resolver)

    @classmethod
    def build(cls, d: dict[type, TypeDescriptor] = None) -> Self:
        d = d or {}
        return SimpleIndex(frozendict(d))


assert issubclass(SimpleIndex, TypeIndex)


@snapshot_as_lifecycle
class SimpleRegistry(NamedTuple):
    data: dict[type, MutableTypeDescriptor]

    @classmethod
    def make(cls, *t: Collectable[type]) -> Self:
        return SimpleRegistry(defaultdict(MutableTypeDescriptor)).with_registered(*t)

    def with_registered(self, *t: Collectable[type]) -> Self:
        self.register(*t)
        return self

    def register(self, *t: Collectable[type]) -> DiscoveredTypes:
        out = set()
        def scan(x: type):
            if x not in self.data:
                out.add(x)
                desc = self.data[x]
                if is_concrete(x):
                    desc.implementations.add(x)
                deps = get_dependencies(x)
                desc.dependencies = deps
                for d in deps:
                    if d.kind != DependencyKind.OPTIONAL:
                        scan(d.type_)

        for x in collect(type, *t):
            scan(x)
        for newly_scanned in out:
            for already_scanned in self.data:
                if already_scanned != newly_scanned:
                    if is_concrete(newly_scanned) and issubclass(newly_scanned, already_scanned):
                        self.data[already_scanned].implementations.add(newly_scanned)
                    if is_concrete(already_scanned) and issubclass(already_scanned, newly_scanned):
                        self.data[newly_scanned].implementations.add(already_scanned)
        return frozenset(out)

    def known_types(self) -> ImmutableTypeSet:
        return frozenset(self.data.keys())

    def _figure_out_primary(self, t: type) -> Optional[ConcreteType]:
        assert t in self.data  # todo msg
        # if t in self.forced[t]:
        #     return self.forced[t]
        impls = self.data[t].implementations
        hint = PrimaryImplementation(t).get()
        if hint is not None:
            if hint in impls:
                return hint
        if len(impls) == 1:
            return list(impls)[0]
        if is_concrete(t):
            assert t in impls  # todo msg
            return t
        # if t in self.defaults:
        #     return self.defaults[t]
        return None

    def snapshot(self) -> TypeIndex:
        return SimpleIndex(frozendict({
            t: desc.freeze(lambda: self._figure_out_primary(t))
            for t, desc in self.data.items()
        }))


assert issubclass(SimpleRegistry, TypeRegistry)