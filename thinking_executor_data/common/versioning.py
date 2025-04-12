from logging import getLogger
from typing import Protocol

from thinking_modules.immutable import Immutable

from thinking_executor.executor_model import TaskCoordinates
from thinking_injection.injectable import Injectable
from thinking_programming.names import make_uuid, resolve_uuid
from thinking_reflection.discovery import discover
from thinking_reflection.interfaces import interface

log = getLogger(__name__)


class UnparsableBranchNameException(ValueError):
    def __init__(self, name: str):
        self.branch_name = name
        ValueError.__init__(f"Branch name '{name}' cannot be parsed to TaskCoordinates")

class BranchNameAdapter(Protocol):
    #todo how to treat root coordinates? introduce TaskType=ROOT or accept/return None here?
    # dolt uses None approach for now; terminus isnt guarded against it yet
    def to_branch_name(self, coordinates: TaskCoordinates | None) -> str: ...

    def from_branch_name(self, branch_name: str) -> TaskCoordinates | None:
        """
        :raises UnparsableBranchNameException:
        """

class UuidBranchNameAdapter(BranchNameAdapter):
    def __init__(self, no_coordinates_branch: str = "main"):
        self.no_coordinates_branch = no_coordinates_branch

    def to_branch_name(self, coordinates: TaskCoordinates | None) -> str:
        if coordinates is None:
            return self.no_coordinates_branch
        return make_uuid(TaskCoordinates.__name__, str(coordinates))

    def from_branch_name(self, branch_name: str) -> TaskCoordinates | None:
        """
        :raises UnparsableBranchNameException:
        """
        if branch_name == self.no_coordinates_branch:
            return None
        uuid = resolve_uuid(branch_name)
        assert uuid.namespace == TaskCoordinates.__name__
        # todo TC.parse raises smth else than this dedicated exception
        return TaskCoordinates.parse(uuid.name)


@interface
class Versioning(Protocol):
    #fixme first 4 methods should be properties, but then Protocol complain about non-method member of runtime_checkable
    def name_adapter(self) -> BranchNameAdapter: ...

    def current_branch(self) -> str: ...

    def current_coordinates(self) -> TaskCoordinates: ...

    def is_dirty(self) -> bool: ...

    def has_branch(self, coordinates: TaskCoordinates) -> bool: ...

    def new_branch(self, coordinates: TaskCoordinates): ...

    #todo what should happen if we're deleting current branch? what if branch is missing?
    def delete_branch(self, coordinates: TaskCoordinates): ...

    def checkout(self, coordinates: TaskCoordinates): ...

    def commit(self, comment: str = None):
        """
        Comment is strictly advisory; it can be freely ignored by the backend.
        """

    def rollback(self): ...

@discover
class VersioningManager(Injectable):
    def __init__(self):
        self.versionings: tuple[Versioning] = None

    def inject_requirements(self, versionings: list[Versioning]) -> None:
        self.versionings = tuple(versionings)
        log.info(f"Found {len(versionings)} versionings:")
        for i, v in enumerate(versionings):
            log.info(f"Versioning #{i+1}: {v}")

    @property
    def is_dirty(self) -> bool:
        return any(v.is_dirty() for v in self.versionings)

    def ensure_empty_branch(self, coordinates: TaskCoordinates):
        for v in self.versionings:
            if v.has_branch(coordinates):
                v.delete_branch(coordinates)
            v.new_branch(coordinates)

    def checkout(self, coordinates: TaskCoordinates):
        for v in self.versionings:
            v.checkout(coordinates)

    def commit(self):
        for v in self.versionings:
            v.commit()

    def rollback(self):
        for v in self.versionings:
            v.rollback()