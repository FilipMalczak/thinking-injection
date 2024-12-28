from typing import Protocol, runtime_checkable, Any


@runtime_checkable
class ReadDescriptor[T](Protocol):
    def __get__(self, instance: Any, owner: type = None) -> T: pass


@runtime_checkable
class WriteDescriptor[T](Protocol):
    def __set__(self, instance: Any, value: T) -> None: pass


#todo del descriptor


AnyDescriptor = ReadDescriptor | WriteDescriptor # | DeleteDescriptor
