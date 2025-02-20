from typing import Iterable, Self


class NoneValueException(ValueError):
    def __init__(self, details: str | None = None):
        ValueError.__init__(self, "The argument"+(" ("+details+")" if details else "")+" is None")


    #todo previously this didn't return the value; browse the codebase and simplify it if possible
    #todo make other exceptions return the guarded value (where it makes sense)
    @classmethod
    def guard[T](cls, val: T, details: str | None = None) -> T:
        if val is None:
            raise cls(details)
        return val


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


class Group:
    """
    Fluent API over multiple Exc.guard(...) statements, brought as exception group.

    Use it as:
    try:
        with Group("Message defaulting to None==''") as guard:
            guard(SomeException, something, else)
            guard(AnotherException, foo, bar, baz)
    except ExceptionGroup as g:
        ...

    SomeException and AnotherException must have static/class method guard(...) that accepts (something, else) and
    (foo, bar, baz), respectively.
    """

    #fixme maybe use BaseException(Group)?
    def __init__(self, msg: str=None):
        self.msg = msg
        self.exceptions: list[Exception] = []

    def guard(self, t: type[Exception], *args, **kwargs) -> Self:
        try:
            t.guard(*args, **kwargs)
        except Exception as e:
            self.exceptions.append(e)
        return self

    def __call__(self, *args, **kwargs) -> Self:
        return self.guard(*args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.exceptions:
            raise ExceptionGroup(self.msg or "", self.exceptions)
