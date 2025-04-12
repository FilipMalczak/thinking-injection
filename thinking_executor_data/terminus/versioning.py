from logging import getLogger

from terminusdb_client import Client

from thinking_executor.executor_model import TaskCoordinates
from thinking_executor_data.terminus.client import TerminusClientLifecycle
from thinking_executor_data.common.versioning import BranchNameAdapter, Versioning, UuidBranchNameAdapter
from thinking_injection.injectable import Injectable
from thinking_programming.names import make_uuid, resolve_uuid
from thinking_reflection.discovery import discover

log = getLogger(__name__)


@discover
class TerminusDbVersioning(Injectable, Versioning):
    BRANCH_NAME_ADAPTER = UuidBranchNameAdapter()

    def __init__(self):
        self._last_commited_branch: str = None
        self._branch: str = None
        self._coordinates: TaskCoordinates = None
        self.terminus: Client = None

    def inject_requirements(self, lifecycle: TerminusClientLifecycle) -> None:
        self.terminus = lifecycle.client
        self._branch = self.terminus.branch
        self._last_commited_branch = self._branch

    def name_adapter(self) -> BranchNameAdapter:
        return TerminusDbVersioning.BRANCH_NAME_ADAPTER

    def current_branch(self) -> str:
        return self._branch

    def current_coordinates(self) -> TaskCoordinates | None:
        if self._branch == "main":
            return None
        return self.name_adapter().from_branch_name(self._branch)

    def is_dirty(self) -> bool:
        return self._branch != self._last_commited_branch

    def has_branch(self, coordinates: TaskCoordinates) -> bool:
        name = self.name_adapter().to_branch_name(coordinates)
        existing_names = [x["name"] for x in self.terminus.get_all_branches()]
        return name in existing_names

    def new_branch(self, coordinates: TaskCoordinates):
        name = self.name_adapter().to_branch_name(coordinates)
        log.info(f"Creating branch {name} (coordinates: {coordinates})")
        self.terminus.create_branch(name)

    def delete_branch(self, coordinates: TaskCoordinates):
        name = self.name_adapter().to_branch_name(coordinates)
        log.info(f"Deleting branch {name} (coordinates: {coordinates})")
        self.terminus.delete_branch(name)

    def checkout(self, coordinates: TaskCoordinates):
        name = self.name_adapter().to_branch_name(coordinates)
        log.info(f"Checking out branch {name} (coordinates: {coordinates})")
        assert self.has_branch(coordinates) #todo msg, microoptimization (pass name instead of coordinates)
        self.terminus.branch = name
        self._branch = name
        self._last_commited_branch = name

    def commit(self, comment: str = None):
        log.info(f"Commiting to branch {self._branch}")
        self._last_commited_branch = self._branch

    def rollback(self):
        log.info(f"Rolling back branch {self._branch}")
        if self.is_dirty():
            log.info(f"Branch {self._branch} was dirty, reverting changes")
            rolled_back = self._branch
            self.terminus.branch = self._last_commited_branch
            self._branch = self._last_commited_branch
            self.terminus.delete_branch(rolled_back)
            self.terminus.create_branch(rolled_back)