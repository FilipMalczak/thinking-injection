import os
from dataclasses import field, dataclass
from datetime import datetime
from typing import Self
from uuid import UUID, uuid4

from thinking_runtime.defaults.recognise_runtime import Runtime, RuntimeMode, current_runtime

from thinking_executor.data.tiny_schema import tiny_table
from thinking_executor.executor_model import TaskCoordinates
from thinking_programming.serialization import SerializableMixin

SessionId = UUID

@dataclass(frozen=True) #fixme I had multiple approaches to immutability and serialization; once we switch to pydantic sanitize this
class RuntimeRecord(SerializableMixin):
    """
    Serializable equivalent of thinking_runtime.defaults.recognise_runtime.Runtime (sans facet conditions)
    """
    mode: RuntimeMode
    active_facet_names: list[str]
    started_on: datetime

    @classmethod
    def of(cls, runtime: Runtime) -> Self:
        return cls(
            runtime.mode,
            [f.name for f in runtime.facets],
            runtime.started_on
        )

@dataclass
class RuntimeSessionMetadata(SerializableMixin):
    runtime: RuntimeRecord = field(default_factory=lambda: RuntimeRecord.of(current_runtime()))
    hostname: str = field(default_factory=lambda: os.uname().nodename)
    pid: int = field(default_factory=os.getpid)

@dataclass
class ContextSession(SerializableMixin):
    session_no: int
    sanitized: bool
    started_on: datetime
    invoked_steps: list[TaskCoordinates]

@tiny_table("runtime-sessions")
@dataclass
class RuntimeSession(SerializableMixin):
    sid: SessionId
    metadata: RuntimeSessionMetadata
    context_sessions: dict[int, ContextSession]

    def last_context_session(self) -> ContextSession | None:
        if not self.context_sessions:
            return None
        max_idx = max(self.context_sessions.keys())
        last = self.context_sessions[max_idx]
        return last

@dataclass
class ContextSessionPointer(SerializableMixin):
    runtime_sid: SessionId
    context_session_no: int

RUNTIME_SESSION = RuntimeSession(uuid4(), RuntimeSessionMetadata(), {})
