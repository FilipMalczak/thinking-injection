from abc import ABC, abstractmethod
from typing import Mapping


class GuardedDict[K, V](dict[K, V], ABC):
    def __init__(self, data: dict[K, V]):
        dict.__init__(self)
        self.update(data)

    def __setitem__(self, k: K, v: V):
        self.__guard__(k, v)
        dict.__setitem__(self, k, v)

    @abstractmethod
    def __guard__(self, k, v): pass

    def __delitem__(self, key):
        raise NotImplementedError(f"{type(self)} doesn't support item deletion")

    def __init_subclass__(cls, **kwargs):
        assert cls.__delitem__ == GuardedDict.__delitem__ #todo msg shouldn't override