from typing import Protocol, Callable, Any

#todo define what happens if cannot resolve the args
class Invoker(Protocol):
    def gather_arguments[**P, R](self, callable: Callable[P, R]) -> dict[str, Any]: ...

    def invoke[**P, R](self, callable: Callable[P, R]) -> R:
        arguments = self.gather_arguments(callable)
        return callable(**arguments)