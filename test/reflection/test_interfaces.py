from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_reflection.interfaces import interface, is_concrete, ConcreteClass, ConcreteType, is_interface, Interface, \
    InterfaceType


class X: pass


@interface
class I: pass # noqa: E742


@case
def test_concrete_type():
    assert is_concrete(X)
    assert issubclass(X, ConcreteClass)
    assert isinstance(X, ConcreteType)


@case
def test_interface_type():
    assert is_interface(I)
    assert issubclass(I, Interface)
    assert isinstance(I, InterfaceType)

if __name__=="__main__":
    run_current_module()