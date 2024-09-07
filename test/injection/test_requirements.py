from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_injection.dependencies import DependencyGraph
from thinking_injection.implementations import Implementations
from thinking_injection.injectable import Injectable
from thinking_injection.requirements import RequirementsGraph


class SimpleDependency: pass

class SimpleDependent(Injectable):
    def inject_requirements(self, simple: SimpleDependency) -> None: pass

class OptionalDependent(Injectable):
    def inject_requirements(self, simple: SimpleDependency | None) -> None: pass


@case
def test_basic_dependency():
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



if __name__ == "__main__":
    run_current_module()
    # test_optional_dependency_missing()