from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from types import GenericAlias, NoneType
from typing import Self, Any, Callable, get_type_hints, TypeVar
from uuid import UUID

try:
    from numpy import ndarray, asarray
    NUMPY_FOUND = True
except ModuleNotFoundError:
    NUMPY_FOUND = False

RepresentationValue = str | int | float | bool | NoneType
RepresentationContainer = dict[RepresentationValue, 'Representation'] | list['Representation']
RepresentedField = RepresentationValue | RepresentationContainer
Representation = dict[str, RepresentedField]


NativelySerializableValue = RepresentationValue
EasilySerializableValue = NativelySerializableValue | datetime | UUID

SerializableContainer = dict[EasilySerializableValue, 'Serializable'] | list['Serializable']
EasilySerializable = EasilySerializableValue | SerializableContainer


class CustomSerializable(ABC):
    @abstractmethod
    def serialize(self) -> Representation:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls: type[Self], data: Representation) -> Self:
        pass


Serializable = EasilySerializable | CustomSerializable

def _serialize_dict(d: dict) -> Representation:
    out = {}
    for k, v in d.items():
        assert isinstance(k, EasilySerializableValue)
        out[serialize(k)] = serialize(v)
    return out

SERIALIZERS = {
    datetime: lambda x: x.timestamp(),
    UUID: str,
    Enum: lambda x: x.name,
    CustomSerializable: lambda x: x.serialize(),
    list: lambda l: list(map(serialize, l)),
    dict: _serialize_dict
}


DESERIALIZERS = {
    datetime: lambda c, v: datetime.fromtimestamp(v),
    UUID: lambda c, v: UUID(v),
    Enum: lambda c, v: c[v],
    CustomSerializable: lambda c, v: c.deserialize(v)
}

if NUMPY_FOUND:
    SERIALIZERS[ndarray] = list
    DESERIALIZERS[ndarray] = lambda c, v: asarray(v)
class SerializableMixin(CustomSerializable):
    def serialize(self) -> Representation:
        return self._enhance({
            k: serialize(v)
            for k, v in self._summarize().items()
        })

    def _summarize(self) -> dict[str, Any]:
        return dict(vars(self))

    def _enhance(self, repr: Representation) -> Representation:
        return repr

    @classmethod
    def _simplify(cls, data: Representation) -> Representation:
        return data

    @classmethod
    def _choose_type(cls: type[Self], data: Representation) -> type[Self]:
        return cls

    @classmethod
    def _type_hint(cls, name: str) -> type[Serializable]:
        return get_type_hints(cls)[name]

    @classmethod
    def deserialize(cls: type[Self], data: Representation) -> Self:
        t = cls._choose_type(data)
        simplified = cls._simplify(data)
        serial_data = {
            k: deserialize(v, t._type_hint(k))
            for k, v in simplified.items()
        }
        return t(**serial_data)

class PolymorphicSerializableMixin(SerializableMixin):
    ID_TO_CLS = {}

    TYPE_ID_FIELD = "__type_id__"

    @classmethod
    def type_id(cls):
        return cls.__module__+"."+cls.__name__

    @classmethod
    def __init_subclass__(cls, **kwargs):
        PolymorphicSerializableMixin.ID_TO_CLS[cls.type_id()] = cls

    @classmethod
    def _choose_type(cls: type[Self], data: Representation) -> Callable[[Representation], Self]:
        return PolymorphicSerializableMixin.ID_TO_CLS[data[PolymorphicSerializableMixin.TYPE_ID_FIELD]]

    def _enhance(self, repr: Representation) -> Representation:
        repr[PolymorphicSerializableMixin.TYPE_ID_FIELD] = type(self).type_id()
        return repr

    @classmethod
    def _simplify(cls, data: Representation) -> Representation:
        del data[PolymorphicSerializableMixin.TYPE_ID_FIELD]
        return data

def serialize(o: Serializable) -> Representation:
    if isinstance(o, NativelySerializableValue):
        return o
    for t, s in SERIALIZERS.items():
        if isinstance(o, t):
            return s(o)
    assert False, f"Cannot serialize {o} of type {type(o)}"

T = TypeVar("T")
def deserialize(o: Serializable, t: type[T]) -> T:
    if o is None or (not isinstance(t, GenericAlias) and isinstance(o, t)):
        return o
    if isinstance(o, list):
        if isinstance(t, GenericAlias):
            assert t.__origin__ == list
            assert len(t.__args__) == 1
            return [deserialize(x, t.__args__[0]) for x in o]
        else:
            if t == list:
                return [deserialize(x, NativelySerializableValue) for x in o]
    if isinstance(o, dict):
        if isinstance(t, GenericAlias) and \
            t.__origin__ == dict and \
            len(t.__args__) == 2 and \
            issubclass(t.__args__[0], EasilySerializableValue):
            return {
                deserialize(k, t.__args__[0]): deserialize(v, t.__args__[1]) for k, v in o.items()
            }
        elif t == dict:
            assert isinstance(o, dict)
            return o
    for td, d in DESERIALIZERS.items():
        if issubclass(t.__origin__ if isinstance(t, GenericAlias) else t, td):
            return d(t, o)
    if issubclass(t, NativelySerializableValue):
        return t(o)
    assert False, f"Cannot deserialize {repr(o)} of type {type(o)} as {t}"