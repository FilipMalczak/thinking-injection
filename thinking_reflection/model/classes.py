from typing import NamedTuple, Protocol, runtime_checkable, Self

from frozendict import frozendict

from thinking_reflection.model.members import FieldDescriptor, MethodDescriptor

def unique_concat[T](*ts: tuple[T, ...]) -> tuple[T, ...]:
    def i():
        for t in ts:
            yield from t
    return tuple(set(i()))

def unique_merge[T](d1: frozendict[str, tuple[T]], d2: frozendict[str, tuple[T]]) -> frozendict[str, tuple[T]]:
    out = dict(d1)
    for k, v in d2.items():
        if k not in out:
            out[k] = tuple()
        out[k] = unique_concat(out[k], v)
    return frozendict(out)

class TypeDescriptor(NamedTuple):
    fields: frozendict[str, tuple[FieldDescriptor]]
    methods: frozendict[str, tuple[MethodDescriptor]]

    def add(self, other: Self) -> Self:
        return TypeDescriptor(
            unique_merge(self.fields, other.fields),
            unique_merge(self.methods, other.methods)
        )

    def __add__(self, other) -> Self:
        assert isinstance(other, TypeDescriptor) #todo msg
        return self.add(other)

    @classmethod
    def empty(cls) -> Self:
        return TypeDescriptor(frozendict(), frozendict())