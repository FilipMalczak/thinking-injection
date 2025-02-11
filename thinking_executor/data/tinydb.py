from logging import getLogger
from os import makedirs
from os.path import exists, dirname, abspath

from tinydb import TinyDB

from thinking_executor.data.tiny_model import TinyConfiguration, TinyDBTable, TinyDBParameters
from thinking_executor.data.tiny_schema import TinyDBWithSchema, TinyDBTableWithSchema
from thinking_injection.injectable import Injectable
from thinking_reflection.discovery import discover

log = getLogger(__name__)

@discover
class TinyDBLifecycle(Injectable):
    def __init__(self):
        self.path: str = None
        self.db: TinyDB = None
        self.db_with_schema: TinyDBWithSchema = None

    def inject_requirements(self, configuration: TinyConfiguration) -> None:
        params = configuration.get_tinydb_parameters()
        self.path = params.path

    def initialize(self) -> None:
        directory = dirname(abspath(self.path))
        log.debug(f"Initializing TinyDB with path {self.path}")
        if not exists(directory):
            log.debug(f"Parent directory {directory} doesn't exist, creating it")
            makedirs(directory)
        self.db = TinyDB(self.path)
        self.db_with_schema = TinyDBWithSchema(self.db)

    def deinitialize(self, exc: BaseException | None) -> None:
        try:
            self.db.close()
        finally:
            self.db = None
            self.db_with_schema = None

    def get_raw_table(self, name: str) -> TinyDBTable:
        return self.db.table(name)

    def get_table_of(self, t: type) -> TinyDBTableWithSchema:
        return self.db_with_schema.table_of(t)

try:
    from thinking_tests.current import current_case, current_case_id

    @discover
    class TinyDBTestConfiguration(TinyConfiguration):
        def get_tinydb_parameters(self) -> TinyDBParameters:
            return TinyDBParameters(f"./test-data/{current_case_id()}.json")
except ModuleNotFoundError:
    pass # declare this class only if in testing environment
