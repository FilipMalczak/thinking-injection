from thinking_executor.session_model import RuntimeSession, ContextSessionPointer, ContextSession
from thinking_programming.callbacks import conventional_callback, CompositeCallback


@conventional_callback
class SessionCallback:
    """
    Returned value should indicate whether there has been any changes to sessions (not pointers!) passed as
    the argument (by reference). In other words - should the stuff that's been fed to callback be persisted, or
    was it untouched.
    """

    def on_new_runtime_session(self, new_session: RuntimeSession, previous_session: RuntimeSession | None) -> bool: ...

    def before_context_session(self, pointer: ContextSessionPointer, session: ContextSession) -> bool: ...

    def after_context_session(self, pointer: ContextSessionPointer, session: ContextSession) -> bool: ...

CompositeSessionCallback = CompositeCallback(SessionCallback)