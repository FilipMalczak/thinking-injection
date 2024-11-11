from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_reflection.source_scope import get_source_scope, SourceScope


class A:
    def foo(self): pass

    def bar(self):
        pass

class B(A):
    def bar(self, x): pass

    def baz(self): ...

@case
def test_resolving_type_scope():
    assert get_source_scope(A) == SourceScope(__file__, 7, 5)

@case
def test_resolving_method_scope():
    assert get_source_scope(A.foo) == SourceScope(__file__, 8, 1)

@case
def test_scope_contains():
    assert get_source_scope(A.foo) in get_source_scope(A)
    assert get_source_scope(B.bar) not in get_source_scope(A)
    assert get_source_scope(B.baz) not in get_source_scope(A)

if __name__=="__main__":
    run_current_module()