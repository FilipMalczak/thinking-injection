from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from thinking_executor_data.dolt.daemon import DoltConectionConfig, DoltConnectionConfigFactory
from thinking_injection.injectable import Injectable
from thinking_programming.exceptions import NoneValueException


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
        self._engine = create_engine(
            db_connection,
            #todo make these ("echo") configurable
            # echo=True,
            # echo_pool=True,
            #todo these too
            # pool_pre_ping=True,
            connect_args={
                "connect_timeout": 120  # in seconds
            }
        )
        self._session = Session(self._engine)

    def deinitialize(self, exc: BaseException | None) -> None:
        # if we lose connection during this stage of deinitializing, we shouldn't care;
        # we already handled the consistency stuff, so what we try to do with the connection handles is that we try
        # to make them useless in the future; if they are already useless - yay!
        def _ignore_lost_connection(foo, *args):
            try:
                return foo(*args)
            except OperationalError as e:
                handled = False
                try:
                    #todo this is very much pymysql; will need to change that if we enable multiple backends
                    if e.orig.args[0] == 2013: # code for lost connection
                        handled = True
                except:
                    pass
                if not handled:
                    raise
        try:
            _ignore_lost_connection(self._session.close)
        finally:
            try:
                _ignore_lost_connection(self._engine.dispose, True)
            finally:
                self._session = None
                self._engine = None

    @property
    def engine(self) -> Engine:
        return NoneValueException.guard(self._engine)

    @property
    def session(self) -> Session:
        return NoneValueException.guard(self._session)
