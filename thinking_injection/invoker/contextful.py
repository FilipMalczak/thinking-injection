from typing import NamedTuple, Callable, Any

from thinking_injection.common.dependencies import get_non_method_dependencies
from thinking_injection.context.protocol import InstanceIndex
from thinking_injection.injectable import Injectable
from thinking_injection.invoker.protocol import Invoker
from thinking_reflection.discovery import discover, PrimaryImplementation


#todo index could use this to replace thinking_injection.context.simple.SimpleInstanceIndex._inject_instance
@discover
@PrimaryImplementation(Invoker)
class ContextfulInvoker(Invoker, Injectable):
    def __init__(self):
        self.index: InstanceIndex = None

    def inject_requirements(self, index: InstanceIndex) -> None:
        self.index = index

    def gather_arguments[**P, R](self, callable: Callable[P, R]) -> dict[str, Any]:
        deps = get_non_method_dependencies(callable)
        result =  {
            d.name: self.index.resolve_dependency(d)
            for d in deps
        }
        return result

    def invoke[**P, R](self, callable: Callable[P, R]) -> R:
        return Invoker.invoke(self, callable)
