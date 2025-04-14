from logging import getLogger
from time import sleep

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from thinking_executor_data.dolt.daemon import DoltConectionConfig, DoltConnectionConfigFactory
from thinking_executor_data.dolt.sqlalchemy.base import SqlAlchemyEntity
from thinking_injection.injectable import Injectable
from thinking_programming.exceptions import NoneValueException

log = getLogger(__name__)

class SqlAlchemyEngineLifecycle(Injectable):
    def __init__(self):
        self._engine: Engine = None
        self._session: Session = None
        self._connection_config: DoltConectionConfig = None

    def inject_requirements(self, config_factory: DoltConnectionConfigFactory) -> None:
        self._connection_config = config_factory.create_dolt_connection_config()

    def initialize(self) -> None:
        #todo general cleanup of this method

        db_connection = self._connection_config.mysql_connection_str
        log.info(f"Creating engine for workload: {db_connection}")
        self._engine = create_engine(
            db_connection,
            #todo make these ("echo") configurable
            # echo=True,
            # echo_pool=True,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 10  # in seconds
            }
        )
        self._session = Session(self._engine)

    def deinitialize(self, exc: BaseException | None) -> None:
        try:
            self._session.close()
        finally:
            self._engine.dispose(True)

    @property
    def engine(self) -> Engine:
        return NoneValueException.guard(self._engine)

    @property
    def session(self) -> Session:
        return NoneValueException.guard(self._session)
