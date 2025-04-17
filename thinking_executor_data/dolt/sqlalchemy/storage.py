import traceback
from dataclasses import dataclass
from functools import wraps
from logging import getLogger
from typing import Iterable, NamedTuple, Protocol, Callable

from sqlalchemy import ColumnExpressionArgument, Engine
# from pymysql.err import ProgrammingError as MySqlProgrammingError
from pymysql.err import ProgrammingError
from pymysql.constants import ER
# from sqlalchemy.exc import ProgrammingError as SqlAlchemyProgrammingError
from sqlalchemy.orm import Session

from thinking_executor_data.dolt.sqlalchemy.engine import SqlAlchemyEngineLifecycle
from thinking_executor_data.dolt.sqlalchemy.versioning import SqlAlchemyDoltVersioning
from thinking_injection.injectable import Injectable
from thinking_programming.collectable import Collectable, collect

from thinking_executor_data.common.storage import Storage, Repository, RepositoryMetadata, Find, Count, Exist, \
    ExistByIds, Delete
from thinking_executor_data.common.writability import WritabilityManager
from thinking_executor_data.dolt.sqlalchemy.base import SqlAlchemyEntity

#if this is simply `SQLFilter = ColumnExpressionArgument` (w/o `type` keyword)
# then there are failures when declaring generic types referring to SQLFilter
# that seems to be because w/o `type` keyword, this is simply an alias for forward-referencing union
# which then leaves an unresolved _T type in generic parameters set
#
# it's hard to explain properly; just remove the `type` and weep
type SQLFilter = ColumnExpressionArgument


log = getLogger(__name__)


#I'm not sure if that's the best of ideas, but it will work as "auto-create DDL whenever needed"; todo: rethink this
def create_schema_if_needed(repo):
    def decorator(foo):
        @wraps(foo)
        def wrapper(*args, **kwargs):
            try:
                return foo(*args, **kwargs)
            except BaseException as e:
                exc = e
                no_such_table = lambda: isinstance(exc, ProgrammingError) and exc.args[0] == ER.NO_SUCH_TABLE
                has_context = lambda: exc.__context__ is not None
                while not no_such_table() and has_context():
                    exc = exc.__context__
                if no_such_table():
                    try:
                        repo.session.rollback()
                        # SqlAlchemyEntity.metadata.create_all(repo.session)
                        SqlAlchemyEntity.metadata.create_all(repo.session.bind)
                    except:
                        raise
                    try:
                        repo.versioning.commit("DDL")
                    except BaseException as y:
                        to_log = "\n"+ "".join(traceback.format_exception(y))
                        log.error(to_log)
                        raise
                    try:
                        out = foo(*args, **kwargs)
                        return out
                    except:
                        raise
                raise
        return wrapper
    return decorator

#todo extract this; expose it from Repository protocol
class ProgressTracker[T](Protocol):
    def track_progress(self, i: int, value: T): ...

@dataclass
class ApplyPeriodically[T](ProgressTracker[T]):
    period: int
    apply: Callable[[int, T], None]
    phase: int = 0

    def track_progress(self, i: int, value: T):
        if i % self.period == self.phase:
            self.apply(i, value)

def track_with[T](iter: Iterable[T], tracker: ProgressTracker[T]) -> Iterable[T]:
    if tracker is None:
        return iter
    def mapping(i_and_x):
        tracker.track_progress(*i_and_x)
        return i_and_x[1]
    return map(mapping, enumerate(iter))



class DoltRepository[E: SqlAlchemyEntity, ID](Repository[E, ID, SQLFilter]):
    def __init__(self, entity_type: type[E], session: Session, versioning: SqlAlchemyDoltVersioning, writability: WritabilityManager):
        self.entity_type: type[E] = entity_type
        self.session: Session = session
        self.versioning: SqlAlchemyDoltVersioning = versioning
        self.writability: WritabilityManager = writability

    def _id_column(self):
        id_cols = list(self.entity_type.__table__.primary_key.columns)
        assert len(id_cols) == 1  # todo allow for composite IDs
        return id_cols[0]

    def _id(self):
        return getattr(self.entity_type, self._id_column().name)

    def _id_type(self):
        return self._id_column().type.python_type

    def _do_query(self, q: SQLFilter = None):
        out = self.session.query(self.entity_type)
        if q is not None:
               out = out.filter(q)
        return out

    def _id_is(self, _id: ID):
        return self._id() == _id

    def _id_in(self, *ids: Collectable[ID]):
        collected = list(collect(self._id_type(), *ids))
        return self._id().in_(collected)

    def metadata(self) -> RepositoryMetadata[type[E], ID, SQLFilter]:
        return RepositoryMetadata(self.entity_type, self._id_type(), SQLFilter)

    def save(self, *entities: Collectable[E], tracker: ProgressTracker[E] = None) -> list[E]:
        #w/o this local function, we couldn't pass self to the decorator
        @create_schema_if_needed(self)
        def _impl():
            self.writability.require_writing("dolt")
            out = None
            to_save = collect(self.entity_type, *entities)
            with self.session.no_autoflush:
                out = [self.session.merge(i) for i in track_with(to_save, tracker)]
            self.session.flush(out)
            return out
        return _impl()

    #todo ordering, paging
    def find(self) -> Find[ID, SQLFilter, E]:
        class DoltFind(Find[ID, SQLFilter, E]):
            @create_schema_if_needed(self)
            def by_id(find, _id: ID) -> E | None:
                #todo assert no more than one result?
                return self._do_query(self._id_is(_id)).first()

            @create_schema_if_needed(self)
            def by_ids(find, *ids: Collectable[ID]) -> Iterable[E]:
                return self._do_query(self._id_in( *ids)).all()

            @create_schema_if_needed(self)
            def where(find, query: SQLFilter) -> Iterable[E]:
                return self._do_query(query).all()

            @create_schema_if_needed(self)
            def all(find) -> Iterable[E]:
                return self._do_query().all()
        return DoltFind()

    def count(self) -> Count[ID, SQLFilter]:
        class DoltCount(Count[ID, SQLFilter]):
            @create_schema_if_needed(self)
            def by_ids(count, *ids: Collectable[ID]) -> int:
                return count.where(self._id_in(*ids))

            @create_schema_if_needed(self)
            def where(count, query: SQLFilter) -> int:
                return self._do_query(query).count()

            @create_schema_if_needed(self)
            def all(count) -> int:
                return self._do_query().count()
        return DoltCount()

    def exist(self) -> Exist[ID, SQLFilter]:
        def _exists_query(condition):
            q = self._do_query(condition)
            e = q.exists()
            query = self.session.query(e)
            result = self.session.execute(query)
            return result.scalar()
        class DoltExistByIds(ExistByIds):
            def __init__(byids, ids: list[ID]):
                byids.ids = ids

            @create_schema_if_needed(self)
            def all(byids) -> bool:
                return self._do_query(self._id_in(byids.ids)).count() == len(byids.ids)

            @create_schema_if_needed(self)
            def any(byids) -> bool:
                return _exists_query(self._id_in(byids.ids))

        class DoltExist(Exist[ID, SQLFilter]):
            @create_schema_if_needed(self)
            def by_id(exist, _id: ID) -> bool:
                return _exists_query(self._id_is(_id))

            @create_schema_if_needed(self)
            def by_ids(exist, *ids: Collectable[ID]) -> DoltExistByIds:
                return DoltExistByIds(list(collect(self._id_type(), *ids)))

            @create_schema_if_needed(self)
            def where(exist, query: SQLFilter) -> bool:
                return _exists_query(query)
        return DoltExist()

    def delete(self) -> Delete[ID, SQLFilter]:
        class DoltDelete(Delete[ID, SQLFilter]):
            @create_schema_if_needed(self)
            def by_id(exist, _id: ID):
                self._do_query(self._id_is(_id)).delete()

            @create_schema_if_needed(self)
            def by_ids(count, *ids: Collectable[ID]):
                self._do_query(self._id_in(*ids)).delete()

            @create_schema_if_needed(self)
            def where(count, query: SQLFilter):
                self._do_query(query).delete()

            @create_schema_if_needed(self)
            def all(self):
                #todo I expect there to be session.delete_all or smth; check if it can be done better
                self._do_query().delete()
        return DoltDelete()

class DoltStorage(Injectable, Storage):
    def __init__(self):
        self.session: Session = None
        self.versioning: SqlAlchemyDoltVersioning = None
        self.writability: WritabilityManager = None

    def inject_requirements(self, sessions: SqlAlchemyEngineLifecycle, versioning: SqlAlchemyDoltVersioning, writability: WritabilityManager) -> None:
        self.session = sessions.session
        self.versioning = versioning
        self.writability = writability


    def supports_entity[E](self, t: type[E]) -> bool:
        return issubclass(t, SqlAlchemyEntity)

    def repository[E, ID](self, t: type[E]) -> DoltRepository[E, ID]:
        return DoltRepository(t, self.session, self.versioning, self.writability)