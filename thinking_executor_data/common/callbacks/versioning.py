from thinking_executor.executor_model import TaskCoordinates

from thinking_programming.callbacks import conventional_callback, CompositeCallback


#todo single versioning callback? e.g. callback for dolt only?

@conventional_callback
class VersioningManagerCallback:
    def on_ensure_empty_branch(self, coordinates: TaskCoordinates):
        ...

    def on_checkout(self, coordinates: TaskCoordinates):
        ...

    def on_commit(self):
        ...

    def on_rollback(self):
        ...

CompositeVersioningManagerCallback = CompositeCallback(VersioningManagerCallback)