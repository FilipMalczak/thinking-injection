from logging import getLogger
from time import sleep
from typing import Callable, NamedTuple

from thinking_programming.exceptions import InvalidStateException

log = getLogger(__name__)

#todo predicate and named predicate would go well with NamedLambda from testing; consider turbo-extraction, outside of thinking
Predicate = Callable[[], bool]

class NamedPredicate(NamedTuple):
    name: str
    predicate: Predicate

    def __call__(self) -> bool:
        return self.predicate()

    def __str__(self):
        return f"NamedPredicate({self.name})"

StepbackStrategy = Callable[[int], float]
"""
Function that takes retry number (0-based) and returns wait time before next retry.
"""

class ConstantStepback(NamedTuple):
    stepback: float

    def __call__(self, retry_no: int) -> float:
        return self.stepback

#todo expotential stepback?


class PollingFailureException(InvalidStateException):
    def __init__(self, pred: Predicate, retries: int, stepback_strategy: StepbackStrategy):
        self.predicate = pred
        self.retries = retries
        self.stepback_strategy = stepback_strategy
        InvalidStateException.__init__(self, f"Predicate {pred} still not satisfied after {retries} retries")

def poll(pred: Predicate, retries: int, stepback_strategy: StepbackStrategy):
    """
    It is recommended to use NamedPredicate instead of simple lambda, as it will make logs cleaner.
    :raises PollingFailureException:
    """
    success = False
    for i in range(retries):
        log.debug(f"Polling {pred}; retry {i + 1}/{retries}")
        if not pred():
            sleep_time = stepback_strategy(i)
            log.info(f"{pred} failed; sleeping for {sleep_time}s")
            sleep(sleep_time)
        else:
            success = True
            log.debug(f"{pred} succeeded")
            break
    if not success:
        raise PollingFailureException(pred, retries, stepback_strategy)