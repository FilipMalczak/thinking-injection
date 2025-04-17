import sys
from logging import getLogger
from pprint import pformat
from typing import Callable, Iterable

from thinking_modules.model import ModuleName
from thinking_tests import decorators
from thinking_tests.fluent_decorator import fluent_decorator
from thinking_tests.protocol import CaseCoordinates, ThinkingCase
from thinking_tests.runner.protocol import BackendResultType
from thinking_tests.running.start import default_sorter, run_all
from thinking_tests.simple import SimpleThinkingCase
from thinking_tests.utils import caller_module_name, main_module_real_name



#todo move to thinking-tests
def assert_fails(l, exc_type=None):
    exc = None
    try:
        l()
    except BaseException as e:
        exc = e
    assert exc is not None
    if exc_type is not None:
        try:
            assert isinstance(exc, exc_type)
            return exc
        except:
            log = getLogger("test.assert_fails")
            import traceback
            log.error(f"Exception: {exc}")
            log.error(f"Expected exception type: {exc_type}")
            raise

def assert_equal_dicts(expected, result):
    try:
        assert expected == result
    except:
        log = getLogger("test.assert_equal_dicts")
        expected_keys = set(expected.keys())
        result_keys = set(result.keys())
        not_found = expected_keys - result_keys
        unexpected = result_keys - expected_keys
        for nf in sorted(not_found, key=str):
            log.error(f"Key {nf} expected, but not found")
            log.error(f"\tExpected value: {pformat(expected[nf])}")
        for ue in sorted(unexpected, key=str):
            log.error(f"Unexpected key {ue} found")
            log.error(f"\tFound value: {pformat(result[ue])}")
        smaller_keys = expected_keys if len(expected_keys) < len(result_keys) else result_keys
        for k in sorted(smaller_keys, key=str):
            if k not in not_found and k not in unexpected:
                expected_val = expected[k]
                result_val = result[k]
                if expected_val != result_val:
                    log.error(f"Value mismatch for key {k}")
                    log.error(f"\tExpected value: {pformat(expected_val)}")
                    log.error(f"\tResult value:   {pformat(result_val)}")
        raise

class NamedLambda[C: Callable]:
    def __init__(self, name: str, foo: C):
        self.name = name
        self.foo = foo

    def __call__(self, *args, **kwargs):
        return self.foo(*args, **kwargs)

    def __str__(self):
        return type(self).__name__+"(name: "+self.name+")"

@fluent_decorator
def parametrized_case(name=None, *, params=None, setup=None, teardown=None):
    def decorator(f):
        nonlocal name, params, setup, teardown
        params = params or tuple()
        if not isinstance(params, Iterable):
            params = (params, )
        else:
            params = tuple(params)
        name = (name or f.__name__)+" // parameters: ("+(", ".join(str(x) for x in params))+")"
        setup = setup or decorators.CURRENT_SETUP
        teardown = teardown or decorators.CURRENT_TEARDOWN
        case = SimpleThinkingCase(
            CaseCoordinates(ModuleName.of(f), name, decorators._lineno(f)),
            setup,
            lambda: f(*params),
            teardown
        )
        decorators.KNOWN_CASES.append(case)
        return case
    return decorator

#fixme bundled variant is broken
#also, it fails when there are no tests in suite
def run_current_package(predicate: Callable[[ThinkingCase], bool] = None,
                        *,
                        sorter: Callable[[list[ThinkingCase]], list[ThinkingCase]] = None) -> BackendResultType:
    """
    Scan the package in which calling module lies, as well as its subpackages. If called from pkg.__main__ or pkg.__init__,
    takes pkg as that package. Run all tests found within
    """
    predicate = predicate or (lambda x: True)
    sorter = sorter or default_sorter
    name = caller_module_name(2) # 1 is this module, we're looking for caller of this method
    caller_module = main_module_real_name() if name == "__main__" else ModuleName.resolve(name)
    pkg_name = caller_module.parent
    def final_predicate(x: ThinkingCase) -> bool:
        return pkg_name.is_ancestor(ModuleName.resolve(x.coordinates.module_name)) and predicate(x)
    return run_all(final_predicate, root_package=pkg_name.qualified, sorter=sorter)
