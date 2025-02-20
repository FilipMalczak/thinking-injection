from tracemalloc import Trace

from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_programming.callbacks import _callback_methods, callback_method, conventional_callback, CompositeCallback


class Callback1:
    @callback_method
    def foo1(self): ...

    @callback_method
    def foo2(self, x: int): ...

    @callback_method(reverse_order_of_composing=True)
    def foo3(self, a, b): ...

@conventional_callback
class Callback2:
    def on_bar(self): ...

    def before_baz(self): ...

    def after_baz(self): ...

@case
def test_callback_methods_extraction():
    assert set(_callback_methods(Callback1)) == {Callback1.foo1, Callback1.foo2, Callback1.foo3}
    assert set(_callback_methods(Callback2)) == {Callback2.on_bar, Callback2.after_baz, Callback2.before_baz}

@case
def test_composite_delegation():
    class X:
        @callback_method
        def foo(self, a):
            pass

    l1 = []
    l2 = []
    _counter = 0

    class Impl(X):
        def __init__(self, l):
            self.l = l

        def foo(self, a):
            nonlocal _counter
            self.l.append((a, _counter))
            _counter += 1

    CompositeX = CompositeCallback(X)
    cx = CompositeX([Impl(l1), Impl(l2)])

    cx.foo(1)
    cx.foo(2)

    assert l1 == [(1, 0), (2, 2)]
    assert l2 == [(1, 1), (2, 3)]

@case
def test_composite_order():
    class I:
        @callback_method
        def open(self, x): pass

        @callback_method(reverse_order_of_composing=True)
        def close(self, x): pass

    class Impl(I):
        def __init__(self, a, l):
            self.a = a
            self.l = l

        def open(self, x):
            self.l.append(("open", self.a, x))

        def close(self, x):
            self.l.append(("close", self.a, x))

    CompositeI = CompositeCallback(I)

    trace = []
    i1 = Impl(1, trace)
    i2 = Impl(2, trace)
    composite = CompositeI([i1, i2])
    composite.open(5)
    assert trace == [
        ("open", 1, 5),
        ("open", 2, 5)
    ]
    composite.close(6)
    assert trace == [
        ("open", 1, 5),
        ("open", 2, 5),
        ("close", 2, 6),
        ("close", 1, 6)
    ]

@case
def test_composite_caching():
    class X:
        @callback_method
        def foo(self, a):
            pass


    CompositeX = CompositeCallback(X)

    assert CompositeX is CompositeCallback(X)

if __name__ == "__main__":
    run_current_module()