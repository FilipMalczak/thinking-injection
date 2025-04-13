from datetime import datetime
from warnings import warn

from thinking_executor.callbacks.executor import StepExecutorCallback
from thinking_executor.callbacks.session import SessionCallback
from thinking_executor.executor_model import TaskExecutionRecord, TaskCoordinates
from thinking_executor.session_model import ContextSessionPointer, RuntimeSession
from thinking_executor_data.common.versioning import VersioningManager
from thinking_executor_data.common.writability import WritabilityManager
from thinking_injection.injectable import Injectable
from thinking_programming.outcome import Outcome, Success
from thinking_reflection.discovery import discover


class UnmanagedWritesWarning(UserWarning):
    def __init__(self):
        UserWarning.__init__(self, "It seems that you performed data writes (including deletes or updates) within a read-only task")


@discover
class ConsistentDataVersioningCallback(Injectable, StepExecutorCallback, SessionCallback):
    def __init__(self):
        self.versioning: VersioningManager = None
        self.writability: WritabilityManager = None

    def inject_requirements(self, versioning: VersioningManager, writability: WritabilityManager) -> None:
        self.versioning = versioning
        self.writability = writability

    def on_new_runtime_session(self, new_session: RuntimeSession, previous_session: RuntimeSession | None):
        #the assumption is that all but last context sessions went through deinitialization; this is supposed
        # to check for cases of power outage, forceful system shutdown, straight-on killing the process, etc
        # so only the last context session may be dirty
        if previous_session is not None and not previous_session.last_context_session().sanitized:
            self.versioning.rollback()

    def on_step_skipped(self, exec_log: TaskExecutionRecord):
        self.versioning.checkout(exec_log.coordinates)

    def on_step_invoked(self, start: datetime, coordinates: TaskCoordinates):
        self.versioning.ensure_empty_branch(coordinates)
        self.versioning.checkout(coordinates)
        self.writability.allow_writing()

    def on_step_finished(self, start: datetime, finish: datetime, coordinates: TaskCoordinates, outcome: Outcome):
        if isinstance(outcome, Success):
            self.versioning.commit()
        else:
            self.versioning.rollback()
        self.writability.disallow_writing()

    def on_stage_finished(self, start: datetime, finish: datetime, coordinates: TaskCoordinates, outcome: Outcome):
        try:
            if self.versioning.is_dirty:
                #todo default config for this kind of warnings? definitely make a good point in docs about it
                warn(UnmanagedWritesWarning())
        except UnmanagedWritesWarning:
            self.versioning.rollback()
            raise
