from typing import Protocol

from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_injection.context.configurable.configurator import FallbacksProvider, DefaultPrimaryImplementations, \
    ForcedPrimaryImplementations
from thinking_injection.context.configurable.impl import ConfigurableContext
from thinking_injection.context.protocol import InstanceIndex
from thinking_reflection.interfaces import interface, ConcreteType


@interface
class Proto(Protocol):
    def foo(self): pass

class Impl1:
    def foo(self): pass

class Impl2:
    def foo(self): pass

class Impl3:
    def foo(self): pass

@case
def test_empty_context():
    ctx = ConfigurableContext([Proto])
    with ctx.lifecycle() as index:
        pass

def assert_context(idx: InstanceIndex, proto: type, primary_type: type | None, impl_types: set[type]):
    primary = idx.instance(proto)
    impls = idx.instances(proto)
    if primary_type is None:
        assert primary is None
    else:
        assert isinstance(primary, primary_type)
    for impl_t in impl_types:
        assert any(isinstance(x, impl_t) for x in impls)

@case
def test_single_impl():
    ctx = ConfigurableContext([Proto, Impl1])
    with ctx.lifecycle() as index:
        assert_context(index, Proto, Impl1, {Impl1})


@case
def test_multiple_impls():
    ctx = ConfigurableContext([Proto, Impl1, Impl2])
    with ctx.lifecycle() as index:
        assert_context(index, Proto, None, {Impl1, Impl2})

class FallbackForProto(FallbacksProvider):
    def fallbacks(self) -> dict[type, ConcreteType]:
        return {
            Proto: Impl1
        }

@case
def test_fallback_works_when_no_impl():
    ctx = ConfigurableContext([Proto, FallbackForProto])
    with ctx.lifecycle() as index:
        assert_context(index, Proto, Impl1, {Impl1})

@case
def test_fallback_ignored_w_single_impl():
    ctx = ConfigurableContext([Proto, Impl2, FallbackForProto])
    with ctx.lifecycle() as index:
        assert_context(index, Proto, Impl2, {Impl2})

@case
def test_fallback_ignored_w_multiple_impls():
    ctx = ConfigurableContext([Proto, Impl2, Impl3, FallbackForProto])
    with ctx.lifecycle() as index:
        assert_context(index, Proto, None, {Impl2, Impl3})

#todo what if fallback doesn't register as impl?

class DefaultForProto(DefaultPrimaryImplementations):
    def primaries(self) -> dict[type, ConcreteType]:
        return {
            Proto: Impl1
        }

@case
def test_default_ignored_when_primary_present():
    ctx = ConfigurableContext([Proto, Impl2, DefaultForProto])
    with ctx.lifecycle() as index:
        assert_context(index, Proto, Impl2, {Impl2})

@case
def test_default_applied_when_primary_unknown():
    ctx = ConfigurableContext([Proto, Impl1, Impl2, DefaultForProto])
    with ctx.lifecycle() as index:
        assert_context(index, Proto, Impl1, {Impl1, Impl2})

@case
def test_default_cannot_register_new_types():
    ctx = ConfigurableContext([Proto, Impl2, Impl3, DefaultForProto])
    reached = False
    exc = None
    try:
        with ctx.lifecycle() as index:
            reached = True
    except BaseException as e:
        exc = e
    assert not reached
    assert exc is not None

# no point in testing fallback + default - they work in separate situations

class ProtoForcer(ForcedPrimaryImplementations):
    def forced(self) -> dict[type, ConcreteType]:
        return {
            Proto: Impl1
        }


@case
def test_forcing_given_single_impl():
    ctx = ConfigurableContext([Proto, Impl1, ProtoForcer])
    with ctx.lifecycle() as index:
        assert_context(index, Proto, Impl1, {Impl1})

@case
def test_forcing_given_multiple_impls():
    ctx = ConfigurableContext([Proto, Impl1, Impl2, ProtoForcer])
    with ctx.lifecycle() as index:
        assert_context(index, Proto, Impl1, {Impl1, Impl2})

@case
def test_forcing_given_single_impl_and_fallback():
    ctx = ConfigurableContext([Proto, FallbackForProto, ProtoForcer])
    with ctx.lifecycle() as index:
        assert_context(index, Proto, Impl1, {Impl1})


@case
def test_forcing_registers_impl_type_given_no_impls():
    ctx = ConfigurableContext([Proto, ProtoForcer])
    with ctx.lifecycle() as index:
        assert isinstance(index.instance(Proto), Impl1)


@case
def test_forcing_registers_impl_typegiven_single_impl():
    ctx = ConfigurableContext([Proto, Impl2, ProtoForcer])
    with ctx.lifecycle() as index:
        assert isinstance(index.instance(Proto), Impl1)


@case
def test_forcing_registers_impl_type_given_multiple_impl():
    ctx = ConfigurableContext([Proto, Impl2, Impl3, ProtoForcer])
    with ctx.lifecycle() as index:
        assert isinstance(index.instance(Proto), Impl1)


if __name__=="__main__":
    run_current_module()