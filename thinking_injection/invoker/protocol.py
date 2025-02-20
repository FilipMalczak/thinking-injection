from typing import Protocol, Callable, Any

from thinking_reflection.interfaces import interface

@interface
class Invoker(Protocol):
    def gather_arguments[**P, R](self, callable: Callable[P, R]) -> dict[str, Any]:
        """
        :raises DependencyValidationFailureException:
        """

    def invoke[**P, R](self, callable: Callable[P, R]) -> R:
        """
        :raises DependencyValidationFailureException:
        """
        arguments = self.gather_arguments(callable)
        return callable(**arguments)