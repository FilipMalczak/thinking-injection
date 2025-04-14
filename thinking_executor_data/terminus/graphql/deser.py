from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, time, date
from time import strftime, strptime
from typing import Callable

from thinking_executor_data.terminus.base import XSD_TYPES


class Deser[T](ABC):
    @abstractmethod
    def serialize(self, pythonic: T) -> str:
        """
        Turn into value usable in query.
        """

    @abstractmethod
    def deserialize(self, terminus: str) -> T:
        """
        Read the value returned from query.
        """

@dataclass
class LambdaDeser[T](Deser[T]):
    ser: Callable[[T], str]
    deser: Callable[[str], T]

    def serialize(self, pythonic: T) -> str:
        return self.ser(pythonic)

    def deserialize(self, terminus: str) -> T:
        return self.deser(terminus)

def not_implemented[T, R](arg: T) -> R:
    raise NotImplementedError()

def identity[T](arg) -> T:
    return arg

#date format is iso format, so no point in declaring it here, since its exposed as a method
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
TIME_FORMAT = "%H:%M:%SZ"

DESER = {
    str: LambdaDeser(lambda s: '"'+s+'"', identity),
    int: LambdaDeser(str, int),
    float: LambdaDeser(str, float),
    bool: LambdaDeser(lambda b: str(b).lower(), identity),
    date: LambdaDeser(date.isoformat, date.fromisoformat),
    time: LambdaDeser(lambda t: t.strftime(TIME_FORMAT), time.fromisoformat),
    datetime: LambdaDeser(lambda dt: dt.strftime(DATETIME_FORMAT), datetime.fromisoformat),
}

assert set(DESER.keys()) == set(XSD_TYPES.keys())