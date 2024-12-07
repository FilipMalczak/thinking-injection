from logging import getLogger
from pprint import pformat

from thinking_modules.model import ModuleName
from thinking_tests import decorators
from thinking_tests.fluent_decorator import fluent_decorator
from thinking_tests.protocol import CaseCoordinates
from thinking_tests.simple import SimpleThinkingCase


#todo move to thinking-tests
def assert_fails(l):
    try:
        l()
        fail = False
    except:
        fail = True
    assert fail

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

@fluent_decorator
def parametrized_case(name=None, *, params=None, setup=None, teardown=None):
    def decorator(f):
        nonlocal name, params, setup, teardown
        params = params or tuple()
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