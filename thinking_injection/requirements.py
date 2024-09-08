from functools import cmp_to_key
from typing import Iterable, Self

from thinking_injection.ordering import TypeComparator, requirement_comparator, CyclicResolver
from thinking_injection.dependencies import DependencyGraph, Dependencies, DependencyKind, Dependency
from thinking_injection.guardeddict import GuardedDict
from thinking_injection.implementations import Implementations, ImplementationDetails
from thinking_injection.interfaces import ConcreteClass, ConcreteType, is_concrete
from thinking_injection.scope import ContextScope
from thinking_injection.typeset import TypeSet


class RequirementsGraph(GuardedDict[ConcreteType, set[ConcreteType]]): #todo make it frozenset
    def __init__(self, data: dict[ConcreteType, set[ConcreteType]], deps: DependencyGraph, impls: Implementations):
        GuardedDict.__init__(self, data)
        self.dependencies = deps
        self.implementations = impls

    @property
    def scope(self) -> ContextScope:
        return self.implementations.scope


    def __guard__(self, k: type, v: set[ConcreteType]):
        #todo msgs
        assert isinstance(k, ConcreteType)
        assert isinstance(v, set)
        assert all(isinstance(x, ConcreteType) for x in v)

    @classmethod
    def build(cls, scope: ContextScope) -> Self:
        types = scope.types
        deps = DependencyGraph.build(types)
        # scope = ContextScope.of(*deps.types, defaults=scope.defaults, forced=scope.forced)
        impls = Implementations.build(scope)
        data = {}
        for t in types:
            if is_concrete(t):
                ds = deps[t]
                requirements = set()
                if ds is not None:
                    for d in ds:
                        d: Dependency = d
                        impl_details: ImplementationDetails = impls[d.type_]
                        dep_kind = d.kind.value
                        try:
                            assert dep_kind.arity.matches(len(impl_details.implementations)) #todo msg; fixme should actually check if primary is set or not too
                        except:
                            raise
                        impl = dep_kind.choose_implementations(impl_details)
                        if d.kind == DependencyKind.COLLECTIVE: #todo this should be externalized to kind too
                            requirements.update(impl)
                        #this and following could be simplified, but this is more descriptive
                        elif d.kind == DependencyKind.OPTIONAL:
                            if impl is not None:
                                requirements.add(impl)
                        else:
                            requirements.add(impl)
                #todo assert all are concrete?
                data[t] = requirements
        return cls(data, deps, impls)

    def without(self, *t: ConcreteType) -> Self:
        return RequirementsGraph(
            {
                k: set(x for x in v if x not in t)
                for k, v in self.items()
                if k not in t
            },
            self.dependencies, self.implementations #todo deps/impls.without
        )

    def least_requiring(self) -> set[ConcreteType]:
        counts = {
            k: len(v)
            for k, v in self.items()
        }
        min_count = min(counts.values())
        return {k for k in counts.keys() if counts[k] == min_count}

    def requires(self, target: ConcreteType, requirement: ConcreteType) -> bool:
        return requirement is self[target]

    def order(self, cyclic_resolver: TypeComparator = None) -> Iterable[ConcreteType]:
        comparator = requirement_comparator(self.requires, cyclic_resolver or CyclicResolver())
        key_foo = cmp_to_key(comparator)
        if len(self):
            least_dependent = self.least_requiring()
            order = sorted(least_dependent, key=key_foo)
            for x in order:
                yield x
            remainder = self.without(*least_dependent)
            yield from remainder.order(cyclic_resolver)
