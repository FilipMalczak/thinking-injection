from abc import ABC, abstractmethod
from typing import Protocol, Optional

from frozendict import frozendict
from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_reflection.definitions import TypeDefinition
from thinking_reflection.discovery import discover
from thinking_reflection.interfaces import interface
from thinking_reflection.model.members import FieldDescriptor, MethodDescriptor


class SimpleClass:
    a_simple_c: int

    #notice that the constructor doesn't matter

    def foo_simple(self) -> str:
        return str(self.a_simple_c)

@interface
class InterfaceClass:
    a_inter_c: int

    def foo_inter(self) -> str:
        return str(self.a_inter_c)

@discover
class DiscoveredClass:
    a_disco_c: int

    def foo_disco(self) -> str:
        return str(self.a_disco_c)

class SimpleProtocol(Protocol):
    a_simple_p: bool

    def bar_simple(self) -> str: pass

@interface
class InterfaceProtocol(Protocol):
    a_inter_p: bool

    def bar_inter(self) -> str: pass

@discover
class DiscoveredProtocol(Protocol):
    a_disco_p: bool

    def bar_disco(self) -> str: pass

class SimpleABC(ABC):
    a_simple_a: list

    @abstractmethod
    def baz_simple(self) -> set: pass

@interface
class InterfaceABC(ABC):
    a_interface_a: list

    @abstractmethod
    def baz_simple(self) -> set: pass

@discover
class DiscoveredABC(ABC):
    a_disco_a: list

    @abstractmethod
    def baz_disco(self) -> set: pass

class Clean: pass

@case
def test_degenerate_type_has_empty_definition():
    d = TypeDefinition.of(Clean)
    assert not d.type_descriptor.fields
    assert not d.type_descriptor.methods

class CompositeType(DiscoveredClass, SimpleABC):
    def xyz(self, deadbeef: Optional[str]) -> int: return 0

@case
def test_example_composite_type():
    d = TypeDefinition.of(CompositeType)
    assert d.type_descriptor.fields == frozendict({
        "a_disco_c": (FieldDescriptor(int, int), ),
        "a_simple_a": (FieldDescriptor(list, list), ),
    })
    m = d.type_descriptor.methods
    assert isinstance(m, frozendict)
    assert set(m.keys()) == {"baz_simple", "foo_disco", "xyz"}
    for v in m.values():
        assert isinstance(v, tuple)
        assert len(v) == 1
        assert isinstance(v[0], MethodDescriptor)



if __name__ == "__main__":
    #this file is unfinished; generally speaking, reflection needs betters test

    # run_current_module()
    test_example_composite_type()