from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from test.injection.fixtures import class_fixtures
from test.injection.fixtures.subpkg import class_subfixtures
from thinking_injection.typeset import from_module, from_package

EXPECTED_FROM_HIGHER_LEVEL = {
    class_fixtures.SimpleClass,
    class_fixtures.ANamedTuple,
    class_fixtures.ADataclass,

    class_fixtures.HasLifecycleDuckTyped,
    class_fixtures.HasLifecycleInheriting,

    class_fixtures.SimpleInitializable,

    class_fixtures.InjectableNoDeps,
    class_fixtures.InjectableOneValueDep,
    class_fixtures.InjectableOneConcreteDep,
    class_fixtures.InjectableTwoConcreteDep,

    class_fixtures.InjectableOptionalInjectableByTyping,
    class_fixtures.InjectableOptionalInjectableByOperator,
    class_fixtures.InjectableOptionalInjectableByUnion,

    class_fixtures.InjectableOptionalValueByTyping,
    class_fixtures.InjectableOptionalValueByOperator,
    class_fixtures.InjectableOptionalValueByUnion,

    class_fixtures.AnInterface,
    class_fixtures.Impl1,
    class_fixtures.Impl2,
    class_fixtures.Impl11,

    class_fixtures.InjectableCollectiveByInterface,
    class_fixtures.InjectableCollectiveByImpl1,
    class_fixtures.InjectableCollectiveByImpl2,

    class_fixtures.Interesting1
}

#notice no Undiscovered here
EXPECTED_FROM_SUBMODULE = {
    class_subfixtures.Discovered,
    class_subfixtures.AnInjectable,
    class_subfixtures.AnInterface
}

EXPECTED_FROM_WHOLE_PACKAGE = EXPECTED_FROM_HIGHER_LEVEL.union(EXPECTED_FROM_SUBMODULE)

@case
def test_from_module():
    assert from_module(class_fixtures) == EXPECTED_FROM_HIGHER_LEVEL
    assert from_module(class_subfixtures) == EXPECTED_FROM_SUBMODULE

@case
def test_from_package():
    assert from_package("test.injection.fixtures") == EXPECTED_FROM_WHOLE_PACKAGE

if __name__=="__main__":
    run_current_module()