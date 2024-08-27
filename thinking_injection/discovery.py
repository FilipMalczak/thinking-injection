from typing import Callable

DISCOVERED_TYPES = set()

def discover[T: type](t: T) -> T:
    assert isinstance(t, type), "Can only discover concrete types, generics are disallowed" #todo better msg
    DISCOVERED_TYPES.add(t)
    return t


def get_primary_hint[T: type, I: type](t: T) -> I | None:
    try:
        return t.__primary_implementation__
    except AttributeError:
        return None


def set_primary_hint[B: type, I: type](base: B, impl: I):
    assert get_primary_hint(base) is None #todo msg
    base.__primary_implementation__ = impl


def primary_implementation_of[B: type, I: type](base: B) -> Callable[[I], I]:
    def decorator(impl: I) -> I:
        set_primary_hint(base, impl)
        return impl
    return decorator