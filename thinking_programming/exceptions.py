from typing import Iterable


class NoneValueException(ValueError):
    def __init__(self):
        ValueError.__init__(self, "The argument is None")

    @classmethod
    def guard(cls, val):
        if val is None:
            raise cls()


class WrongIterableSizeException(ValueError):
    def __init__(self, i: Iterable, expected_size: int):
        self.subject = i
        self.expected_size = expected_size
        ValueError.__init__(self, f"Iterable {i} size should be {expected_size} but was {len(i)} instead!")

    @classmethod
    def guard(cls, i: Iterable, e: int):
        if len(i) != e:
            raise cls(i, e)


class EmptyIterableException(WrongIterableSizeException):
    def __init__(self, i: Iterable):
        WrongIterableSizeException.__init__(self, i, 0)

    @classmethod
    def guard(cls, i: Iterable):
        if not len(i):
            raise cls(i)


class InvalidStateException(RuntimeError): pass


class UnreachableInstructionException(InvalidStateException):
    def __init__(self, reason: str = None):
        self.reason = reason
        InvalidStateException.__init__(self, "The program reached the point that shouldn't be reachable" +
                                       ("; detailed reasons: " + self.reason if self.reason else ""))

    @classmethod
    def guard(cls, reason: str = None):
        raise cls(reason)
