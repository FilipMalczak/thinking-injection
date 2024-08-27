from dataclasses import dataclass, field
from typing import NamedTuple, Self

from thinking_injection.discovery import get_primary_hint
from thinking_injection.guardeddict import GuardedDict
from thinking_injection.interfaces import ConcreteClass, ConcreteType
from thinking_injection.typeset import TypeSet, ImmutableTypeSet, freeze


class ImplementationDetails(NamedTuple):
    implementations: ImmutableTypeSet
    primary: ConcreteType


@dataclass
class MutableImplementationDetails:
    implementations: TypeSet = field(default_factory=set)
    primary: ConcreteType = None

    def add(self, t: ConcreteType):
        assert issubclass(t, ConcreteClass) #todo msg
        self.implementations.add(t)

    def freeze(self) -> ImplementationDetails:
        return ImplementationDetails(freeze(self.implementations), self.primary)


class Implementations(GuardedDict[type, ImplementationDetails]):
    def __guard__(self, k: type, v: ImplementationDetails):
        assert isinstance(k, type) #todo allow for parametrized types; out of MVP
        assert v is not None
        assert isinstance(v, ImplementationDetails)

    @classmethod
    def build(cls, types: TypeSet, defaults: dict[type, type] = None, force: dict[type, type] = None) -> Self:
        """
        :param types - all the known types, including interfaces; basically keyset of dependency graph
        :param defaults - use these as primary implementations only if there is more than one implementation
        :param force - use these as primary implementations unconditionally; can be used to enforce implementation or to provide defaults
        """
        defaults = defaults or {}
        assert all(
            isinstance(k, type) and
            isinstance(v, type) and
            k in types and
            v in types and
            issubclass(v, k)
            for k, v in defaults.items()
        ) #todo msg
        force = force or {}
        assert all(
            isinstance(k, type) and
            isinstance(v, type) and
            k in types and
            v in types and
            issubclass(v, k)
            for k, v in force.items()
        )  # todo msg
        data = {
            t: MutableImplementationDetails()
            for t in types
        }
        for t in types:
            if issubclass(t, ConcreteClass):
                for base in types:
                    if issubclass(t, base):
                        data[base].add(t)
        for t in types:
            details = data[t]
            hint = get_primary_hint(t)
            if hint is not None:
                details.primary = hint
            if details.primary is None and len(details.implementations) == 1:
                details.primary = list(details.implementations)[0]
            if details.primary is None and issubclass(t, ConcreteClass):
                details.primary = t
            if details.primary is None and t in defaults:
                details.primary = defaults[t]
        for t, i in force.items():
            data[t].primary = i
        return cls({k: v.freeze() for k, v in data.items()})
