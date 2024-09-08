from typing import Callable

import deepdiff
from deepdiff import DeepDiff


#todo move to thinking-tests
def assert_fails(l):
    try:
        l()
        fail = False
    except:
        fail = True
    assert fail


def assert_equals(expected, result):
    #fixme do some magic so that this method is ommited in stack trace
    #todo extract to thinking-tests
    assert expected == result, f"""Objects:
\texpected={expected}
and
\tresult=  {result}
were supposed to be equal; instead the diff is:
{'\n'.join('\t| '+x for x in DeepDiff(expected, result).pretty().splitlines())}
"""
