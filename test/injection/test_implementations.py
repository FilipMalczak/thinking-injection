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

#simple subtype hierarchy of concrete classes
#ditto, but use @primary
#hierarchy of interface impls
#ditto, use @primary


if __name__ == "__main__":
    run_current_module()