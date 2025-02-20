from datetime import datetime

from thinking_executor.callbacks.session import CompositeSessionCallback, SessionCallback
from thinking_executor.data.tinydb import TinyDBLifecycle
from thinking_executor.data.tiny_schema import TinyDBTableWithSchema, Query
from thinking_executor.executor_model import TaskCoordinates
from thinking_executor.globals_manager import GlobalsManager, LastSession
from thinking_executor.session_model import RUNTIME_SESSION, ContextSession, RuntimeSession, ContextSessionPointer
from thinking_injection.injectable import Injectable
from thinking_programming.str import StrReprMixin


#fixme even if there are no invoked steps we still mark the session in Tiny - it will accumulate over time, clean it up

class PersistentSessionManager(Injectable, StrReprMixin):
    def __init__(self):
        self._table: TinyDBTableWithSchema = None
        self.globals: GlobalsManager = None
        self.runtime_session: RuntimeSession = RUNTIME_SESSION
        self.previous_runtime_session: RuntimeSession = None
        self.current_context_session: ContextSession = None
        self.current_session_pointer: ContextSessionPointer = None
        self.callbacks: CompositeSessionCallback = CompositeSessionCallback()


    def inject_requirements(self, globals: GlobalsManager, tiny: TinyDBLifecycle, callbacks: list[SessionCallback]) -> None:
        self.globals = globals
        self._table = tiny.get_table_of(RuntimeSession)
        self._persist()
        self.callbacks.add_delegate(*callbacks)

    def initialize(self):
        prev_session = self.globals.find(LastSession)
        if prev_session.sid is not None:
            #todo Im using typed collection, I think I can do without str here and below
            self.previous_runtime_session = self._table.get(Query().sid == str(prev_session.sid))
        self.globals.save(LastSession(RUNTIME_SESSION.sid))
        if prev_session.sid != RUNTIME_SESSION.sid:
            self.callbacks.on_new_runtime_session(RUNTIME_SESSION, self.previous_runtime_session)
        self._open_context_session()

    def deinitialize(self, exc: BaseException | None) -> None:
        self._close_context_session(exc is None)


    def _persist(self):
        self._table.upsert(self.runtime_session, Query().sid == str(self.runtime_session.sid))

    #todo dedicated exceptions
    def _open_context_session(self):
        assert self.current_context_session is None, "Cannot open a new context session while existing one isn't closed yet"
        session_no = len(RUNTIME_SESSION.context_sessions)
        self.current_context_session = ContextSession(session_no, False, datetime.now(), [])
        RUNTIME_SESSION.context_sessions[session_no] = self.current_context_session
        self._persist()
        self.current_session_pointer = ContextSessionPointer(RUNTIME_SESSION.sid, self.current_context_session.session_no)
        self.callbacks.before_context_session(self.current_session_pointer, self.current_context_session)

#todo this is unused; probably leftover from previous repo that entangled database versioning with the executor; fix it and update the `clustering` example DB
    def mark_invoked_step(self, coordinates: TaskCoordinates):
        assert self.current_context_session is not None, "Cannot mark invoked steps outside of context session"
        self.current_context_session.invoked_steps.append(coordinates)
        self._persist()

    def _close_context_session(self, sanitized_close: bool):
        assert self.current_context_session is not None, "Cannot close the context session, because there isn't an open one"
        self.current_context_session.sanitized = sanitized_close
        session = self.current_context_session
        self.current_context_session = None
        pointer = self.current_session_pointer
        self.current_session_pointer = None
        self._persist()
        self.callbacks.after_context_session(pointer, session)

