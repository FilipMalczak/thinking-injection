import json
import pickle

import bson
from sqlalchemy import TypeDecorator, Text, LargeBinary
from sqlalchemy.orm import DeclarativeBase

from thinking_programming.serialization import serialize, deserialize


#source: https://stackoverflow.com/a/5192374
#todo extract to programming
class classproperty(object):
    def __init__(self, f):
        self.f = f
    def __get__(self, obj, owner):
        return self.f(owner)

class SqlAlchemyEntity(DeclarativeBase):
    @classproperty
    def __tablename__(cls):
        return cls.__name__

    @classproperty
    def column_names(cls) -> list[str]:
        return [ c.name for c in cls.__table__.columns ]

    def __str__(self):
        fields = ", ".join(f"{n}={getattr(self, n)}" for n in self.column_names)
        return f"{type(self).__name__}({fields})"

    __repr__ = __str__

#todo rethink the name
class DumpsLoads(TypeDecorator):
    #todo should be abstract, should have protocol
    def _backend(self): ...

    def _pack(self, val):
        return val

    def _unpack(self, val):
        return val

    def process_bind_param(self, value, dialect):
        if value is not None:
            packed = self._pack(value)
            return self._backend().dumps(packed)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            packed = self._backend().loads(value)
            unpacked = self._unpack(packed)
            return unpacked
        return None

    @classmethod
    def __class_getitem__(cls, T: type) -> type:
        cls_instance = cls()
        class TypedDumpLoads(TypeDecorator):
            impl = cls.impl

            def process_bind_param(self, value, dialect):
                serialized = serialize(value)
                return cls.process_bind_param(cls_instance, serialized, dialect)

            def process_result_value(self, value, dialect):
                serialized = cls.process_result_value(cls_instance, value, dialect)
                deserialized = deserialize(serialized, T)
                return deserialized

        return TypedDumpLoads

#todo I'm afraid it's gonna get confused with SQLAlchemy JSON...
class JSON(DumpsLoads):
    impl = Text

    def _backend(self):
        return json

#pip install bson==0.5.10

class BSON(DumpsLoads):
    impl = LargeBinary

    def _backend(self):
        return bson

    def _pack(self, val):
        return {"_x": val}

    def _unpack(self, val):
        return val["_x"]

class Pickle(DumpsLoads):
    impl = LargeBinary

    def _backend(self):
        return pickle