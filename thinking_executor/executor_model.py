import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import NamedTuple, Union, Any, Callable, Self, Iterable

from thinking_executor.data.tiny_schema import tiny_table
from thinking_programming.serialization import SerializableMixin
from thinking_programming.collectable import Collectable, collect

TaskKey = Union[str, int]

TaskPath = list[TaskKey]
TaskOrder = list[int]

class TaskType(enum.Enum):
    STAGE = enum.auto()
    STEP = enum.auto()

def can_have_subtasks(task_type: TaskType) -> bool:
    return task_type == TaskType.STAGE or task_type is None

def assert_can_have_subtasks(task_type: TaskType):
    assert can_have_subtasks(task_type), f"Subtasks are only allowed in root or {TaskType.STAGE.name} tasks"

_TrackingConstants = enum.Enum("_TrackingConstants", "DEFAULT_NAME")

DEFAULT_NAME = _TrackingConstants.DEFAULT_NAME

#todo test the algebra
class Args(NamedTuple):
    args: tuple[Any, ...] = tuple()
    kwargs: dict[str, Any] = {}

    def invoke(self, f: Callable):
        return f(*self.args, **self.kwargs)

    def without_kwargs(self, *names: Collectable[str]) -> Self:
        collected = collect(str, names)
        return Args(self.args, {k: v for k, v in self.kwargs.items() if k not in collected})

    def add(self, other: Self) -> Self:
        #todo exception, docs
        assert len(set(self.kwargs.keys()).intersection(set(other.kwargs.keys()))) == 0, "When adding two Args, keys of kwargs cannot overlap!"
        new_args = self.args + other.args
        new_kwargs = dict(self.kwargs)
        new_kwargs.update(other.kwargs)
        return Args(new_args, new_kwargs)

    def __add__(self, other: Self) -> Self:
        assert isinstance(other, Args)
        return self.add(other)

    def with_overrides(self, other: Self) -> Self:
        """
        Similiar to add(), but if a keyword arg is present in both self and other, the value is taken from other.
        """
        return self.without_kwargs(other.kwargs.keys()).add(other)

    def __lshift__(self, other: Self) -> Self:
        assert isinstance(other, Args)
        return self.with_overrides(other)

    def __rshift__(self, other: Self) -> Self:
        assert isinstance(other, Args)
        return other.with_overrides(self)

    @staticmethod
    def of(*args, **kwargs):
        return Args(args, kwargs)

class CoordinatePart(NamedTuple):
    key: TaskKey
    order: int

    def as_coordinates(self) -> 'TaskCoordinates':
        return TaskCoordinates([self.key], [self.order], TaskType.STAGE)

@dataclass
class TaskCoordinates(SerializableMixin):
    path: TaskPath
    order: list[int]  # todo alias StepOrder
    task_type: TaskType

    def __len__(self):
        #todo invariant: len(self.path) == len(self.order)
        return len(self.path)

    def ancestor(self, depth: int, of_type: TaskType = TaskType.STAGE) -> Self:
        assert depth >= 0, f"Cannot compute a negative ({depth}) ancestor (invariant: depth >= 0)"
        assert depth < len(self), f"Cannot compute {depth}th ancestor of coordinates of length {len(self)} (invariant: depth < len(self))"
        result_len = len(self) - depth
        return TaskCoordinates(self.path[:result_len], self.order[:result_len], of_type)

    @property
    def parent(self) -> Self:
        return self.ancestor(1)

    @property
    def parts(self) -> Iterable[CoordinatePart]:
        return map(lambda x: CoordinatePart(*x), zip(self.path, self.order))

    def sibling(self, key: TaskKey, offset: int = 1, of_type: TaskType = None) -> Self:
        new_path = list(self.path)
        new_path[-1] = key
        new_order = list(self.order)
        new_order[-1] += offset
        new_type = of_type or self.task_type
        return TaskCoordinates(new_path, new_order, new_type)

    def is_descendant_of(self, ancestor: Self) -> bool:
        #todo logs get circular here; somehow bring this assertion back
        # if not can_have_subtasks(ancestor.task_type):
        #     log.warning(f"Trying to check if {self} is descendant of {ancestor}, while the ancestors type doesn't allow for subtasks!")
        l = len(ancestor)
        path_prefix = self.path[:l]
        order_prefix = self.order[:l]
        return path_prefix == ancestor.path and order_prefix == ancestor.order

    def is_sibling(self, possible_sibling: Self, offset: int = 1) -> bool:
        return self.parent == possible_sibling.parent and self.order[-1] + offset == possible_sibling.order

    def __str__(self):
        return f"{self.task_type.name}:{'/'.join(map(str, self.path))}@{'/'.join(map(str, self.order))}"

    @classmethod
    def parse(cls, s: str) -> Self:
        task_type, colon, rest = s.partition(":")
        task_type = TaskType[task_type]
        path, at, order = rest.partition("@")
        order = list(map(int, order.split("/")))
        path = path.split("/")
        for i in range(len(path)):
            v = path[i]
            try:
                v = int(v)
                path[i] = v
            except ValueError:
                pass
        return TaskCoordinates(path, order, task_type)

    def __add__(self, other: CoordinatePart) -> Self:
        assert isinstance(other, CoordinatePart)
        c = other.as_coordinates()
        return TaskCoordinates(self.path + c.path, self.order + c.order, TaskType.STAGE)

#todo proper test case
assert TaskCoordinates.parse("STEP:x/y/z/0/a@0/0/2/0/10") == TaskCoordinates(
    ["x", "y", "z", 0, "a"],
    [0, 0, 2, 0, 10],
    TaskType.STEP
)

@tiny_table("executor-steps")
@dataclass
class TaskExecutionRecord(SerializableMixin):
    coordinates: TaskCoordinates
    session_id: uuid.UUID  #todo 'thinking_executor.session_model.SessionId', but typing system went bonkers because of circular import (may not be the case in this repo)
    session_no: int
    start: datetime
    finish: datetime
    latest_step: TaskCoordinates = None
