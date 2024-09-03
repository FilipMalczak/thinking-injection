from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from test.injection import class_fixtures
from thinking_injection.implementations import Implementations
from thinking_injection.typeset import from_module


@case
def test_fixture_impls():
    impls = Implementations.build(from_module(class_fixtures))
    print(impls)

if __name__ == "__main__":
    run_current_module()