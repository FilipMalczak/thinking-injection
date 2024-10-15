from typing import Iterable


class UnknownTypesException(Exception):
    def __init__(self, msg: str, unknown: Iterable[type]):
        self.message = msg
        self.unknown_types = frozenset(unknown)

    def __repr__(self):
        return f"UnknownTypesException(message='{self.message}', unknown_types={self.unknown_types})"

    def __str__(self):
        return f"{self.message}; unknown types: {set(self.unknown_types)}"

class UnknownTypeException(UnknownTypesException):
    def __init__(self, msg: str, unknown_type: type):
        super(msg, [unknown_type])

    @property
    def unknown_type(self):
        return list(self.unknown_types)[0] #todo use next()?


    def __repr__(self):
        return f"UnknownTypeException(message='{self.message}', unknown_type={self.unknown_type})"

    def __str__(self):
        return f"{self.message}; unknown type: {set(self.unknown_type)}"
