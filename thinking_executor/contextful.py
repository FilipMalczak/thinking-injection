from typing import Callable

from thinking_executor.executor import ExecutorDecoratorsMixin, SimpleTaskExecutor
from thinking_executor.executor_model import TaskKey, TaskType, Args
from thinking_injection.injectable import Injectable
from thinking_injection.invoker.protocol import Invoker
from thinking_programming.str import StrReprMixin
from thinking_reflection.discovery import discover


#todo untested
@discover
class ContextfulTaskExecutor(Injectable, ExecutorDecoratorsMixin, StrReprMixin):
    def __init__(self):
        self.invoker: Invoker = None
        self.executor: SimpleTaskExecutor = None

    def inject_requirements(self, invoker: Invoker, executor: SimpleTaskExecutor) -> None:
        self.invoker = invoker
        self.executor = executor

    #todo parametrize callable
    def execute(self, task_key: TaskKey, task_body: Callable, task_type: TaskType, task_args: Args = None):
        args = Args.of(**self.invoker.gather_arguments(task_body)) << (task_args or Args())
        self.executor.execute(task_key, task_body, task_type, args)