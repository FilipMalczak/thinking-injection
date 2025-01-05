from enum import Enum
from inspect import getfullargspec
from types import GenericAlias
from typing import NamedTuple, Iterable, Self, Callable, Union, Protocol

from thinking_injection.common.implementations import ImplementationDetails
from thinking_injection.exceptions import InvalidInjectionPointException
from thinking_injection.typeset import TypeSet
from thinking_programming.exceptions import WrongIterableSizeException, NoneValueException, UnreachableInstructionException
from thinking_reflection.interfaces import AnyType


class ImplementationArity(Protocol):
    def __call__(self, impl_count: int) -> bool:
        """
        Predicate 'does arity match the count?'
        """

    def matches(self, impl_count: int) -> bool:
        return self(impl_count)

    @classmethod
    def of(cls, c: Callable[[int], bool]) -> Self:
        class Wrapper(ImplementationArity):
            def __init__(self):
                self.callable = c

            def __call__(self, i):
                return self.callable(i)
        return Wrapper()


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
        UnreachableInstructionException.guard("This type shouldn't be constructed nor subclassed, its only supposed to be used for resolving Unions")

    def __init__(self):
        type(self)._explain()

    @classmethod
    def __init_subclass__(cls, **kwargs):
        cls._explain()


def _ensure_single_type(types: Iterable[type]) -> type:
    """
    :raise WrongIterableSizeException:
    """
    out = list(types)
    WrongIterableSizeException.guard(out, 1)
    return out[0]


def _nonthrowing_isinstance(*args) -> bool:
    try:
        return isinstance(*args)
    except TypeError:
        return False


def _guard_non_none[T](x: T) -> T:
    """
    :raise NoneValueException:
    """
    NoneValueException.guard(x)
    return x


class DependencyKind(Enum):
    # todo rename to REQUIRED or PRIMARY?
    SIMPLE = KindDefinition(EXACTLY_ONE, lambda details: _guard_non_none(details.primary), lambda t: True, lambda t: t)

    OPTIONAL = KindDefinition(
        ZERO_OR_ONE,
        lambda details: details.primary,
        lambda t: _nonthrowing_isinstance(None, t), # "type is optional" aka "None can be instance of this type"
        lambda t: _ensure_single_type(
            x
            # this turns t to Union and flattens it, no matter if its a single type, Optional, |-style optional or already an union
            for x in Union[t, _Guard].__args__
            if x not in (type(None), _Guard)
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
    raise NotImplementedError(f"No dependency type matches packed dependency {t}")


class NoDefaultForKwOnlyArgException(InvalidInjectionPointException):
    def __init__(self, issues: list[str]):
        self.issues: tuple[str, ...] = tuple(issues)
        InvalidInjectionPointException.__init__(f"Some keyword-only arguments({issues}) have no default value")


class UnannotatedNoDefaultPositionalArgException(InvalidInjectionPointException):
    def __init__(self, issues: list[str]):
        self.issues: tuple[str, ...] = tuple(issues)
        InvalidInjectionPointException.__init__(f"Some arguments({issues}) have neither a default value nor an annotation")


def get_dependencies(t: type) -> Dependencies | None:
    """
    :raise InvalidInjectionPointException:
    """
    try:
        inject_method = t.inject_requirements
    except AttributeError:
        #non-injectable types have no dependencies
        #todo replace with protocol check instead of duck-typing?
        return frozenset()
    spec = getfullargspec(inject_method)
    #todo rethink these constraints
    # assert spec.varargs is None, "Inject method cannot have varargs (*args)" #todo better msg
    # assert spec.varkw is None, "Inject method cannot have keyword args (**kwargs)" #todo better msg
    if spec.kwonlyargs:
        if spec.kwonlydefaults is None:
            raise NoDefaultForKwOnlyArgException(spec.kwonlyargs)
        missing = []
        for kwonly in spec.kwonlyargs:
            if kwonly not in spec.kwonlydefaults:
                missing.append(kwonly)
        if missing:
            raise NoDefaultForKwOnlyArgException(missing)
    no_default_count = len(spec.args) - (len(spec.defaults) if spec.defaults is not None else 0)
    result = set()
    missing = []
    for i, a in enumerate(spec.args):
        if i == 0:
            continue #skip self
        if i >= no_default_count:
            if a not in spec.annotations:
                missing.append(a)
        if not missing and a in spec.annotations:
            t, kind = unpack_dependency(spec.annotations[a])
            result.add(Dependency(a, t, kind))
    if missing:
        raise UnannotatedNoDefaultPositionalArgException(missing)
    return frozenset(result)
