from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_injection.context.simple import SimpleContext
from thinking_injection.invoker.protocol import Invoker


def no_args() -> int:
    return 5

@case
def no_args_gets_called():
    ctx = SimpleContext([])
    with ctx.lifecycle() as idx:
        invoker = idx.instance(Invoker)
        assert invoker.invoke(no_args) == 5

class Returns6:
    def return6(self) -> int:
        return 6

def single_arg(r: Returns6) -> int:
    return r.return6()

@case
def single_args_gets_called_if_arg_available():
    ctx = SimpleContext([Returns6])
    with ctx.lifecycle() as idx:
        invoker = idx.instance(Invoker)
        assert invoker.invoke(single_arg) == 6

#todo test that it raises if missing

def optional_arg(r: Returns6 | None) -> int:
    if r is not None:
        return r.return6()
    return 7

@case
def optional_args_gets_called_if_arg_available():
    ctx = SimpleContext([Returns6])
    with ctx.lifecycle() as idx:
        invoker = idx.instance(Invoker)
        assert invoker.invoke(optional_arg) == 6

@case
def optional_args_gets_called_if_arg_unavailable():
    ctx = SimpleContext([])
    with ctx.lifecycle() as idx:
        invoker = idx.instance(Invoker)
        assert invoker.invoke(optional_arg) == 7

#todo test collective (0, 1, n implementations)
#todo test multiple args

if __name__ == "__main__":
    run_current_module()
    # single_args_gets_called_if_arg_available()