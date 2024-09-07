from functools import cmp_to_key
from typing import Iterable, Self

from thinking_injection.ordering import TypeComparator, requirement_comparator, CyclicResolver
from thinking_injection.dependencies import DependencyGraph, Dependencies, DependencyKind, Dependency
from thinking_injection.guardeddict import GuardedDict
from thinking_injection.implementations import Implementations, ImplementationDetails
from thinking_injection.interfaces import ConcreteClass, ConcreteType
from thinking_injection.typeset import TypeSet


class RequirementsGraph(GuardedDict[ConcreteType, set[ConcreteType]]): #todo make it frozenset
    def __guard__(self, k: type, v: set[ConcreteType]):
        #todo msgs
        assert isinstance(k, ConcreteType)
        assert isinstance(v, set)
        assert all(isinstance(x, ConcreteType) for x in v)

    @classmethod
    def build(cls, types: TypeSet = None, *, deps: DependencyGraph = None, impls: Implementations = None) -> Self:
        if types is None:
            assert deps is not None or impls is not None #todo msg
            if deps is not None:
                types = set(deps.keys())
            else:
                types = set(impls.keys())
        if deps is None:
            deps = DependencyGraph.build(types)
        if impls is None:
            impls = Implementations.build(types)
        data = {}
        for t in types:
            ds = deps[t]
            requirements = set()
            if ds is not None:
                for d in ds:
                    d: Dependency = d
                    impl_details: ImplementationDetails = impls[d.type_]
                    dep_kind = d.kind.value
                    assert dep_kind.arity.matches(len(impl_details.implementations)) #todo msg; fixme should actually check if primary is set or not too
                    impl = dep_kind.choose_implementations(impl_details)
                    requirements.update(impl)
            #todo assert all are concrete?
            data[t] = requirements
        return cls(data)

    def without(self, *t: ConcreteType) -> Self:
        return RequirementsGraph({
            k: set(x for x in v if x not in t)
            for k, v in self.items()
            if k not in t
        })

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
            least_dependent = self.least_dependent()
            order = sorted(least_dependent, key=key_foo)
            for x in order:
                yield x
            remainder = self.without(*least_dependent)
            yield from remainder.order(cyclic_resolver)
