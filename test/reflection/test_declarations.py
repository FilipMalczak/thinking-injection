from abc import abstractmethod, ABC
from typing import Protocol

from pydot import frozendict
from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_reflection.declarations import analyse_declaration
from thinking_reflection.model.members import FieldDescriptor, UNSUPPORTED


class AProtocol(Protocol):
    x: int
    _y: str

    def foo(self, a): pass

    def _bar(self): pass

    @abstractmethod
    def baz(self): pass

    @abstractmethod
    def _boo(self): pass

    @property
    def a(self): pass

    @property
    def _b(self) -> str: pass

    @_b.setter
    def _b(self, x: bool): pass

    @property
    @abstractmethod
    def c(self) -> str: pass

    @property
    @abstractmethod
    def _d(self) -> int: pass

def test_fixture(t: type, methods: set[str], fields: dict[str, FieldDescriptor]):
    declaration = analyse_declaration(t)
    assert set(declaration.methods.keys()) == methods
    assert declaration.fields == frozendict(fields)

@case
def test_protocol_declaration():
    test_fixture(
        AProtocol,
        {"foo", "_bar", "baz", "_boo"},
        {
            "x": FieldDescriptor(int, int),
            "_y": FieldDescriptor(str, str),
            "a": FieldDescriptor(object, UNSUPPORTED),
            "_b": FieldDescriptor(str, bool),
            "c": FieldDescriptor(str, UNSUPPORTED),
            "_d": FieldDescriptor(int, UNSUPPORTED)
        }
    )

class AnABC(ABC):
    x: int
    _y: str

    def foo(self, a): pass

    def _bar(self): pass

    @abstractmethod
    def baz(self): pass

    @abstractmethod
    def _boo(self): pass

    @property
    def a(self): pass

    @property
    def _b(self) -> str: pass

    @_b.setter
    def _b(self, x: bool): pass

    @property
    @abstractmethod
    def c(self) -> str: pass

    @property
    @abstractmethod
    def _d(self) -> int: pass

@case
def test_abc_declaration():
    test_fixture(
        AnABC,
        {"foo", "baz", "_boo"},
        {
            "x": FieldDescriptor(int, int),
            "_y": FieldDescriptor(str, str),
            "a": FieldDescriptor(object, UNSUPPORTED),
            "c": FieldDescriptor(str, UNSUPPORTED),
            "_d": FieldDescriptor(int, UNSUPPORTED)
        }
    )

class NormalClass:
    x: int
    _y: str

    def foo(self, a): pass

    def _bar(self): pass

    @abstractmethod
    def baz(self): pass

    @abstractmethod
    def _boo(self): pass

    @property
    def a(self): pass

    @property
    def _b(self) -> str: pass

    @_b.setter
    def _b(self, x: bool): pass

    @property
    @abstractmethod
    def c(self) -> str: pass

    @property
    @abstractmethod
    def _d(self) -> int: pass

@case
def test_normal_class_declaration():
    test_fixture(
        NormalClass,
        {"foo", "baz"},
        {
            "x": FieldDescriptor(int, int),
            "a": FieldDescriptor(object, UNSUPPORTED),
            "c": FieldDescriptor(str, UNSUPPORTED)
        }
    )

if __name__=="__main__":
    run_current_module()