from enum import Enum
from inspect import getfullargspec
from types import GenericAlias
from typing import NamedTuple, Iterable, Self, Callable, Union, Protocol, Any

from thinking_injection.common.implementations import ImplementationDetails
from thinking_injection.exceptions import InvalidInjectionPointException
from thinking_injection.typeset import TypeSet
from thinking_programming.exceptions import WrongIterableSizeException, NoneValueException, UnreachableInstructionException
from thinking_programming.singleton import NastySingleton
from thinking_reflection.interfaces import AnyType, ConcreteType


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



class _Guard:
    @classmethod
    def _explain(cls):
        UnreachableInstructionException.guard("This type shouldn't be constructed nor subclassed, its only supposed to be used for resolving Unions")

    def __init__(self):
        type(self)._explain()

    @classmethod
    def __init_subclass__(cls, **kwargs):
        cls._explain()


def _guard_len_equals(types: Iterable[type], l: int) -> list[type]:
    """
    :raise WrongIterableSizeException:
    """
    out = list(types)
    WrongIterableSizeException.guard(out, l)
    return out


def _nonthrowing_isinstance(*args) -> bool:
    try:
        return isinstance(*args)
    except TypeError:
        return False


#todo most likely unused
def _guard_non_none[T](x: T, details: str) -> T:
    """
    :raise NoneValueException:
    """
    NoneValueException.guard(x, details)
    return x

def flatten_types(*ts: type) -> list[type]:
    return [
        x
        # this turns t to Union and flattens it, no matter if its a single type, Optional, |-style optional or already an union
        for x in Union[*ts, _Guard].__args__
        if x not in (type(None), _Guard)
    ]

class KindDefinition(NastySingleton):# todo make it abc
    # arity: ImplementationArity #todo get rid of this

    def choose_injected_types(self, details: ImplementationDetails) -> list[ConcreteType]:
        """
        Used when figuring out the prerequisites as well as when performing injection. Chooses which implementation(s)
        to use.
        """

    def validate_injected_types(self, to_inject: list[ConcreteType]):
        """
        Called immediately after choose_injected_types; should raise some exception if there is an incorrect state (e.g.
        any implementation was expected, but none were found, in case of simple dependency).
        """
    #todo get_injected_types = choose then validate

    def as_injected_value(self, values_to_inject: list) -> Any:
        """
        Used when performing the injection. Expects to be passed any number of instances managed by the context
        and should return the value to actually be injected. Core use case: return the first element for optional/simple
        dependencies, but return the whole list for collective one.

        Shouldn't do any validation - it will happen before we even touch instances, on the type choosing level;
        validate_injected_types(type(x) for x in values_to_inject) is guaranteed to be True if this method is called
        at all.
        """

    def matches_hint(self, t: type) -> bool:
        """
        Used when parsing the dependencies. Should return whether the given type (possibly an alias, like Optional or
        list[...]) indicates the kind of dependency represented by self.
        """

    def unpack_hint(self, t: type) -> type:
        """
        Only called if matches_hint(t) == True; used to strip the metadata (like Optional[X], list[X], etc) to the
        dependendency type (X, in mentioned examples).
        """

class SimpleDependency(KindDefinition):
    # @property
    # def arity(self) -> ImplementationArity: return EXACTLY_ONE

    def choose_injected_types(self, details: ImplementationDetails) -> list[ConcreteType]:
        return [ details.primary ]

    def validate_injected_types(self, to_inject: list[ConcreteType]):
        assert len(to_inject) == 1 #todo better exception

    def as_injected_value(self, values_to_inject: list) -> Any:
        return values_to_inject[0]

    def matches_hint(self, t: type) -> bool:
        return True

    def unpack_hint(self, t: type) -> type:
        return t

class OptionalDependency(KindDefinition):
    # @property
    # def arity(self) -> ImplementationArity: return ZERO_OR_ONE

    def choose_injected_types(self, details: ImplementationDetails) -> Any:
        return [ details.primary ] if details.primary else []

    def validate_injected_types(self, to_inject: list[ConcreteType]):
        try:
            assert len(to_inject) < 2 #todo better exception
        except:
            raise

    def as_injected_value(self, values_to_inject: list) -> Any:
        return values_to_inject[0] if values_to_inject else None

    def matches_hint(self, t: type) -> bool:
        return _nonthrowing_isinstance(None, t) # "type is optional" aka "None can be an instance of this type"

    def unpack_hint(self, t: type) -> type:
        return _guard_len_equals(flatten_types(t), 1)[0]

class CollectiveDependency(KindDefinition):
    # @property
    # def arity(self) -> ImplementationArity: return ANY_NUMBER

    def choose_injected_types(self, details: ImplementationDetails) -> Any:
        return list(details.implementations)

    def validate_injected_types(self, to_inject: list[ConcreteType]):
        pass

    def as_injected_value(self, values_to_inject: list) -> Any:
        return values_to_inject

    def matches_hint(self, t: type) -> bool:
        # todo allow for sets next to lists
        return isinstance(t, GenericAlias) and t.__origin__ == list

    def unpack_hint(self, t: type) -> type:
        return _guard_len_equals(flatten_types(*t.__args__), 1)[0]


class DependencyKind(Enum):
    SIMPLE = SimpleDependency()
    OPTIONAL = OptionalDependency()
    COLLECTIVE = CollectiveDependency()

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


def get_function_dependencies[**P, R](callable: Callable[P, R]) -> Dependencies:
    """
    :raise InvalidInjectionPointException:
    """
    spec = getfullargspec(callable)
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


def get_type_dependencies(t: type) -> Dependencies:
    try:
        inject_method = t.inject_requirements
    except AttributeError:
        # non-injectable types have no dependencies
        # todo replace with protocol check instead of duck-typing?
        return frozenset()
    return get_function_dependencies(inject_method)
