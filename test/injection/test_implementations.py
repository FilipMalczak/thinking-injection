from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from test.injection import class_fixtures
from thinking_injection.implementations import Implementations, ImplementationDetails
from thinking_injection.typeset import from_module


@case
def test_fixture_impls():
    typeset = from_module(class_fixtures)
    impls = Implementations.build(typeset)
    expected = Implementations({
        t: ImplementationDetails(frozenset([t]), t)
        for t in typeset
    })
    assert expected == impls

class ConcreteParent: pass

class ConcreteChild1(ConcreteParent): pass

class ConcreteChild2(ConcreteParent): pass

class ConcreteGrandchild11(ConcreteChild1): pass

class ConcreteGrandchild12(ConcreteChild1): pass


@case
def test_concrete_hierarchy_with_default_primary():
    impls = Implementations.build({ConcreteParent, ConcreteChild1, ConcreteChild2, ConcreteGrandchild11, ConcreteGrandchild12})
    expected = Implementations({
        ConcreteParent: ImplementationDetails(frozenset([ConcreteChild1, ConcreteChild2, ConcreteGrandchild11, ConcreteGrandchild12]), ConcreteParent),
        ConcreteChild1: ImplementationDetails(frozenset([ConcreteChild1, ConcreteGrandchild11, ConcreteGrandchild12]), ConcreteChild1),
        ConcreteChild2: ImplementationDetails(frozenset([ConcreteChild2]), ConcreteChild2),
        ConcreteGrandchild11: ImplementationDetails(frozenset([ConcreteGrandchild11]), ConcreteGrandchild11),
        ConcreteGrandchild12: ImplementationDetails(frozenset([ConcreteGrandchild12]), ConcreteGrandchild12)
    })

#simple subtype hierarchy of concrete classes
#ditto, but use @primary
#hierarchy of interface impls
#ditto, use @primary


if __name__ == "__main__":
    run_current_module()