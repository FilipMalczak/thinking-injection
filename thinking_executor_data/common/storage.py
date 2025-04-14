from typing import Protocol, Iterable

from typing import NamedTuple

from thinking_programming.collectable import Collectable



class RepositoryMetadata[E: type, ID, Query](NamedTuple):
    entity_type: E
    id_type: type[ID]
    query_type: type[Query]

class _ById[ID, Result](Protocol):
    def by_id(self, _id: ID) -> Result: ...

class _ByIds[ID, Result](Protocol):
    def by_ids(self, *ids: Collectable[ID]) -> Result: ...

class _Where[Query, Result](Protocol):
    def where(self, query: Query) -> Result: ...

class _All[Result](Protocol):
    def all(self) -> Result: ...

class _Any[Result](Protocol):
    def any(self) -> Result: ...

class Find[ID, Query, E](_ById[ID, E | None], _ByIds[ID, Iterable[E]], _Where[Query, Iterable[E]], _All[Iterable[E]]): ...

class Count[ID, Query](_ByIds[ID, int], _Where[Query, int], _All[int]): ...

class ExistByIds(_All[bool], _Any[bool]): ...

class Exist[ID, Query](_ById[ID, bool], _ByIds[ID, ExistByIds], _Where[Query, bool]): ...

class Delete[ID, Query](_ById[ID, None], _ByIds[ID, None], _Where[Query, None], _All[None]): ...

class Repository[E, ID, Query](Protocol):

    def metadata(self) -> RepositoryMetadata[type[E], ID, Query]: ...

    def save(self, *entities: Collectable[E]) -> list[E]: ...

    #todo update terminus tests to use this
    def save_one(self, entity: E) -> E:
        return self.save(entity)[0]

    #todo ordering, paging
    def find(self) -> Find[ID, Query, E]: ...

    def count(self) -> Count[ID, Query]: ...

    def exist(self) -> Exist[ID, Query]: ...

    def delete(self) -> Delete[ID, Query]:
        """
        When deleting by ID[s] this should raise if there is no such document.
        """
        #todo specify the exception

class Storage(Protocol):
    def supports_entity[E](self, t: type[E]) -> bool: ...

    def repository[E, ID, Q](self, t: type[E]) -> Repository[E, ID, Q]: ...