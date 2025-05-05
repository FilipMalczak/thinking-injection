from logging import getLogger

from sqlalchemy import text
from sqlalchemy.orm import Session

from thinking_executor.executor_model import TaskCoordinates
from thinking_executor_data.common.versioning import BranchNameAdapter, Versioning, UuidBranchNameAdapter
from thinking_executor_data.dolt.sqlalchemy.engine import SqlAlchemyEngineLifecycle
from thinking_injection.injectable import Injectable
from thinking_reflection.discovery import discover

log = getLogger(__name__)


@discover
class SqlAlchemyDoltVersioning(Versioning, Injectable):
    BRANCH_NAME_ADAPTER = UuidBranchNameAdapter()
    
    def __init__(self):
        self.session: Session = None

    def inject_requirements(self, engine: SqlAlchemyEngineLifecycle) -> None:
        self.session = engine.session

    def _call_procedure(self, proc_name: str, *args: str):
        statement = f"CALL {proc_name}({', '.join(map(lambda x: '\''+str(x)+'\'', args))})"
        log.debug("Calling procedure: |'"+statement+"|")
        self.session.execute(text(statement))

    def name_adapter(self) -> BranchNameAdapter:
        return SqlAlchemyDoltVersioning.BRANCH_NAME_ADAPTER

    def current_branch(self) -> str:
        result = self.session.execute(text("SELECT active_branch();")).scalar()
        return result

    def current_coordinates(self) -> TaskCoordinates:
        b = self.current_branch()
        return self.name_adapter().from_branch_name(b)

    def is_dirty(self):
        return bool(self.session.dirty)

    def has_branch(self, coordinates: TaskCoordinates) -> bool:
        name = self.name_adapter().to_branch_name(coordinates)
        found = self.session.execute(text(f"SELECT count(*) FROM dolt_branches WHERE name = '{name}'")).scalar() > 0
        return found

    def new_branch(self, coordinates: TaskCoordinates):
        name = self.name_adapter().to_branch_name(coordinates)
        self._call_procedure("DOLT_BRANCH", name, self.current_branch())

    def delete_branch(self, coordinates: TaskCoordinates):
        name = self.name_adapter().to_branch_name(coordinates)
        #-D == --delete --force
        #w/o --force it would fail if branch wasn't fully merged, which may happen
        #todo introduce configurable strategy; for example: rename the branch with some suffix instead of deleting;
        # may be useful for auditing and debugging
        self._call_procedure("DOLT_BRANCH", "-D", name)

    def checkout(self, coordinates: TaskCoordinates):
        name = self.name_adapter().to_branch_name(coordinates)
        self._call_procedure("DOLT_CHECKOUT", name)

    def commit(self, comment: str = None):
        # DO NOT DO
        #     self.session.commit()
        # HERE! Standard SQL commits and rollbacks clash with Dolt procedures
        suffix = "" if comment is None else " ["+comment+"]"
        self._call_procedure("DOLT_COMMIT", "-A",  "--allow-empty", "-m", str(self.current_coordinates())+suffix)

    def rollback(self):
        # DO NOT DO
        #     self.session.rollback()
        # HERE! Standard SQL commits and rollbacks clash with Dolt procedures
        self._call_procedure("DOLT_RESET", "--hard")
