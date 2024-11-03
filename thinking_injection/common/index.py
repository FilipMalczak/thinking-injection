from typing import Protocol, runtime_checkable, Any


@runtime_checkable
class TypeIndex[Graph: dict[type, Any]](Protocol):
    def register_type[T: type](self, t: T) -> set[type]:
        """Should be idempotent. Should return a set of newly registered types."""

    def graph_snapshot(self) -> Graph:
        """
        Should return a graph (a mapping from type to any immutable descriptor of that types connections)
        at the moment of calling this method. That way the index can be mutable, but you can obtain the immutable
        view at specific moments.

        The mapping itself is usually mutable, but the immutability is more important when it comes to connection
        descriptor. It's usually either a frozenset, tuple or some named tuple with immutable fields.
        """