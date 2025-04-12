from logging import getLogger
from time import sleep

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from thinking_executor_data.dolt.daemon import DoltConectionConfig, DoltConnectionConfigFactory
from thinking_executor_data.dolt.sqlalchemy.base import Base
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

        # no_db_connection = "/".join(self._connection_config.mysql_connection_str.split("/")[:-1])
        db_connection = self._connection_config.mysql_connection_str
        # log.info(f"Creating engine for healthcheck: {no_db_connection}")
        # self._engine = create_engine(
        #     no_db_connection,
        #     echo=True,
        #     echo_pool=True,
        #     pool_pre_ping=True,
        #     connect_args={
        #         "connect_timeout": 10 # in seconds
        #     }
        # )
        # ready = False
        # for i in range(5): #todo configurable
        #     log.info(f"Performing connection healthcheck #{i+1}")
        #     try:
        #         #fixme this healthcheck is duplicated, dolt server does the same thing from within the container
        #         conn = self._engine.connect()
        #         cursor = conn.execute(text("select schema_name from information_schema.schemata where schema_name = 'dolt';"))
        #         result = cursor.all()
        #         log.info(f"Found database: {result}")
        #         ready = bool(result)
        #     except OperationalError as e:
        #         log.info(f"Caught {e}")
        #         ready = False
        #     if ready:
        #         break
        #     else:
        #         log.info("Sleeping")
        #         sleep(1) #todo
        # assert ready
        # self._engine.dispose()
        log.info(f"Creating engine for workload: {db_connection}")
        self._engine = create_engine(
            db_connection,
            # echo=True,
            # echo_pool=True,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 10  # in seconds
            }
        )
        # try:
        #     Base.metadata.create_all(self._engine)
        # except:
        #     raise
        self._session = Session(self._engine)

    def deinitialize(self, exc: BaseException | None) -> None:
        #todo make the latter happen even if session.close raises
        self._session.close()
        self._engine.dispose(True)

    @property
    def engine(self) -> Engine:
        return NoneValueException.guard(self._engine)

    @property
    def session(self) -> Session:
        return NoneValueException.guard(self._session)
