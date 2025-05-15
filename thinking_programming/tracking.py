"""
Used to decorate iterable with actions per-element. Mostly useful for tracking progress of foreach.
Following code logs every 100th entity and logs when the iterable is exhausted:

for entity in track(
        thousand_entities_to_save,
        sample(
            periodically(100),
            tracker(
                lambda i, e: log.info(f'Entity #{i} / 1000: {e}'),
                lambda i: log.info(f'Finished saving {i} entities')
            )
        )
):
    db.save(entity)
"""

from typing import NamedTuple, Callable, Iterable, Protocol

from thinking_programming.callbacks import conventional_callback, Composite, CompositeCallback


@conventional_callback
class TrackingCallback[T](Protocol):
    def on_element(self, i: int, value: T): ...

    def on_end(self, i: int):
        '''
        i is the smallest non-present index of the iterable. i-1 is the last index for which on_element has been called.
        '''

class LambdaCallback[T](NamedTuple):
    on_element: Callable[[int, T], None]
    on_end: Callable[[int], None]

def tracker[T](on_element: Callable[[int, T], None] = None, on_end: Callable[[int], None] = None):
    on_element = on_element or (lambda i, x: None)
    on_end = on_end or (lambda i: None)
    return LambdaCallback(on_element, on_end)

SamplingStrategy = Callable[[int], bool]
"""
function (index) -> should apply delegate to sample of that index?
"""

class SamplingCallback[T](NamedTuple):
    strategy: SamplingStrategy
    delegate: TrackingCallback[T]

    def on_element(self, i: int, value: T):
        if self.strategy(i):
            self.delegate.on_element(i, value)

    def on_end(self, i: int):
        self.delegate.on_end(i)

def sample[T](strategy: SamplingStrategy, callback: TrackingCallback[T]) -> TrackingCallback[T]:
    return SamplingCallback(strategy, callback)

def periodically(period: int, phase: int=0) -> SamplingStrategy:
    assert period > phase
    assert period > 0 and phase >= 0
    return lambda i: i % period == phase

CompositeTrackingCallback = CompositeCallback(TrackingCallback)

def track[T](iter: Iterable[T], callback: TrackingCallback[T]) -> Iterable[T]:
    def _impl():
        i = -1
        for i, x in enumerate(iter):
            callback.on_element(i, x)
            yield x
        callback.on_end(i+1)
    return _impl()