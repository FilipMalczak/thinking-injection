from typing import NamedTuple

from bidict import bidict

DISCOVERED_TYPES = set()

def discover[T: type](t: T) -> T:
    assert isinstance(t, type), "Can only discover concrete types, generics are disallowed" #todo better msg
    DISCOVERED_TYPES.add(t)
    return t


class PrimaryImplementation[B: type, I: type](NamedTuple):
    base: B

    def get(self) -> I:
        return PrimaryImplementation.DATA.get(self.base, None)

    def set(self, impl: I) -> I:
        assert self.get() is None
        assert issubclass(impl, self.base)
        PrimaryImplementation.DATA[self.base] = impl
        return impl

    def __call__(self, impl: I) -> I:
        return self.set(impl)

PrimaryImplementation.DATA = bidict()

class FallbackImplementation[B: type, I: type](NamedTuple):
    base: B

    def get(self) -> I:
        return FallbackImplementation.DATA.get(self.base, None)

    def set(self, impl: I) -> I:
        assert self.get() is None
        assert issubclass(impl, self.base)
        FallbackImplementation.DATA[self.base] = impl
        return impl

    def __call__(self, impl: I) -> I:
        return self.set(impl)

FallbackImplementation.DATA = bidict()