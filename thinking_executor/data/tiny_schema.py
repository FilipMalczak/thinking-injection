from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from logging import getLogger
from typing import Callable

import tinydb

from thinking_executor.data.tiny_model import TinyDBTable
from thinking_programming.serialization import Serializable, serialize, deserialize

log = getLogger(__name__)

TableName = str
TableType = type[Serializable]

GLOBAL_SCHEMA: dict[TableName, TableType] = {}
REVERSE_SCHEMA: dict[TableType, list[TableName]] = defaultdict(list)

def register(name: TableName, t: TableType):
    # log.info(f"Registering TinyDB table {name} to hold instances of {t}")
    assert name not in GLOBAL_SCHEMA, f"Table {name} has already been registered!"
    GLOBAL_SCHEMA[name] = t
    REVERSE_SCHEMA[t].append(name)
    log.debug(f"Table {name} registered")


def tiny_table[T](name: TableName) -> Callable[[T], T]:
    def decorator(t: T) -> T:
        register(name, t)
        return t
    return decorator

class Query(tinydb.Query):
    pass

def _wrap(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        return method(self, *tuple(serialize(a) for a in args), **{k: serialize(v) for k, v in kwargs.items()})
    return wrapper

for method in [
    tinydb.Query.__eq__,
    tinydb.Query.__ne__,
    tinydb.Query.__lt__,
    tinydb.Query.__le__,
    tinydb.Query.__gt__,
    tinydb.Query.__ge__,
    tinydb.Query.exists,
    tinydb.Query.matches,
    tinydb.Query.search,
    tinydb.Query.test,
    tinydb.Query.any,
    tinydb.Query.all,
    tinydb.Query.one_of,
    tinydb.Query.fragment
]:
    setattr(Query, method.__name__, _wrap(method))

# todo this should be a proper test case
assert (Query().x == datetime(2024, 4, 4, 12, 15, 18)) == (tinydb.Query().x == serialize(datetime(2024, 4, 4, 12, 15, 18)))

@dataclass
class TinyDBTableWithSchema[T]:
    table: TinyDBTable
    t: type[T]

    #todo replace asserts w/ dedicated exceptions
    def insert(self, t: T):
        assert isinstance(t, self.t), f"Trying to insert {t} into table of {self.t}"
        return self.table.insert(serialize(t))

    def search(self, q: Query):
        return [deserialize(t, self.t) for t in self.table.search(q)]

    def contains(self, q: Query) -> bool:
        return self.table.contains(q)

    def update(self, t: T, q: Query):
        assert isinstance(t, self.t), f"Trying to update table of {self.t} with value {t}"
        self.table.update(serialize(t), q)

    def upsert(self, t: T, q: Query):
        assert isinstance(t, self.t), f"Trying to upsert table of {self.t} with value {t}"
        try:
            self.table.upsert(serialize(t), q)
        except:
            raise

    def get(self, q: Query) -> T:
        return deserialize(self.table.get(q), self.t)

    def truncate(self):
        self.table.truncate()

    def remove(self, q: Query):
        self.table.remove(q)

    def all(self) -> list[T]:
        return [deserialize(t, self.t) for t in self.table.all()]


@dataclass
class TinyDBWithSchema:
    db: tinydb.TinyDB

    def _table_with_schema(self, name: TableName, t: TableType, **kwargs):
        return TinyDBTableWithSchema(self.db.table(name, **kwargs), t)

    def table(self, name: TableName, **kwargs) -> TinyDBTableWithSchema:
        #todo what if name is not registered?
        return self._table_with_schema(name, GLOBAL_SCHEMA[name], **kwargs)

    def table_of(self, t: TableType) -> TinyDBTableWithSchema:
        names = REVERSE_SCHEMA.get(t, [])
        #todo dedicated exception
        assert len(names) == 1, f"There is no single table containing {t}; available tables are: {names}"
        return self._table_with_schema(names[0], t)
