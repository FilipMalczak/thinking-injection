from typing import Callable

from thinking_executor.executor import ExecutorDecoratorsMixin, TaskExecutor
from thinking_executor.executor_model import TaskKey, TaskType, Args
from thinking_injection.injectable import Injectable
from thinking_injection.invoker.protocol import Invoker
from thinking_programming.str import StrReprMixin

#todo untested outside of example project
class ContextfulTaskExecutor(Injectable, ExecutorDecoratorsMixin, StrReprMixin):
    def __init__(self):
        self.invoker: Invoker = None
        self.executor: TaskExecutor = None

    def inject_requirements(self, invoker: Invoker, executor: TaskExecutor) -> None:
        self.invoker = invoker
        self.executor = executor

    #todo parametrize callable
    def execute(self, task_key: TaskKey, task_body: Callable, task_type: TaskType, task_args: Args = None):
        args = Args.of(**self.invoker.gather_arguments(task_body)) << (task_args or Args())
        self.executor.execute(task_key, task_body, task_type, args)