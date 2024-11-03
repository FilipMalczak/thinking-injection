from typing import Iterable

__all__ = ["Collectable", "collect"]

#todo untested

type Collectable[T] = T | Iterable[T]

def collect[T](t: type[T], *collectable: Collectable[T]) -> Iterable[T]:
    for c in collectable:
        if isinstance(c, t):
            yield c
        else:
            for x in c:
                assert isinstance(x, t)
                yield x
