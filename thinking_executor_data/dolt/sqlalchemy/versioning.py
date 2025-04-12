from logging import getLogger

from sqlalchemy import text
from sqlalchemy.orm import Session

from thinking_executor.executor_model import TaskCoordinates
from thinking_executor_data.common.versioning import BranchNameAdapter, Versioning, UuidBranchNameAdapter
from thinking_executor_data.dolt.sqlalchemy.engine import SqlAlchemyEngineLifecycle
from thinking_injection.injectable import Injectable
from thinking_programming.names import make_uuid
from thinking_reflection.discovery import discover

log = getLogger(__name__)


class DoltBranchNameAdapter(BranchNameAdapter):
    # fixme disallow consecutive dashes in task coordinates, so that we can avoid name clashes

    def to_branch_name(self, coordinates: TaskCoordinates) -> str:
        if coordinates is None:
            return "main"
        # return str(coordinates).replace("@", "--").replace(":", "---")
        return make_uuid()

    def from_branch_name(self, branch_name: str) -> TaskCoordinates:
        if branch_name == "main":
            return None
        #todo branch name may not be parsable; make TaskCoordinates.parse raise something dedicated and reraise it here as Unparsable...
        return TaskCoordinates.parse(branch_name.replace("---", ":").replace("--", "@"))

@discover
class SqlAlchemyDoltVersioning(Versioning, Injectable):
    BRANCH_NAME_ADAPTER = UuidBranchNameAdapter()
    
    def __init__(self):
        self.session: Session = None

    def inject_requirements(self, engine: SqlAlchemyEngineLifecycle) -> None:
        self.session = engine.session

    def _call_procedure(self, proc_name: str, *args: str):
        statement = f"CALL {proc_name}({', '.join(map(lambda x: '\''+str(x)+'\'', args))})"
        log.info("Calling procedure: |'"+statement+"|")
        self.session.execute(text(statement))

    def name_adapter(self) -> BranchNameAdapter:
        return SqlAlchemyDoltVersioning.BRANCH_NAME_ADAPTER

    def current_branch(self) -> str:
        result = self.session.execute(text("SELECT active_branch();")).scalar()
        log.info("Current branch is "+result)
        return result

    def current_coordinates(self) -> TaskCoordinates:
        b = self.current_branch()
        return self.name_adapter().from_branch_name(b)

    def is_dirty(self):
        return bool(self.session.dirty)

    def has_branch(self, coordinates: TaskCoordinates) -> bool:
        name = self.name_adapter().to_branch_name(coordinates)
        log.info("Looking for branch "+name+" (coordinates: "+str(coordinates)+")")
        found = self.session.execute(text(f"SELECT count(*) FROM dolt_branches WHERE name = '{name}'")).scalar() > 0
        log.info("Found branch "+name+": "+str(found))
        return found

    def new_branch(self, coordinates: TaskCoordinates):
        name = self.name_adapter().to_branch_name(coordinates)
        self._call_procedure("DOLT_BRANCH", name, self.current_branch())

    def delete_branch(self, coordinates: TaskCoordinates):
        name = self.name_adapter().to_branch_name(coordinates)
        self._call_procedure("DOLT_BRANCH", "-d", name)

    def checkout(self, coordinates: TaskCoordinates):
        name = self.name_adapter().to_branch_name(coordinates)
        self._call_procedure("DOLT_CHECKOUT", name)
        log.info(f"Post-checkout branch is {self.current_branch()}")

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
