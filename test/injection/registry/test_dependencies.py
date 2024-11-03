from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from test.injection.fixtures.class_fixtures import *
from test.util import assert_fails
from thinking_injection.common.dependencies import unpack_dependency, DependencyKind, get_dependencies, Dependency


@case
def test_optional_unpacking():
    assert unpack_dependency(str) == (str, DependencyKind.SIMPLE)
    assert unpack_dependency(Optional[str]) == (str, DependencyKind.OPTIONAL)
    assert unpack_dependency(str | None) == (str, DependencyKind.OPTIONAL)
    assert unpack_dependency(Union[str, None]) == (str, DependencyKind.OPTIONAL)
    assert unpack_dependency(Union[str | None]) == (str, DependencyKind.OPTIONAL)
    assert unpack_dependency(Optional[str | None]) == (str, DependencyKind.OPTIONAL)
    assert unpack_dependency(Optional[Union[str | None]]) == (str, DependencyKind.OPTIONAL)
    assert unpack_dependency(Optional[Union[str, None]]) == (str, DependencyKind.OPTIONAL)
    assert_fails(lambda: unpack_dependency(Optional[str | int]))
    assert_fails(lambda: unpack_dependency(str | int | None))
    assert_fails(lambda: unpack_dependency(Optional[str | int | None]))
    assert_fails(lambda: unpack_dependency(Union[str | int] | None))
    assert_fails(lambda: unpack_dependency(Union[str, int] | None))
    assert_fails(lambda: unpack_dependency(Union[str | int, None]))

@case
def test_collective_unpacking():
    assert unpack_dependency(list[str]) == (str, DependencyKind.COLLECTIVE)
    assert_fails(lambda: unpack_dependency(list[str | int]))

@case
def test_values_have_no_deps():
    assert get_dependencies(str) == frozenset()
    assert get_dependencies(int) == frozenset()
    assert get_dependencies(SimpleClass) == frozenset()
    assert get_dependencies(ANamedTuple) == frozenset()
    assert get_dependencies(ADataclass) == frozenset()

@case
def test_initializables_have_no_deps():
    assert get_dependencies(HasLifecycleDuckTyped) == frozenset()
    assert get_dependencies(HasLifecycleInheriting) == frozenset()
    assert get_dependencies(SimpleInitializable) == frozenset()

@case
def test_simple_deps():
    assert get_dependencies(InjectableNoDeps) == set()
    assert get_dependencies(InjectableOneValueDep) == {
        Dependency("val", SimpleClass, DependencyKind.SIMPLE)
    }
    assert get_dependencies(InjectableOneConcreteDep) == {
        Dependency("concrete", InjectableNoDeps, DependencyKind.SIMPLE)
    }
    assert get_dependencies(InjectableTwoConcreteDep) == {
        Dependency("concrete1", InjectableNoDeps, DependencyKind.SIMPLE),
        Dependency("concrete2", InjectableOneConcreteDep, DependencyKind.SIMPLE),
    }

@case
def test_optional_deps():
    assert get_dependencies(InjectableOptionalInjectableByTyping) == {
        Dependency("optional", InjectableNoDeps, DependencyKind.OPTIONAL)
    }
    assert get_dependencies(InjectableOptionalInjectableByOperator) == {
        Dependency("optional", InjectableNoDeps, DependencyKind.OPTIONAL)
    }
    assert get_dependencies(InjectableOptionalInjectableByUnion) == {
        Dependency("optional", InjectableNoDeps, DependencyKind.OPTIONAL)
    }

    assert get_dependencies(InjectableOptionalValueByTyping) == {
        Dependency("optional", SimpleClass, DependencyKind.OPTIONAL)
    }
    assert get_dependencies(InjectableOptionalValueByOperator) == {
        Dependency("optional", SimpleClass, DependencyKind.OPTIONAL)
    }
    assert get_dependencies(InjectableOptionalValueByUnion) == {
        Dependency("optional", SimpleClass, DependencyKind.OPTIONAL)
    }


@case
def test_collective_deps():
    assert get_dependencies(InjectableCollectiveByInterface) == {
        Dependency("x", AnInterface, DependencyKind.COLLECTIVE)
    }
    assert get_dependencies(InjectableCollectiveByImpl1) == {
        Dependency("x", Impl1, DependencyKind.COLLECTIVE)
    }
    assert get_dependencies(InjectableCollectiveByImpl2) == {
        Dependency("x", Impl2, DependencyKind.COLLECTIVE)
    }

@case
def test_interesting():
    assert get_dependencies(Interesting1) == {
        Dependency("a", InjectableNoDeps, DependencyKind.SIMPLE),
        Dependency("b", InjectableOneValueDep, DependencyKind.OPTIONAL),
        Dependency("c", Impl2, DependencyKind.SIMPLE),
        Dependency("d", AnInterface, DependencyKind.SIMPLE),
        Dependency("e", AnInterface, DependencyKind.COLLECTIVE),
        Dependency("f", Impl1, DependencyKind.COLLECTIVE)
    }

if __name__ == "__main__":
    run_current_module()
