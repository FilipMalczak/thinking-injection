import sys
from logging import getLogger
from pprint import pformat

import deepdiff.helper


def _eval_top_level_class(txt: str):

    parts = txt.split(".")
    mod = ".".join(parts[:-1])
    name = parts[-1]
    _mod = sys.modules[mod]
    getattr(_mod, name)
deepdiff.helper.LITERAL_EVAL_PRE_PROCESS.append(("<class ", '>', _eval_top_level_class))

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