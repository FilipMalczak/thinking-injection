from abc import abstractmethod
from collections import defaultdict
from enum import Enum, auto
from functools import wraps
from logging import getLogger
from typing import Iterable, NamedTuple
from unittest.mock import Mock

from thinking_injection.context.configurable.configurator import specialized_configurator, ContextConfigurator
from thinking_injection.context.configurable.phase import ConfigurationPhase, AddingFallbackImpls
from thinking_injection.registry.customizable.customizer import TypeRegistryCustomizer
from thinking_reflection.definitions import TypeDefinition
from thinking_reflection.interfaces import interface
from thinking_reflection.model.members import UNSUPPORTED

log = getLogger(__name__)

class GetSet(Enum):
    GET = auto()
    SET = auto()


class InstanceAwarePropertyMock(NamedTuple):
    name: str

    def __get__(self, instance, owner):
        return mocked_property(instance, self.name)(GetSet.GET)

    def __set__(self, instance, value):
        mocked_property(instance, self.name)(GetSet.SET, value)


def mocked_property(mock, prop_name: str) -> InstanceAwarePropertyMock:
    return mock.__property_mocks__[prop_name]


class ReflectiveMock:
    def __init__(self):
        """
        Constructor must be empty, so that MRO stops looking into the supertypes; It will be replaced with Mock during __new__
        """

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

        def __new__(cls, *args, **kwargs): #todo ignore linter
            try:
                self = object.__new__(cls, *args, **kwargs)
            except TypeError:
                #this isn't the best way to do this, but if we're mocking stuff like ints, we need to use __new__ other than
                # from object; to be enhanced in the future
                self = list(mocked_types)[0].__new__(cls, *args, **kwargs)

            def _lazy_get(n: str):
                if n not in self.__property_mock_values__:
                    self.__property_mock_values__[n] = reflective_mock(*props[n])()
                return self.__property_mock_values__[n]

            def _make_side_effect(n):
                def _mock_side_effect(direction, val=None):
                    if direction is GetSet.GET:
                        return _lazy_get(n)
                return _mock_side_effect

            # InstanceAwarePropertyMock is a property (so, class-level field) that delegates the call to the
            # __property_mocks__ value (dispatched over property name), adding the direction (GET/SET) parameter
            # Value returned by GET will be a reflective mock (ReflectiveMock subclass) instance. It will be stored in
            # __property_mock_values__.
            #
            # class X:
            #     a: int
            #     def foo(...): ...
            # class Y:
            #     x: X
            #
            # mock_type = reflective_mock(Y)
            # mock = mock_type()
            # mock_type.x is an InstanceAwarePropertyMock
            # mock.__property_mocks__["x"] is an instance of Mock, with lazy side effect that constructs and caches mock for x
            # mock.x is gonna be mock.__property_mock_values__["x"] and it will be an instance of ReflectiveMock
            # mock.x.a will behave the same way - it will be an instance of ReflectiveMock for int type
            # mock.x.foo will be Mock instance, specific to mock.x instance: mock_type().x.foo is not mock.x.foo
            #
            # to check whether the property has been accessed, you can do:
            # mocked_property(mock, "x") which will give you the Mock instance, so you can check things like:
            # mocked_property(mock, "x").assert_called_with(GET)
            # notice that self is not passed to mocked_property(...), as the property mocks are per-instance

            #todo describe methods, the fact that __init__ gets mocked too and that they are not present in the class
            #itself, but are set per-instance (thus, self is present in calls to them)

            self.__property_mocks__ = {
                pn: Mock(side_effect=_make_side_effect(pn))
                for pn in props
            }

            self.__property_mock_values__ = {}
            self.__init__ = Mock()

            for mn in methods:
                setattr(self, mn, Mock())

            return self
        cls.__new__ = __new__
        for pn, pts in props.items():
            setattr(cls, pn, InstanceAwarePropertyMock(pn))


def reflective_mock(*t: type, name=None) -> type[ReflectiveMock]:
    name = name or "ReflectiveMockOf_"+("__".join(x.__name__ for x in t))
    bases = (ReflectiveMock, ) + t
    out = type(name, bases, {}, mocked_types=set(t))
    return out


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
            log.info(f"To be mocked: {t}")
            #make the type an interface, so it wont ever get instantiated
            log.info("Ensuring its an interface")
            interface(t)
            mocked = reflective_mock(t)
            log.info(f"Mocked type: {mocked}")
            impls = customizer.implementations[t]
            log.info(f"Implementations: {impls}")
            if mocked not in impls.all:
                log.info("Registering mocked type")
                customizer.register(mocked)
            log.info("Setting as a primary")
            impls.primary = mocked
            log.info(f"Implementations after mocking: {impls}")


    def inject_requirements(self, phase: Mocking):
        self._phase = phase

    def phase(self) -> ConfigurationPhase:
        return self._phase
