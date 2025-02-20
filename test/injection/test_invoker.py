from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from test.util import assert_fails
from thinking_injection.context.protocol import DependencyValidationFailureException
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


@case
def raises_if_simple_dependency_missing():
    ctx = SimpleContext([])
    with ctx.lifecycle() as idx:
        invoker = idx.instance(Invoker)
        assert_fails(lambda: invoker.invoke(single_arg), DependencyValidationFailureException)
        #todo analyse

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

class Concrete: pass


class SubConcrete(Concrete): pass


def collective(l: list[Concrete]) -> list[Concrete]:
    return l


@case
def only_one_impl_gets_injected_to_collective():
    ctx = SimpleContext([Concrete])
    with ctx.lifecycle() as index:
        invoker = index.instance(Invoker)
        l = invoker.invoke(collective)
        assert len(l) == 1
        assert l[0] is [*index.instances(Concrete)][0]


@case
def two_impl_gets_injected_to_collective():
    ctx = SimpleContext([Concrete, SubConcrete])
    with ctx.lifecycle() as index:
        invoker = index.instance(Invoker)
        l = invoker.invoke(collective)
        assert len(l) == 2
        l_ids = { *map(id, l)}
        concrete_instances = { *map(id, index.instances(Concrete)) }
        sub_instances = { *map(id, index.instances(SubConcrete)) }
        assert l_ids == concrete_instances
        assert len(sub_instances) == 1
        assert all(x in l_ids for x in sub_instances)


#todo test collective (0 implementations)
#todo test multiple args

if __name__ == "__main__":
    run_current_module()
    # raises_if_simple_dependency_missing()
    # single_args_gets_called_if_arg_available()