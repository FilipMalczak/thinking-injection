from logging import getLogger

from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from test.injection import class_fixtures
from test.util import assert_equals
from thinking_injection.discovery import PrimaryImplementation
from thinking_injection.implementations import Implementations, ImplementationDetails
from thinking_injection.interfaces import interface, is_concrete
from thinking_injection.scope import ContextScope
from thinking_injection.typeset import from_module

#todo these tests use expected=Implementations(..., result.scope) - extract scope to var, use it there

@case
def test_fixture_impls():
    typeset = from_module(class_fixtures)
    impls = Implementations.build(ContextScope.of(*typeset))
    expected = Implementations({
        t:
            ImplementationDetails(frozenset([t]), t)
            if is_concrete(t) else
            ImplementationDetails(frozenset(), None)
        for t in typeset
    }, impls.scope)
    assert_equals(expected, impls)


class ConcreteParent: pass

class ConcreteChild1(ConcreteParent): pass

class ConcreteChild2(ConcreteParent): pass

class ConcreteGrandchild11(ConcreteChild1): pass

class ConcreteGrandchild12(ConcreteChild1): pass


@case
def test_concrete_hierarchy_with_default_primary():
    impls = Implementations.build(ContextScope.of(ConcreteParent, ConcreteChild1, ConcreteChild2, ConcreteGrandchild11, ConcreteGrandchild12))
    expected = Implementations({
        ConcreteParent: ImplementationDetails(frozenset([ConcreteParent,ConcreteChild1, ConcreteChild2, ConcreteGrandchild11, ConcreteGrandchild12]), ConcreteParent),
        ConcreteChild1: ImplementationDetails(frozenset([ConcreteChild1, ConcreteGrandchild11, ConcreteGrandchild12]), ConcreteChild1),
        ConcreteChild2: ImplementationDetails(frozenset([ConcreteChild2]), ConcreteChild2),
        ConcreteGrandchild11: ImplementationDetails(frozenset([ConcreteGrandchild11]), ConcreteGrandchild11),
        ConcreteGrandchild12: ImplementationDetails(frozenset([ConcreteGrandchild12]), ConcreteGrandchild12)
    }, impls.scope)
    assert_equals(expected, impls)


class ConcreteParent2: pass

class ConcreteChild21(ConcreteParent2): pass

@PrimaryImplementation(ConcreteParent2).set
class ConcreteChild22(ConcreteParent2): pass

@PrimaryImplementation(ConcreteChild21).set
class ConcreteGrandchild211(ConcreteChild21): pass

class ConcreteGrandchild212(ConcreteChild21): pass


@case
def test_concrete_hierarchy_with_specific_primaries():
    impls = Implementations.build(ContextScope.of(ConcreteParent2, ConcreteChild21, ConcreteChild22, ConcreteGrandchild211, ConcreteGrandchild212))
    expected = Implementations({
        ConcreteParent2: ImplementationDetails(frozenset([ConcreteParent2,ConcreteChild21, ConcreteChild22, ConcreteGrandchild211, ConcreteGrandchild212]), ConcreteChild22),
        ConcreteChild21: ImplementationDetails(frozenset([ConcreteChild21, ConcreteGrandchild211, ConcreteGrandchild212]), ConcreteGrandchild211),
        ConcreteChild22: ImplementationDetails(frozenset([ConcreteChild22]), ConcreteChild22),
        ConcreteGrandchild211: ImplementationDetails(frozenset([ConcreteGrandchild211]), ConcreteGrandchild211),
        ConcreteGrandchild212: ImplementationDetails(frozenset([ConcreteGrandchild212]), ConcreteGrandchild212)
    }, impls.scope)
    assert_equals(expected, impls)


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
    impls = Implementations.build(ContextScope.of(TheInterface))
    expected= Implementations({TheInterface: ImplementationDetails(frozenset(), None)}, impls.scope)
    assert_equals(expected, impls)

@case
def single_impl_for_interface():
    impls = Implementations.build(ContextScope.of(TheInterface, Impl1))
    expected = Implementations({
        TheInterface: ImplementationDetails(frozenset([Impl1]), Impl1),
        Impl1: ImplementationDetails(frozenset([Impl1]), Impl1)
    }, impls.scope)
    assert_equals(expected, impls)


@case
def multiple_impls_for_interface():
    impls = Implementations.build(ContextScope.of(TheInterface, Impl1, Impl2, Impl3, SubInterface1, SubImpl4))
    expected = Implementations({
        TheInterface: ImplementationDetails(frozenset([Impl1, Impl2, Impl3, SubImpl4]), None),
        Impl1: ImplementationDetails(frozenset([Impl1]), Impl1),
        Impl2: ImplementationDetails(frozenset([Impl2, Impl3]), Impl2),
        Impl3: ImplementationDetails(frozenset([Impl3]), Impl3),
        SubInterface1: ImplementationDetails(frozenset([SubImpl4]), SubImpl4),
        SubImpl4: ImplementationDetails(frozenset([SubImpl4]), SubImpl4)
    }, impls.scope)
    assert_equals(expected, impls)

@interface
class AnotherInterface: pass

class AnotherImpl1(AnotherInterface): pass

@PrimaryImplementation(AnotherInterface)
class AnotherImpl2(AnotherInterface): pass

@case
def no_impls_for_interface_w_primary():
    impls = Implementations.build(ContextScope.of(AnotherInterface))
    expected = Implementations({
        AnotherInterface: ImplementationDetails(frozenset(), None)
    }, impls.scope)
    assert_equals(expected, impls)

@case
def one_interface_impl_that_isnt_primary():
    impls = Implementations.build(ContextScope.of(AnotherInterface, AnotherImpl1))
    expected = Implementations({
        AnotherInterface: ImplementationDetails(frozenset([AnotherImpl1]), AnotherImpl1),
        AnotherImpl1: ImplementationDetails(frozenset([AnotherImpl1]), AnotherImpl1)
    }, impls.scope)
    assert_equals(expected, impls)

@case
def one_interface_impl_that_is_primary():
    impls = Implementations.build(ContextScope.of(AnotherInterface, AnotherImpl2))
    expected = Implementations({
        AnotherInterface: ImplementationDetails(frozenset([AnotherImpl2]), AnotherImpl2),
        AnotherImpl2: ImplementationDetails(frozenset([AnotherImpl2]), AnotherImpl2)
    }, impls.scope)
    assert_equals(expected, impls)

@case
def interface_with_multiple_impls_and_primary():
    impls = Implementations.build(ContextScope.of(AnotherInterface, AnotherImpl1, AnotherImpl2))
    expected = Implementations({
        AnotherInterface: ImplementationDetails(frozenset([AnotherImpl1, AnotherImpl2]), AnotherImpl2),
        AnotherImpl1: ImplementationDetails(frozenset([AnotherImpl1]), AnotherImpl1),
        AnotherImpl2: ImplementationDetails(frozenset([AnotherImpl2]), AnotherImpl2)
    }, impls.scope)
    assert_equals(expected, impls)

#test that PrimaryImplementation(x).set(...) == PrimaryImplementation(x)(...) - already implicitly tested

#test defaults and forcing

if __name__ == "__main__":
    run_current_module()
    # single_impl_for_interface()