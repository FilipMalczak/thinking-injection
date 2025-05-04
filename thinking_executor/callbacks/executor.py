from datetime import datetime
from logging import getLogger

from thinking_executor.executor_model import TaskCoordinates, TaskType, TaskExecutionRecord
from thinking_executor.session_model import ContextSessionPointer
from thinking_programming.callbacks import callback_method, CompositeCallback, conventional_callback
from thinking_programming.exceptions import UnreachableInstructionException
from thinking_programming.outcome import Outcome

logger = getLogger(__name__)

@conventional_callback
class StepExecutorCallback:
    def before_session(self, initialized_on: datetime, current_session: ContextSessionPointer): ...

    def on_task_submitted(self, coordinates: TaskCoordinates):
        if coordinates.task_type == TaskType.STEP:
            self.on_step_submitted(coordinates)
        elif coordinates.task_type == TaskType.STAGE:
            self.on_stage_submitted(coordinates)
        else:
            UnreachableInstructionException.guard("Unknown task type: "+str(coordinates.task_type))

    def on_step_submitted(self, coordinates: TaskCoordinates): ...

    def on_stage_submitted(self, coordinates: TaskCoordinates): ...

    def on_task_skipped(self, exec_log: TaskExecutionRecord):
        if exec_log.coordinates.task_type == TaskType.STEP:
            self.on_step_skipped(exec_log)
        elif exec_log.coordinates.task_type == TaskType.STAGE:
            self.on_stage_skipped(exec_log)
        else:
            UnreachableInstructionException.guard("Unknown task type: "+str(exec_log.coordinates.task_type))

    def on_step_skipped(self, exec_log: TaskExecutionRecord): ...

    def on_stage_skipped(self, exec_log: TaskExecutionRecord): ...

    @callback_method # todo on_step_invoking? invocation? its happening BEFORE invoking the body
    def on_task_invoked(self, start: datetime, coordinates: TaskCoordinates):
        if coordinates.task_type == TaskType.STEP:
            self.on_step_invoked(start, coordinates)
        elif coordinates.task_type == TaskType.STAGE:
            self.on_stage_invoked(start, coordinates)
        else:
            UnreachableInstructionException.guard("Unknown task type: "+str(coordinates.task_type))

    def on_step_invoked(self, start: datetime, coordinates: TaskCoordinates): ...

    def on_stage_invoked(self, start: datetime, coordinates: TaskCoordinates): ...

    def on_task_finished(self, start: datetime, finish: datetime, coordinates: TaskCoordinates, outcome: Outcome):
        if coordinates.task_type == TaskType.STEP:
            self.on_step_finished(start, finish, coordinates, outcome)
        elif coordinates.task_type == TaskType.STAGE:
            self.on_stage_finished(start, finish, coordinates, outcome)
        else:
            UnreachableInstructionException.guard("Unknown task type: "+str(coordinates.task_type))

    def on_step_finished(self, start: datetime, finish: datetime, coordinates: TaskCoordinates, outcome: Outcome): ...

    def on_stage_finished(self, start: datetime, finish: datetime, coordinates: TaskCoordinates, outcome: Outcome): ...

    def after_session(self, finished_on: datetime, session: ContextSessionPointer, outcome: Outcome): ...

CompositeStepExecutorCallback = CompositeCallback(StepExecutorCallback)

