from typing import NamedTuple, Callable, Any

from thinking_injection.common.dependencies import get_function_dependencies
from thinking_injection.context.protocol import InstanceIndex
from thinking_injection.invoker.protocol import Invoker

#todo index could use this to replace thinking_injection.context.simple.SimpleInstanceIndex._inject_instance
class ContextfulInvoker(NamedTuple):
    index: InstanceIndex

    def gather_arguments[**P, R](self, callable: Callable[P, R]) -> dict[str, Any]:
        deps = get_function_dependencies(callable)
        result =  {
            d.name: self.index.resolve_dependency(d)
            for d in deps
        }
        return result

    def invoke[**P, R](self, callable: Callable[P, R]) -> R:
        return Invoker.invoke(self, callable)
