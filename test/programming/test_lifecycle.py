from thinking_tests.decorators import case
from thinking_tests.start import run_current_module

from thinking_injection.lifecycle import CustomInitializable, composite_lifecycle


@case
def test_composite_lifecycle_happy():
    l = []
    i1 = CustomInitializable(lambda: l.append(1), lambda e: l.append((2, e)))
    i2 = CustomInitializable(lambda: l.append(3), lambda e: l.append((4, e)))
    with composite_lifecycle([i1, i2]):
        pass
    assert l == [1, 3, (4, None), (2, None)]


class Exc(Exception): pass

@case
def test_composite_lifecycle_unhappy():
    l = []
    e = Exc()
    i1 = CustomInitializable(lambda: l.append(1), lambda e: l.append((2, e)))
    i2 = CustomInitializable(lambda: l.append(3), lambda e: l.append((4, e)))
    try:
        with composite_lifecycle([i1, i2]):
            raise e
        assert False
    except Exc as e2:
        assert e2 is e
    assert l == [1, 3, (4, e), (2, e)]

if __name__=="__main__":
    run_current_module()