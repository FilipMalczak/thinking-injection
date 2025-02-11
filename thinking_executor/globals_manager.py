from dataclasses import dataclass
from logging import getLogger


from thinking_executor.data.tinydb import TinyDBLifecycle
from thinking_executor.data.tiny_schema import tiny_table, TinyDBTableWithSchema, Query
from thinking_executor.session_model import SessionId


from thinking_injection.injectable import Injectable
from thinking_programming.serialization import PolymorphicSerializableMixin
from thinking_programming.str import StrReprMixin

log = getLogger(__name__)

@tiny_table("globals")
class Global(PolymorphicSerializableMixin): pass

@dataclass
class LastSession(Global):
    sid: SessionId = None

class GlobalsManager(Injectable, StrReprMixin):
    def __init__(self):
        self.table: TinyDBTableWithSchema = None

    def inject_requirements(self, tiny: TinyDBLifecycle):
        self.table = tiny.get_table_of(Global)

    def _query[T](self, key: type[T]) -> Query:
        return Query()[PolymorphicSerializableMixin.TYPE_ID_FIELD] == key.type_id()

    def find[T](self, key: type[T]) -> T:
        value = self.table.get(self._query(key))
        if value is None:
            value = key()
            log.info(f"Global {key} not found, persisting {value} before returning it")
            self.table.insert(value)
        else:
            log.debug(f"Global {key} retrieved: {value}")
        return value

    def save[T](self, val: T) -> T:
        q = self._query(type(val))
        if self.table.contains(q):
            log.debug(f"Updating global {type(val)} to {val}")
            self.table.update(val, q)
        else:
            log.info(f"Global {type(val)} not found, persisting {val} instead of updating it")
            self.table.insert(val)
        return val