from enum import Enum
from inspect import getfullargspec
from types import GenericAlias
from typing import NamedTuple, Iterable, Self, Callable, Union, Protocol

from thinking_injection.interfaces import AnyType
from thinking_injection.common.implementations import ImplementationDetails
from thinking_injection.typeset import TypeSet


class ImplementationArity(Protocol):
    def __call__(self, impl_count: int) -> bool:
        """
        Predicate 'does arity match the count?'
        """

    def matches(self, impl_count: int) -> bool:
        return self(impl_count)

    @classmethod
    def of(cls, callable: Callable[[int], bool]) -> Self:
        class Wrapper(ImplementationArity):
            def __init__(self, c):
                self.callable = c

            def __call__(self, i):
                return self.callable(i)
        return Wrapper(callable)


EXACTLY_ONE = ImplementationArity.of(lambda x: x == 1)
ZERO_OR_ONE = ImplementationArity.of(lambda x: x in [0, 1])
ANY_NUMBER = ImplementationArity.of(lambda x: x >= 0)

class KindDefinition(NamedTuple):
    arity: ImplementationArity
    choose_implementations: Callable[[ImplementationDetails], TypeSet]
    matches_hint: Callable[[type], bool]
    unpack_hint: Callable[[type], type]

class _Guard:
    @classmethod
    def _explain(cls):
        assert False, "This type shouldn't be constructed nor subclassed, its only supposed to be used for resolving Unions"

    def __init__(self):
        type(self)._explain()

    @classmethod
    def __init_subclass__(cls, **kwargs):
        cls._explain()


def _ensure_single_type(types: Iterable[type]) -> type:
    out = list(types)
    assert len(out) == 1 #todo msg
    return out[0]

def _nonthrowing_isinstance(*args) -> bool:
    try:
        return isinstance(*args)
    except TypeError:
        return False


def _guard_non_None[T](x: T) -> T:
    assert x is not None
    return x

class DependencyKind(Enum):
    # todo rename to REQUIRED or PRIMARY?
    SIMPLE = KindDefinition(EXACTLY_ONE, lambda details: _guard_non_None(details.primary), lambda t: True, lambda t: t)

    OPTIONAL = KindDefinition(
        ZERO_OR_ONE,
        lambda details: details.primary,
        lambda t: _nonthrowing_isinstance(None, t), # "type is optional" aka "None can be instance of this type"
        lambda t: _ensure_single_type(
            x
            # this turns t to Union and flattens it, no matter if its a single type, Optional, |-style optional or already an union
            for x in Union[t, _Guard].__args__
            if not x in (type(None), _Guard)
        )
    )
    COLLECTIVE = KindDefinition(
        ANY_NUMBER,
        lambda details: set(details.implementations),
        #todo allow for sets next to lists
        lambda t: isinstance(t, GenericAlias) and t.__origin__ == list,
        lambda t: _ensure_single_type(
            x
            for x in Union[*t.__args__, _Guard].__args__
            if x is not _Guard
        )
    )

class Dependency(NamedTuple):
    name: str
    type_: type[AnyType]
    kind: DependencyKind

Dependencies = frozenset[Dependency]

def unpack_dependency(t: type) -> tuple[type, DependencyKind]:
    for kind in [DependencyKind.OPTIONAL, DependencyKind.COLLECTIVE, DependencyKind.SIMPLE]:
        if kind.value.matches_hint(t):
            return kind.value.unpack_hint(t), kind
    assert False #todo msg  no enum matched


def get_dependencies(t: type) -> Dependencies | None:
    try:
        inject_method = t.inject_requirements
    except AttributeError:
        #non-injectable types have no dependencies
        #todo replace with protocol check instead of duck-typing?
        return frozenset()
    spec = getfullargspec(inject_method)
    assert spec.varargs is None, "Inject method cannot have varargs (*args)" #todo better msg
    assert spec.varkw is None, "Inject method cannot have keyword args (**kwargs)" #todo better msg
    if spec.kwonlyargs:
        assert spec.kwonlydefaults is not None
        for kwonly in spec.kwonlyargs:
            assert kwonly in spec.kwonlydefaults, "All keyword-only arguments (*, args) of inject method must have defaults" #todo better msg
    no_default_count = len(spec.args) - (len(spec.defaults) if spec.defaults is not None else 0)
    result = set()
    for i, a in enumerate(spec.args):
        if i == 0:
            continue #skip self
        if i >= no_default_count:
            assert a in spec.annotations, "Inject method arguments must either have defaults or annotations" #todo better msg
        if a in spec.annotations:
            t, kind = unpack_dependency(spec.annotations[a])
            result.add(Dependency(a, t, kind))
    return frozenset(result)
