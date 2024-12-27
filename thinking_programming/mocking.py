# from unittest.mock import Mock
#
# class X:
#     a: int
#
# m = Mock()
# m.x = Mock(spec_set=X)
# m.x.a = 2
# print(m.x)
# print(m.x.a)
# print(isinstance(m.x, X))
# m.x.b = 3
from abc import abstractmethod
from collections import defaultdict
from email.policy import default
from enum import Enum, auto
from functools import wraps
from typing import Iterable, Optional, Protocol
from unittest.mock import MagicMock, PropertyMock, Mock

from typing_extensions import NamedTuple

from thinking_injection.context.configurable.configurator import specialized_configurator, ContextConfigurator
from thinking_injection.context.configurable.phase import ConfigurationPhase, AddingFallbackImpls
from thinking_injection.registry.customizable.customizer import TypeRegistryCustomizer
from thinking_reflection.definitions import TypeDefinition
from thinking_reflection.interfaces import interface
from thinking_reflection.model.members import UNSUPPORTED

class GetSet(Enum):
    GET = auto()
    SET = auto()

class InstanceAwarePropertyMock(NamedTuple):
    name: str

    def __get__(self, instance, owner):
        return instance.__property_mocks__[self.name](GetSet.GET)

    def __set__(self, instance, value):
        instance.__property_mocks__[self.name](GetSet.SET, value)


class ReflectiveMock:
    def __init_subclass__(cls, *, mocked_types: Iterable[type]):
        cls.mocked_types = frozenset(mocked_types)
        props: dict[str, set[type]] = defaultdict(set)
        methods: set[str] = set()
        for t in mocked_types:
            definition = TypeDefinition.of(t)
            desc = definition.type_descriptor
            for fn, fds in desc.fields.items():
                for fd in fds:
                    props[fn].add(fd.get_type)
            for mn, mds in desc.methods.items():
                methods.add(mn)
        for x in props.values():
            if UNSUPPORTED in x:
                x.remove(UNSUPPORTED)

        raw__init__ = cls.__init__

        @wraps(raw__init__)
        def __init__(self, *args, **kwargs):
            raw__init__(self, *args, **kwargs)

            def _lazy_get(n: str):
                if n not in self.__property_mock_values__:
                    class YetAnotherMock(ReflectiveMock, mocked_types=props[n]): pass

                    self.__property_mock_values__[n] = YetAnotherMock()
                return self.__property_mock_values__[n]

            def _make_side_effect(n):
                def _mock_side_effect(direction, val=None):
                    if direction is GetSet.GET:
                        return _lazy_get(n)
                return _mock_side_effect

            self.__property_mocks__ = {
                pn: Mock(side_effect=_make_side_effect(pn))
                for pn in props
            }

            self.__property_mock_values__ = {}
        cls.__init__ = __init__
        for pn, pts in props.items():
            setattr(cls, pn, InstanceAwarePropertyMock(pn))
        for mn in methods:
            setattr(cls, mn, Mock())



#todo better signature
def reflective_mock(*t: type) -> type:
    class SpecializedReflectiveMock(ReflectiveMock, mocked_types=set(t)): pass
    return SpecializedReflectiveMock

class Mocking(ConfigurationPhase):
    def __init__(self): pass

    @property
    def name(self) -> str:
        return "mocking"

    def inject_requirements(self, phase: AddingFallbackImpls): pass

@interface
@specialized_configurator(Mocking)
class MockTypes(ContextConfigurator):
    def __init__(self):
        self._phase: Mocking = None

    @abstractmethod
    def mocks(self) -> Iterable[type]: pass

    def configure_context(self, customizer: TypeRegistryCustomizer):
        to_be_mocked = self.mocks()
        assert to_be_mocked  # todo msg; assert is iterable mapping
        for t in to_be_mocked:
            #make the type an interface, so it wont ever get instantiated
            interface(t)
            mocked = mock_of(t)
            impls = customizer.implementations[t]
            if not mocked in impls.all:
                customizer.register(mocked)
            impls.primary = mocked

    def inject_requirements(self, phase: Mocking):
        self._phase = phase

    def phase(self) -> ConfigurationPhase:
        return self._phase

#todo cleanup this module

class Foo:
    x: int

    def foo(self): pass

class Bar(Protocol):
    x: str

    def baz(self, x: int) -> str: pass

#
class X(ReflectiveMock, mocked_types=[Foo, Bar]): pass

#todo use collectable
def mock_of(*t: type) -> type:
    class MockOf(ReflectiveMock, mocked_types=t): pass
    return MockOf

def mocked_property(mock, prop_name: str):
    return mock.__property_mocks__[prop_name]

x = X()
print(x.x)