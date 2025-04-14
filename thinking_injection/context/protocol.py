from typing import Protocol, Optional, runtime_checkable, ContextManager, Any

from frozendict import frozendict

from thinking_injection.cloneable import Cloneable
from thinking_injection.common.dependencies import DependencyKind, Dependency, KindDefinition, \
    DependencyValidationException
from thinking_injection.exceptions import InvalidInjectionPointException
from thinking_injection.lifecycle import HasLifecycle
from thinking_injection.registry.protocol import TypeRegistry, TypeIndex
from thinking_programming.collectable import Collectable
from thinking_reflection.interfaces import interface

class DependencyValidationFailureException(InvalidInjectionPointException):
    def __init__(self, exceptions: dict[str, tuple[DependencyValidationException]]):
        self.exceptions: frozendict[str, tuple[DependencyValidationFailureException]] = frozendict(exceptions)
        issues = []
        for requirement_name, excs in exceptions.items():
            for e in excs:
                issues.append(f"{requirement_name}: {e}")
        self.issues: tuple[str, ...] = tuple(issues)
        InvalidInjectionPointException.__init__(self, f"Validation of dependencies failed:\n{'\n'.join("  - "+x for x in self.issues)}")

@interface
class InstanceIndex(ContextManager, Protocol):
    def instance[T](self, t: type[T], *, required: bool = True) -> Optional[T]: ...

    def instances[T](self, t: type[T]) -> frozenset[T]: ...

    def type_index(self) -> TypeIndex: ...

    def resolve_requirement(self, t: type, kind: DependencyKind | KindDefinition) -> Any:
        """
        :raises DependencyValidationFailureException:
        """

    def resolve_dependency(self, d: Dependency) -> Any:
        """
        :raises DependencyValidationFailureException:
        """
        return self.resolve_requirement(d.type_, d.kind)

@interface
class ApplicationContext[ContextLifetime: InstanceIndex](TypeRegistry,
                                                         HasLifecycle[ContextLifetime],
                                                         Cloneable,
                                                         Protocol):
    def remove(self, *t: Collectable[type]):
        '''raises UnknownTypesException''' #todo fix this docstring
