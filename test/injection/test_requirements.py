from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from test.util import assert_equals
from thinking_injection.injectable import Injectable
from thinking_injection.interfaces import interface
from thinking_injection.requirements import RequirementsGraph
from thinking_injection.scope import ContextScope


class SimpleDependency: pass

class SimpleDependent(Injectable):
    def inject_requirements(self, simple: SimpleDependency) -> None: pass

class OptionalDependent(Injectable):
    def inject_requirements(self, simple: SimpleDependency | None) -> None: pass


@case
def test_simple_dependency():
    reqs = RequirementsGraph.build(ContextScope.of(SimpleDependency, SimpleDependent))
    expected = RequirementsGraph({
        SimpleDependent: set([SimpleDependency]),
        SimpleDependency: set()
    }, reqs.dependencies, reqs.implementations)
    assert_equals(expected, reqs)

@case
def test_optional_dependency_present():
    reqs = RequirementsGraph.build(ContextScope.of(SimpleDependency, OptionalDependent))
    expected = RequirementsGraph({
        OptionalDependent: set([SimpleDependency]),
        SimpleDependency: set()
    }, reqs.dependencies, reqs.implementations)
    assert_equals(expected, reqs)


@case
def test_optional_dependency_missing():
    reqs = RequirementsGraph.build(ContextScope.of(OptionalDependent))
    expected = RequirementsGraph({
        OptionalDependent: set(),
    }, reqs.dependencies, reqs.implementations)
    assert_equals(expected, reqs)

@interface
class Inter: pass

class Impl1(Inter): pass

class Impl2(Inter): pass

class DependsOnInter(Injectable):
    def inject_requirements(self, inters: list[Inter]) -> None: pass

@case
def test_collective_of_interface_wo_impls():
    reqs = RequirementsGraph.build(ContextScope.of(DependsOnInter))
    expected = RequirementsGraph({
        DependsOnInter: set()
    }, reqs.dependencies, reqs.implementations)
    assert_equals(expected, reqs)

    reqs = RequirementsGraph.build(ContextScope.of(DependsOnInter, Inter))
    expected = RequirementsGraph({
        DependsOnInter: set()
    }, reqs.dependencies, reqs.implementations)
    assert_equals(expected, reqs)

@case
def test_collective_of_interface_w_single_impl():
    reqs = RequirementsGraph.build(ContextScope.of(DependsOnInter, Inter, Impl1))
    expected = RequirementsGraph({
        DependsOnInter: set([Impl1]),
        Impl1: set()
    }, reqs.dependencies, reqs.implementations)
    assert_equals(expected, reqs)


@case
def test_collective_of_interface_w_multiple_impls():
    reqs = RequirementsGraph.build(ContextScope.of(DependsOnInter, Inter, Impl1, Impl2))
    expected = RequirementsGraph({
        DependsOnInter: set([Impl1, Impl2]),
        Impl1: set(),
        Impl2: set()
    }, reqs.dependencies, reqs.implementations)
    assert_equals(expected, reqs)

if __name__ == "__main__":
    # run_current_module()
    test_optional_dependency_missing()
    # test_collective_of_interface_w_single_impl()
    # test_collective_of_interface_w_multiple_impls()