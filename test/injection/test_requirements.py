from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_injection.injectable import Injectable
from thinking_injection.interfaces import interface
from thinking_injection.requirements import RequirementsGraph


class SimpleDependency: pass

class SimpleDependent(Injectable):
    def inject_requirements(self, simple: SimpleDependency) -> None: pass

class OptionalDependent(Injectable):
    def inject_requirements(self, simple: SimpleDependency | None) -> None: pass


@case
def test_simple_dependency():
    reqs = RequirementsGraph.build(set([SimpleDependency, SimpleDependent]))
    expected = RequirementsGraph({
        SimpleDependent: set([SimpleDependency]),
        SimpleDependency: set()
    })
    assert expected == reqs

@case
def test_optional_dependency_present():
    reqs = RequirementsGraph.build(set([SimpleDependency, OptionalDependent]))
    expected = RequirementsGraph({
        OptionalDependent: set([SimpleDependency]),
        SimpleDependency: set()
    })
    assert expected == reqs


@case
def test_optional_dependency_missing():
    reqs = RequirementsGraph.build(set([OptionalDependent]))
    expected = RequirementsGraph({
        OptionalDependent: set(),
    })
    assert expected == reqs

@interface
class Inter: pass

class Impl1(Inter): pass

class Impl2(Inter): pass

class DependsOnInter(Injectable):
    def inject_requirements(self, inters: list[Inter]) -> None: pass

@case
def test_collective_of_interface_wo_impls():
    reqs = RequirementsGraph.build(set([DependsOnInter]))
    expected = RequirementsGraph({
        DependsOnInter: set()
    })
    assert expected == reqs

    reqs = RequirementsGraph.build(set([DependsOnInter, Inter]))
    expected = RequirementsGraph({
        DependsOnInter: set(),
        Inter: set()
    })
    assert expected == reqs

@case
def test_collective_of_interface_w_single_impl():
    reqs = RequirementsGraph.build(set([DependsOnInter, Inter, Impl1]))
    expected = RequirementsGraph({
        DependsOnInter: set([Impl1]),
        Inter: set(),
        Impl1: set()
    })
    assert expected == reqs


@case
def test_collective_of_interface_w_multiple_impls():
    reqs = RequirementsGraph.build(set([DependsOnInter, Inter, Impl1, Impl2]))
    expected = RequirementsGraph({
        DependsOnInter: set([Impl1, Impl2]),
        Inter: set(),
        Impl1: set(),
        Impl2: set()
    })
    assert expected == reqs

if __name__ == "__main__":
    run_current_module()
    # test_optional_dependency_missing()
    # test_collective_of_interface_w_single_impl()