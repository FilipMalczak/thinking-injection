from collections import defaultdict
from dataclasses import dataclass, field
from functools import cache
from typing import NamedTuple, Optional, Self, Callable, Iterable

from frozendict import frozendict

from thinking_injection.cloneable import Cloneable
from thinking_injection.common.dependencies import Dependencies, DependencyKind, get_dependencies, Dependency
from thinking_injection.common.exceptions import UnknownTypesException, UnknownTypeException
from thinking_injection.discovery import PrimaryImplementation
from thinking_injection.interfaces import ConcreteType, is_concrete
from thinking_injection.common.implementations import ImplementationDetails
from thinking_injection.ordering import TypeComparator
from thinking_injection.registry.customizable.customizer import TypeRegistryCustomizer, ImplementationsCustomizer, \
    TypeImplementationsCustomizer
from thinking_injection.registry.customizable.protocol import CustomizableTypeRegistry
from thinking_injection.registry.protocol import TypeIndex, Implementations, Prerequisites, DiscoveredTypes, \
    TypeIndexMixin
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



# @snapshot_as_lifecycle #todo
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

    def remove(self, *t: Collectable[type]):
        unknowns = []
        for x in collect(type, *t):
            if x in self.data:
                del self.data[x]
            else:
                unknowns.append(x)
            for v in self.data.values():
                v.dependencies = { d for d in v.dependencies if d.type_ != x }
                v.implementations.remove(x)
                if v.forced_primary == x:
                    v.forced_primary = None
        if unknowns:
            raise UnknownTypesException("Cannot remove unknown types from type registry", unknowns)

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

    def type_index(self) -> TypeIndex:
        return SimpleIndex(frozendict({
            t: desc.freeze(lambda: self._figure_out_primary(t))
            for t, desc in self.data.items()
        }))

    def customizer(self) -> TypeRegistryCustomizer:
        return SimpleTypeRegistryCustomizer(self)

    def clone(self) -> Self:
        return SimpleRegistry({k: v.clone() for k, v in self.data.items()})

assert issubclass(SimpleRegistry, CustomizableTypeRegistry)