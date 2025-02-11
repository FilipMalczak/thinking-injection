from thinking_executor.session_model import RuntimeSession, ContextSessionPointer, ContextSession
from thinking_programming.callbacks import conventional_callback, CompositeCallback


@conventional_callback
class SessionCallback:
    def on_new_runtime_session(self, new_session: RuntimeSession, previous_session: RuntimeSession | None): ...

    def before_context_session(self, pointer: ContextSessionPointer, session: ContextSession): ...

    def after_context_session(self, pointer: ContextSessionPointer, session: ContextSession): ...

CompositeSessionCallback = CompositeCallback(SessionCallback)