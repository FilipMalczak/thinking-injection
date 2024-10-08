from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from test.util import assert_equal_dicts
from thinking_injection.injectable import Injectable
from thinking_injection.interfaces import interface
from thinking_injection.registry.protocol import TypeRegistry
from thinking_injection.registry.simple import SimpleRegistry


def reqs(registry: TypeRegistry) -> dict[type, frozenset[type]]:
    snap = registry.snapshot()
    return {
        t: snap.prerequisites(t)
        for t in snap.known_concrete_types()
    }


class SimpleDependency: pass

class SimpleDependent(Injectable):
    def inject_requirements(self, simple: SimpleDependency) -> None: pass

class OptionalDependent(Injectable):
    def inject_requirements(self, simple: SimpleDependency | None) -> None: pass


@case
def test_simple_dependency():
    registry = SimpleRegistry.make(SimpleDependency, SimpleDependent)
    expected = {
        SimpleDependent: frozenset([SimpleDependency]),
        SimpleDependency: frozenset()
    }
    assert_equal_dicts(expected, reqs(registry))

@case
def test_optional_dependency_present():
    registry = SimpleRegistry.make(SimpleDependency, OptionalDependent)
    expected = {
        OptionalDependent: frozenset([SimpleDependency]),
        SimpleDependency: frozenset()
    }
    assert_equal_dicts(expected, reqs(registry))


@case
def test_optional_dependency_missing():
    registry = SimpleRegistry.make(OptionalDependent)
    expected = {
        OptionalDependent: frozenset(),
    }
    assert_equal_dicts(expected, reqs(registry))

@interface
class Inter: pass

class Impl1(Inter): pass

class Impl2(Inter): pass

class DependsOnInter(Injectable):
    def inject_requirements(self, inters: list[Inter]) -> None: pass

@case
def test_collective_of_interface_wo_impls():
    registry = SimpleRegistry.make(DependsOnInter)
    expected = {
        DependsOnInter: frozenset()
    }
    assert_equal_dicts(expected, reqs(registry))

    registry = SimpleRegistry.make(DependsOnInter, Inter)
    expected = {
        DependsOnInter: frozenset()
    }
    assert_equal_dicts(expected, reqs(registry))

@case
def test_collective_of_interface_w_single_impl():
    registry = SimpleRegistry.make(DependsOnInter, Inter, Impl1)
    expected = {
        DependsOnInter: frozenset([Impl1]),
        Impl1: frozenset()
    }
    assert_equal_dicts(expected, reqs(registry))


@case
def test_collective_of_interface_w_multiple_impls():
    registry = SimpleRegistry.make(DependsOnInter, Inter, Impl1, Impl2)
    expected = {
        DependsOnInter: frozenset([Impl1, Impl2]),
        Impl1: frozenset(),
        Impl2: frozenset()
    }
    assert_equal_dicts(expected, reqs(registry))

if __name__ == "__main__":
    run_current_module()
    # test_optional_dependency_missing()
    # test_collective_of_interface_w_single_impl()
    # test_collective_of_interface_w_multiple_impls()