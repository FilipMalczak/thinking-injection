from collections import namedtuple
from typing import NamedTuple


class Outcome: pass

class Success(Outcome): pass

class Result(Success, namedtuple("ResultData", "result")):
    result: object | None

class Failure(Outcome, namedtuple("FailureData", "reason")):
    reason: BaseException

class Unfinished(Outcome): pass

class ToBeContinued(Unfinished, namedtuple("ToBeContinuedData", "comment")):
    comment: str = ""

class Interrupted(Unfinished): pass

class ToBeContinuedException(Exception):
    def __init__(self, comment: str = ""):
        Exception.__init__(self)
        self.comment = comment

    def __str__(self):
        return f"{type(self).__name__}(comment='{self.comment}')"

    __repr__ = __str__

def outcome_of(result, exception: BaseException = None):
    if exception is not None:
        if isinstance(exception, ToBeContinuedException):
            return ToBeContinued(exception.comment)
        elif isinstance(exception, KeyboardInterrupt):
            return Interrupted()
        else:
            return Failure(exception)
    else:
        return Result(result)
