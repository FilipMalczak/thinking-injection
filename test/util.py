from typing import Callable

#todo move to thinking-tests
def assert_fails(l):
    try:
        l()
        fail = False
    except:
        fail = True
    assert fail