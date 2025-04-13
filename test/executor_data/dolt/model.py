import sqlalchemy

from thinking_executor_data.dolt.sqlalchemy.base import SqlAlchemyEntity


class DumbEntity(SqlAlchemyEntity):
    id_ = sqlalchemy.Column(sqlalchemy.INT, primary_key=True, autoincrement=True)
    txt = sqlalchemy.Column(sqlalchemy.String(256))