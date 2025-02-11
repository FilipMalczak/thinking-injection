import traceback
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from logging import getLogger
from typing import Any, Callable

from thinking_tests.fluent_decorator import fluent_method_decorator

from thinking_executor.callbacks.executor import CompositeStepExecutorCallback, StepExecutorCallback
from thinking_executor.data.tiny_schema import TinyDBTableWithSchema, Query
from thinking_executor.data.tinydb import TinyDBLifecycle
from thinking_executor.executor_model import TaskKey, TaskPath, TaskCoordinates, Args, TaskExecutionRecord, \
    DEFAULT_NAME, TaskType, assert_can_have_subtasks

from thinking_executor.session import PersistentSessionManager
from thinking_executor.session_model import ContextSessionPointer
from thinking_injection.injectable import Injectable
from thinking_programming.outcome import outcome_of, ToBeContinuedException, Success
from thinking_programming.str import StrReprMixin

log = getLogger(__name__)

def assert_is_step_key(step_key: Any):
    assert isinstance(step_key, TaskKey), \
        f"Step key must be one of the following types: {', '.join(map(lambda x: x.__name__, TaskKey.__args__))}"


@dataclass
class ExecutionFrame(StrReprMixin):
    current_path: TaskPath
    next_subtask_order: list[int]
    task_type: TaskType

class ExecutorProtocol:

    #just for type hints
    def execute(self, task_key: TaskKey, task_body: Callable, task_type: TaskType, task_args: Args = None): pass

class FluentExecutorMixin(ExecutorProtocol):

    def execute_step(self, step_key: TaskKey, step_body: Callable, step_args: Args = None):
        self.execute(step_key, step_body, TaskType.STEP, step_args)

    def execute_stage(self, stage_key: TaskKey, stage_body: Callable, stage_args: Args = None, tbc=None):
        to_execute = stage_body
        if tbc is not None:
            comment = "" if isinstance(tbc, bool) else str(tbc)
            @wraps(stage_body)
            def tbc_body(*args, **kwargs):
                stage_body(*args, **kwargs)
                toBeContinued(comment)
            to_execute = tbc_body
        self.execute(stage_key, to_execute, TaskType.STAGE, stage_args)


class ExecutorDecoratorsMixin(FluentExecutorMixin):
    @fluent_method_decorator
    def step(self, step_key: TaskKey | DEFAULT_NAME = DEFAULT_NAME, step_args: Args | None = None):
        def decorator(f):
            k = f.__name__ if step_key == DEFAULT_NAME else step_key
            self.execute_step(k, f, step_args)

        return decorator

    @fluent_method_decorator
    def stage(self, stage_key: TaskKey | DEFAULT_NAME = DEFAULT_NAME, stage_args: Args | None = None):
        def decorator(f):
            k = f.__name__ if stage_key == DEFAULT_NAME else stage_key
            self.execute_stage(k, f, stage_args)

        return decorator

class TaskExecutor(Injectable, ExecutorDecoratorsMixin, StrReprMixin):
    def __init__(self):
        self.table: TinyDBTableWithSchema = None
        self.stack: list[ExecutionFrame] = None
        self.session: ContextSessionPointer = None
        self.session_manager: PersistentSessionManager = None
        self.callbacks: CompositeStepExecutorCallback = CompositeStepExecutorCallback()

    def inject_requirements(self, session_manager: PersistentSessionManager, callbacks: list[StepExecutorCallback], tiny: TinyDBLifecycle):
        self.session_manager = session_manager
        self.callbacks.add_delegate(*callbacks)
        self.table = tiny.get_table_of(TaskExecutionRecord)

    def add_callback(self, *callbacks: StepExecutorCallback):
        self.callbacks.add_delegate(*callbacks)

    def initialize(self):
        s = self.session_manager.current_context_session #todo clean up this mess; s in not needed, we operate on pointer here
        assert not self.is_open(), f"Step executor has already been initialized on {s.started_on}"
        self.stack = [ExecutionFrame([], [0], None)]
        self.session = self.session_manager.current_session_pointer
        self.callbacks.before_session(s.started_on, self.current_session)

    def is_open(self) -> bool:
        return self.session is not None

    def deinitialize(self, exception: Exception | None = None):
        self._assert_initialized("closing")
        self.stack = None
        session = self.session
        self.session = None
        outcome = outcome_of(exception)
        self.callbacks.after_session(datetime.now(), session, outcome)

    def _assert_initialized(self, action="usage"):
        assert self.is_open(), f"Step executor must be initialized before {action}!"

    @property
    def current_path(self) -> TaskPath:
        self._assert_initialized()
        return self.stack[-1].current_path

    @property
    def current_key(self) -> TaskKey:
        return self.current_path[-1]

    @property
    def current_order(self) -> list[int]:
        self._assert_initialized()
        return self.stack[-2].next_subtask_order

    @property
    def current_coordinates(self) -> TaskCoordinates:
        return TaskCoordinates(list(self.current_path), list(self.current_order), self.current_task_type)

    @property
    def current_task_type(self) -> TaskType:
        return self.stack[-1].task_type

    @property
    def current_session(self) -> ContextSessionPointer:
        return self.session

    #todo smth here is fucked up
    def _exception_handler(self, e: BaseException, start: datetime, coordinates: TaskCoordinates) -> bool:
        '''
        :return: indicates whether to let the exception bubble up
        '''
        finish = datetime.now()

        outcome = outcome_of(e)

        log.info(f"Task {coordinates} stopped before finishing (outcome: {outcome})")
        self.callbacks.on_task_finished(start, finish, coordinates, outcome)
        if not isinstance(e, ToBeContinuedException) or len(coordinates) > 1:
            return True
        log.error(''.join(traceback.format_exception(e)))
        return False

    def execute(self, task_key: TaskKey, task_body: Callable, task_type: TaskType, task_args: Args = None):
        self._assert_initialized()
        assert isinstance(task_type, TaskType), f"task_type argument must be one of {', '.join(x.name for x in TaskType)}"
        assert_can_have_subtasks(self.current_task_type)
        if task_args is not None:
            assert isinstance(task_args, Args), "Arguments must be passed as Args instance"
        if len(self.stack) == 1:
            assert isinstance(task_key, str), "Top-level step must be named with a string"
        else:
            assert isinstance(task_key, TaskKey), f"Task key must be one of the following types: {', '.join(map(lambda x: x.__name__, TaskKey.__args__))}"
        parent_frame = self.stack[-1]
        step_path = parent_frame.current_path + [task_key]
        step_order = list(parent_frame.next_subtask_order)
        coordinates = TaskCoordinates(step_path, step_order, task_type)
        self.callbacks.on_task_submitted(coordinates)
        exec_log = self._find_execution_log(coordinates)

        if exec_log is not None:
            log.info(f"Task {coordinates} has already been executed on {exec_log.start} (finished on {exec_log.finish})")
            log.debug(f"Detailed execution log: {exec_log}")
            self.stack[-1].next_subtask_order[-1] += 1
            # self.consistency_manager.skip(coordinates) #fixme
            self.callbacks.on_task_skipped(exec_log)
        else:
            args = task_args or Args()
            log.info(f"Task {coordinates} hasn't been executed yet")
            log.debug(f"Task arguments: {args}")
            try:
                # with self.consistency_manager.invoke(coordinates): #fixme
                    self.stack.append(ExecutionFrame(step_path, step_order + [0], task_type))
                    start = datetime.now()
                    log.debug("Executing task body")
                    self.callbacks.on_task_invoked(start, coordinates)
                    args.invoke(task_body)
                    finish = datetime.now()
                    log.info(f"Task finished executing at {finish}")
                    exec_log = self._mark_finished(coordinates, start, finish)
                    log.debug("Task marked as finished")
                    log.debug(f"Detailed execution log: {exec_log}")

                    self.callbacks.on_task_finished(start, finish, coordinates, Success())
            except Exception as e:
                if self._exception_handler(e, start, coordinates):
                    raise
            except KeyboardInterrupt as e:
                if self._exception_handler(e, start, coordinates):
                    raise
            finally:
                self.stack[-2].next_subtask_order[-1] += 1
                self.stack.pop()


    #todo https://stackoverflow.com/questions/12594148/skipping-execution-of-with-block

    #todo expose ?
    def _find_execution_log(self, coordinates: TaskCoordinates) -> TaskExecutionRecord | None:
        ExecLog = Query()
        found = self.table.search((ExecLog.coordinates.path == coordinates.path) & (ExecLog.coordinates.order == coordinates.order))
        assert len(found) < 2, f"Database inconsistency! More than one ({len(found)}) execution logs found for {coordinates}"
        if found:
            return found[0]
        return None

    def _mark_finished(self, coordinates: TaskCoordinates, start: datetime, finish: datetime):
        record = TaskExecutionRecord(coordinates, self.session.runtime_sid, self.session.context_session_no, start, finish)
        self.table.insert(record)
        return record


def toBeContinued(comment: str=""):
    raise ToBeContinuedException(comment)
