from dataclasses import dataclass
from typing import NamedTuple
from unittest.mock import call

from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from test.util import parametrized_case
from thinking_injection.context.configurable.impl import ConfigurableContext
from thinking_injection.lifecycle import Initializable
from thinking_programming.mocking import mocked_property, GetSet, ReflectiveMock, MockTypes


class Foo:
    def foo(self, x=None): return 10

class MockFoo(MockTypes):
    def mocks(self) -> list[type]:
        return [Foo]

@case
def test_simplest_resolving():
    ctx = ConfigurableContext([Foo, MockFoo])
    with ctx.lifecycle() as index:
        f = index.instance(Foo)
        f.foo.return_value = 20
        assert f.foo() == 20
        assert len(f.foo.mock_calls) == 1

#fixme this is weird, if I use Injectable here, there's an error
class Bar(Initializable):
    def inject_requirements(self, foo: Foo) -> None:
        self.foo = foo

    def bar(self):
        return self.foo.foo(self)

@case
def test_simple_dependency():
    ctx = ConfigurableContext([Foo, MockFoo, Bar])
    with ctx.lifecycle() as index:
        f = index.instance(Foo)
        f.foo.return_value = 20
        b = index.instance(Bar)
        assert b.bar() == 20
        assert len(f.foo.mock_calls) == 1

class Baz:
    def baz(self, x: int) -> int:
        return 2*x

class FirstLevelDependency(Initializable):
    def inject_requirements(self, baz: Baz) -> None:
        self.baz = baz

    def call_me(self):
        return self.baz.baz(100)

class SecondLevelDependency(Initializable):
    def inject_requirements(self, baz: Baz, first: FirstLevelDependency) -> None:
        self.baz = baz
        self.first = first

    def call_me(self):
        return self.baz.baz(200) + self.first.call_me()

class MockBaz(MockTypes):
    def mocks(self) -> list[type]:
        return [Baz]

@case
def test_2_levels_of_dependencies():
    ctx = ConfigurableContext([Baz, FirstLevelDependency, SecondLevelDependency, MockBaz])
    with ctx.lifecycle() as index:
        baz = index.instance(Baz)
        baz.baz.return_value = 50
        second = index.instance(SecondLevelDependency)
        s = second.call_me()
        assert s == 100
        assert baz.baz.mock_calls == [ call(200), call(100) ]

@dataclass
class ADataclass:
    x: int

class ANamedTuple(NamedTuple):
    x: int

class ROProperty:
    @property
    def x(self) -> int:
        return 10


class RWProperty:
    @property
    def x(self) -> int:
        return 20

    @x.setter
    def x(self, x: int):
        pass

for to_be_mocked in [ADataclass, ANamedTuple, ROProperty, RWProperty]:
    class EnforcerForPropertyHolder(MockTypes):
        def mocks(self) -> list[type]:
            return [to_be_mocked]

    @parametrized_case(params=[to_be_mocked])
    def test_property_mocking(tbm): # tbm = to be mocked
        ctx = ConfigurableContext([to_be_mocked, EnforcerForPropertyHolder])
        with ctx.lifecycle() as index:
            holder = index.instance(to_be_mocked)
            x = holder.x
            p = mocked_property(holder, "x")
            assert isinstance(x, ReflectiveMock)
            assert int in x.mocked_types
            assert p.mock_calls == [ call(GetSet.GET) ]
            holder.x = 123
            assert p.mock_calls == [call(GetSet.GET), call(GetSet.SET, 123)]
            x2 = holder.x
            assert x is x2


class PropertyType:
    def some_method(self) -> int:
        return 2345

@dataclass
class PropertyOwner:
    prop: PropertyType

class MockOwner(MockTypes):
    def mocks(self) -> list[type]:
        return [PropertyOwner]

@case
def test_properties_that_get_mocked():
    ctx = ConfigurableContext([PropertyType, PropertyOwner, MockOwner])
    with ctx.lifecycle() as index:
        owner = index.instance(PropertyOwner)
        owner.prop.some_method.return_value = 9876
        v = owner.prop.some_method()
        assert v == 9876
        assert mocked_property(owner, "prop").mock_calls == [
            call(GetSet.GET),
            call(GetSet.GET)
        ]
        assert owner.prop.some_method.mock_calls == [
            call()
        ]

if __name__ == "__main__":
    run_current_module()