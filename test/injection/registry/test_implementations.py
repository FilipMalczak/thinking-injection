from typing import NamedTuple, Self

from thinking_tests.decorators import case

from test.injection.fixtures import class_fixtures
from test.util import assert_equal_dicts
from thinking_injection.discovery import PrimaryImplementation
from thinking_injection.interfaces import interface, is_concrete
from thinking_injection.registry.protocol import TypeRegistry
from thinking_injection.registry.simple import SimpleRegistry
from thinking_injection.typeset import from_module


class Details(NamedTuple):
    implementations: frozenset[type]
    primary: type | None

    @classmethod
    def of(cls, registry: TypeRegistry) -> dict[type, Self]:
        snap = registry.snapshot()
        return {
            t: Details(snap.implementations(t), snap.primary_implementation(t))
            for t in snap.known_types()
        }

@case
def test_fixture_impls():
    typeset = from_module(class_fixtures)
    registry = SimpleRegistry.make(typeset)
    expected = {
        t:
            Details(frozenset([t]), t)
            if is_concrete(t) else
            Details(frozenset(), None)
        for t in typeset
    }
    expected[class_fixtures.AnInterface] = Details(frozenset([class_fixtures.Impl1, class_fixtures.Impl2, class_fixtures.Impl11]), None)
    expected[class_fixtures.Impl1] = Details(frozenset([class_fixtures.Impl1, class_fixtures.Impl11]), class_fixtures.Impl1)
    assert_equal_dicts(expected, Details.of(registry))


class ConcreteParent: pass

class ConcreteChild1(ConcreteParent): pass

class ConcreteChild2(ConcreteParent): pass

class ConcreteGrandchild11(ConcreteChild1): pass

class ConcreteGrandchild12(ConcreteChild1): pass


@case
def test_concrete_hierarchy_with_default_primary():
    registry = SimpleRegistry.make(ConcreteParent, ConcreteChild1, ConcreteChild2, ConcreteGrandchild11, ConcreteGrandchild12)
    expected = {
        ConcreteParent: Details(frozenset([ConcreteParent,ConcreteChild1, ConcreteChild2, ConcreteGrandchild11, ConcreteGrandchild12]), ConcreteParent),
        ConcreteChild1: Details(frozenset([ConcreteChild1, ConcreteGrandchild11, ConcreteGrandchild12]), ConcreteChild1),
        ConcreteChild2: Details(frozenset([ConcreteChild2]), ConcreteChild2),
        ConcreteGrandchild11: Details(frozenset([ConcreteGrandchild11]), ConcreteGrandchild11),
        ConcreteGrandchild12: Details(frozenset([ConcreteGrandchild12]), ConcreteGrandchild12)
    }
    assert_equal_dicts(expected, Details.of(registry))


class ConcreteParent2: pass

class ConcreteChild21(ConcreteParent2): pass

@PrimaryImplementation(ConcreteParent2).set
class ConcreteChild22(ConcreteParent2): pass

@PrimaryImplementation(ConcreteChild21).set
class ConcreteGrandchild211(ConcreteChild21): pass

class ConcreteGrandchild212(ConcreteChild21): pass


@case
def test_concrete_hierarchy_with_specific_primaries():
    registry = SimpleRegistry.make(ConcreteParent2, ConcreteChild21, ConcreteChild22, ConcreteGrandchild211, ConcreteGrandchild212)
    expected = {
        ConcreteParent2: Details(frozenset([ConcreteParent2,ConcreteChild21, ConcreteChild22, ConcreteGrandchild211, ConcreteGrandchild212]), ConcreteChild22),
        ConcreteChild21: Details(frozenset([ConcreteChild21, ConcreteGrandchild211, ConcreteGrandchild212]), ConcreteGrandchild211),
        ConcreteChild22: Details(frozenset([ConcreteChild22]), ConcreteChild22),
        ConcreteGrandchild211: Details(frozenset([ConcreteGrandchild211]), ConcreteGrandchild211),
        ConcreteGrandchild212: Details(frozenset([ConcreteGrandchild212]), ConcreteGrandchild212)
    }
    assert_equal_dicts(expected, Details.of(registry))


@interface
class TheInterface: pass

class Impl1(TheInterface): pass

class Impl2(TheInterface): pass

class Impl3(Impl2): pass

@interface
class SubInterface1(TheInterface): pass

class SubImpl4(SubInterface1): pass

@case
def no_impl_for_interface():
    registry = SimpleRegistry.make(TheInterface)
    expected= {TheInterface: Details(frozenset(), None)}
    assert_equal_dicts(expected, Details.of(registry))

@case
def single_impl_for_interface():
    registry = SimpleRegistry.make(TheInterface, Impl1)
    expected = {
        TheInterface: Details(frozenset([Impl1]), Impl1),
        Impl1: Details(frozenset([Impl1]), Impl1)
    }
    assert_equal_dicts(expected, Details.of(registry))


@case
def multiple_impls_for_interface():
    registry = SimpleRegistry.make(TheInterface, Impl1, Impl2, Impl3, SubInterface1, SubImpl4)
    expected = {
        TheInterface: Details(frozenset([Impl1, Impl2, Impl3, SubImpl4]), None),
        Impl1: Details(frozenset([Impl1]), Impl1),
        Impl2: Details(frozenset([Impl2, Impl3]), Impl2),
        Impl3: Details(frozenset([Impl3]), Impl3),
        SubInterface1: Details(frozenset([SubImpl4]), SubImpl4),
        SubImpl4: Details(frozenset([SubImpl4]), SubImpl4)
    }
    assert_equal_dicts(expected, Details.of(registry))

@interface
class AnotherInterface: pass

class AnotherImpl1(AnotherInterface): pass

@PrimaryImplementation(AnotherInterface)
class AnotherImpl2(AnotherInterface): pass

@case
def no_impls_for_interface_w_primary():
    registry = SimpleRegistry.make(AnotherInterface)
    expected = {
        AnotherInterface: Details(frozenset(), None)
    }
    assert_equal_dicts(expected, Details.of(registry))

@case
def one_interface_impl_that_isnt_primary():
    registry = SimpleRegistry.make(AnotherInterface, AnotherImpl1)
    expected = {
        AnotherInterface: Details(frozenset([AnotherImpl1]), AnotherImpl1),
        AnotherImpl1: Details(frozenset([AnotherImpl1]), AnotherImpl1)
    }
    assert_equal_dicts(expected, Details.of(registry))

@case
def one_interface_impl_that_is_primary():
    registry = SimpleRegistry.make(AnotherInterface, AnotherImpl2)
    expected = {
        AnotherInterface: Details(frozenset([AnotherImpl2]), AnotherImpl2),
        AnotherImpl2: Details(frozenset([AnotherImpl2]), AnotherImpl2)
    }
    assert_equal_dicts(expected, Details.of(registry))

@case
def interface_with_multiple_impls_and_primary():
    registry = SimpleRegistry.make(AnotherInterface, AnotherImpl1, AnotherImpl2)
    expected = {
        AnotherInterface: Details(frozenset([AnotherImpl1, AnotherImpl2]), AnotherImpl2),
        AnotherImpl1: Details(frozenset([AnotherImpl1]), AnotherImpl1),
        AnotherImpl2: Details(frozenset([AnotherImpl2]), AnotherImpl2)
    }
    assert_equal_dicts(expected, Details.of(registry))

#todo test that PrimaryImplementation(x).set(...) == PrimaryImplementation(x)(...) - already implicitly tested

#todo test defaults and forcing

#todo test protocol implementations

if __name__ == "__main__":
    test_fixture_impls()
    # run_current_module()
    # single_impl_for_interface()